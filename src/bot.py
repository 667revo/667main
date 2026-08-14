"""Bot sınıfı, yetki kontrolü ve paylaşılan depolama örneği."""

from collections import defaultdict

import discord
from discord import app_commands

import storage
from src.config import (
    ADMIN_ROLE_ID,
    ADMIN_ROLE_NAME,
    CONFIG_CHANNEL_ID,
    DATA_PATH,
    GUILD_ID,
    log,
)

# Tepki-rol eşleşmeleri ve ayarlar için tek ortak depo.
# Komut dosyaları `from src.bot import store` ile buna ulaşır.
store = storage.ReactionRoleStore(
    int(CONFIG_CHANNEL_ID) if CONFIG_CHANNEL_ID else None, DATA_PATH
)

# message_content'e ihtiyacımız yok (prefix komut kullanmıyoruz), members ise
# tepki kaldırıldığında üyeyi bulabilmek için gerekli.
intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
intents.reactions = True


def has_access(user: discord.abc.User) -> bool:
    """Komutları yalnızca yetkili rol çalıştırabilir.

    Sunucu yöneticiliği bilerek muafiyet sayılmıyor: yetki tek bir role bağlı.
    Rol silinir veya ADMIN_ROLE_ID yanlış girilirse hiç kimse komut
    çalıştıramaz, bu durumda ortam değişkenini düzeltip botu yeniden başlat.
    """
    if not isinstance(user, discord.Member):
        return False
    if ADMIN_ROLE_ID:
        return any(role.id == int(ADMIN_ROLE_ID) for role in user.roles)
    return any(role.name == ADMIN_ROLE_NAME for role in user.roles)


class RestrictedTree(app_commands.CommandTree):
    """Tüm slash komutlar için tek yetki kontrol noktası.

    Kontrolü komut komut yazmak yerine burada topluyoruz; böylece yeni bir
    komut dosyası eklendiğinde kontrolü koymayı unutmak mümkün olmuyor.
    """

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.guild_id != GUILD_ID:
            await interaction.response.send_message(
                "Bu bot yalnızca kendi sunucusunda çalışır.", ephemeral=True
            )
            return False

        if not has_access(interaction.user):
            log.warning(
                "Yetkisiz komut denemesi: %s (%s) -> /%s",
                interaction.user,
                interaction.user.id,
                interaction.command.name if interaction.command else "?",
            )
            await interaction.response.send_message(
                "Bu botu kullanma yetkin yok.", ephemeral=True
            )
            return False

        return True


class MyBot(discord.Client):
    """Sadece slash komut kullandığımız için commands.Bot yerine düz Client.

    commands.Bot prefix komutları için message_content intent'i bekliyor ve
    her açılışta gereksiz bir uyarı basıyordu.

    Ek olarak `add_listener` desteği var: düz Client'ta bir olayın tek bir
    dinleyicisi olabilir (@bot.event ikincisini yazınca birincisini eziyor).
    Her komut kendi dosyasında olduğu için iki dosyanın aynı olayı dinlemesi
    çok olası; bu yüzden commands.Bot'un yaptığı gibi dispatch'i genişletiyoruz.
    """

    def __init__(self):
        super().__init__(intents=intents)
        self.tree = RestrictedTree(self)
        self.extra_events: dict[str, list] = defaultdict(list)

    def add_listener(self, coro, name: str | None = None) -> None:
        """Bir olaya dinleyici ekler. name verilmezse fonksiyon adı kullanılır.

        Örnek: `bot.add_listener(on_member_join)` veya
        `bot.add_listener(benim_fonksiyonum, "on_member_join")`
        """
        self.extra_events[name or coro.__name__].append(coro)

    def dispatch(self, event_name: str, /, *args, **kwargs) -> None:
        super().dispatch(event_name, *args, **kwargs)
        for coro in self.extra_events.get("on_" + event_name, ()):
            self._schedule_event(coro, "on_" + event_name, *args, **kwargs)

    async def setup_hook(self):
        await store.load(self)
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
