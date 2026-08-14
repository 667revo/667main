"""Tepki-rol eşleşmeleri için kalıcı depolama.

Heroku'nun dosya sistemi geçici (her yeniden başlatmada sıfırlanıyor), bu yüzden
durumu Discord'un kendisinde saklıyoruz: bot, CONFIG_CHANNEL_ID ile verilen
kanalda tek bir "durum mesajı" tutar ve eşleşmeler değiştikçe onu günceller.
Ek bir veritabanı gerekmiyor.

CONFIG_CHANNEL_ID verilmezse yerel JSON dosyasına düşer (VM veya yerel kullanım).
"""

import json
import logging
import os
import tempfile

import discord

log = logging.getLogger("667bot.storage")

MARKER = "667bot-state"


def emoji_key(emoji: "discord.PartialEmoji | discord.Emoji | str") -> str:
    """Emoji için tutarlı anahtar.

    Özel emojilerde isim değişebildiği için ID'yi, standart emojilerde
    karakterin kendisini kullanırız.
    """
    if isinstance(emoji, str):
        emoji = discord.PartialEmoji.from_str(emoji)
    return str(emoji.id) if emoji.id else emoji.name


class ReactionRoleStore:
    def __init__(self, channel_id: int | None, path: str):
        self.channel_id = channel_id
        self.path = path
        self._data: dict[str, dict[str, int]] = {}
        # Tepki-rol dışındaki kalıcı ayarlar (ör. guild etiketi rolü).
        self._settings: dict[str, object] = {}
        self._message: discord.Message | None = None

    # ------------------- yükleme -------------------

    async def load(self, bot: discord.Client) -> None:
        if not self.channel_id:
            self._data, self._settings = self._read_file()
            log.warning(
                "CONFIG_CHANNEL_ID tanımlı değil, yerel dosya kullanılıyor (%s). "
                "Heroku'da bu dosya her yeniden başlatmada silinir.",
                self.path,
            )
            return

        channel = bot.get_channel(self.channel_id) or await bot.fetch_channel(self.channel_id)

        async for message in channel.history(limit=50):
            if message.author.id == bot.user.id and message.content.startswith(MARKER):
                self._message = message
                self._data, self._settings = self._parse(message.content)
                log.info("Durum mesajı bulundu, %d mesaj için eşleşme yüklendi", len(self._data))
                return

        self._message = await channel.send(self._render())
        log.info("Durum mesajı oluşturuldu: %s", self._message.id)

    # ------------------- okuma / yazma -------------------

    def get(self, message_id: int, key: str) -> int | None:
        return self._data.get(str(message_id), {}).get(key)

    def mapping_for(self, message_id: int) -> dict[str, int]:
        return dict(self._data.get(str(message_id), {}))

    async def set(self, message_id: int, key: str, role_id: int) -> None:
        self._data.setdefault(str(message_id), {})[key] = role_id
        await self._persist()

    async def remove(self, message_id: int, key: str) -> bool:
        entry = self._data.get(str(message_id))
        if not entry or key not in entry:
            return False

        del entry[key]
        if not entry:
            del self._data[str(message_id)]
        await self._persist()
        return True

    # ------------------- ayarlar -------------------

    def setting(self, key: str, default=None):
        return self._settings.get(key, default)

    async def set_setting(self, key: str, value) -> None:
        """Ayarı kaydeder. value None ise ayar tamamen silinir."""
        if value is None:
            self._settings.pop(key, None)
        else:
            self._settings[key] = value
        await self._persist()

    # ------------------- iç işler -------------------

    def _payload(self) -> dict:
        return {"reactions": self._data, "settings": self._settings}

    def _render(self) -> str:
        return f"{MARKER}\n```json\n{json.dumps(self._payload(), ensure_ascii=False)}\n```"

    @staticmethod
    def _split(data: dict) -> tuple[dict[str, dict[str, int]], dict[str, object]]:
        """Yeni ve eski kayıt biçimini tek biçime indirger.

        Eski kayıtlar doğrudan {mesaj_id: {emoji: rol_id}} şeklindeydi; ayarlar
        eklenince {"reactions": ..., "settings": ...} biçimine geçtik. Eski
        durum mesajları da okunabilsin diye ikisini de destekliyoruz.
        """
        if isinstance(data.get("reactions"), dict):
            settings = data.get("settings")
            return data["reactions"], settings if isinstance(settings, dict) else {}
        return data, {}

    @classmethod
    def _parse(cls, content: str) -> tuple[dict[str, dict[str, int]], dict[str, object]]:
        _, _, rest = content.partition("```json\n")
        payload, _, _ = rest.partition("\n```")
        try:
            return cls._split(json.loads(payload) if payload else {})
        except json.JSONDecodeError:
            log.error("Durum mesajı okunamadı, boş başlanıyor")
            return {}, {}

    async def _persist(self) -> None:
        if self._message is None:
            self._write_file()
            return

        content = self._render()
        if len(content) > 2000:
            raise ValueError(
                "Durum mesajı 2000 karakteri aştı. Eski rol mesajlarının "
                "eşleşmelerini /roltepkisil ile temizle."
            )
        await self._message.edit(content=content)

    def _read_file(self) -> tuple[dict[str, dict[str, int]], dict[str, object]]:
        if not os.path.exists(self.path):
            return {}, {}
        try:
            with open(self.path, encoding="utf-8") as f:
                return self._split(json.load(f))
        except (json.JSONDecodeError, OSError):
            return {}, {}

    def _write_file(self) -> None:
        directory = os.path.dirname(os.path.abspath(self.path))
        os.makedirs(directory, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self._payload(), f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.path)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise
