"""Sunucu etiketi (guild tag) rol otomasyonunun ortak mantığı.

Discord'un "Sunucu Etiketi" özelliğinde kullanıcı bir sunucuyu birincil sunucu
seçip etiketini profilinde taşır. API'de bu bilgi `user.primary_guild` altında
gelir ve etiket değiştiğinde GUILD_MEMBER_UPDATE tetiklenir; discord.py bunu
`on_user_update` olarak yayınlar. Ayrı bir "etiket değişti" olayı yok, bu yüzden
before/after karşılaştırıyoruz.

Komutlar: src/commands/guildrolesetup.py ve src/commands/guildrolegive.py
"""

import discord

from src.bot import store
from src.config import EMBED_COLOR, GUILD_ID, log
from src.helpers import role_problem

SETTING_KEY = "guild_role"


def raw_config() -> dict:
    """Kayıtlı ayarın kopyası (rol seçilmemiş olabilir)."""
    config = store.setting(SETTING_KEY)
    return dict(config) if isinstance(config, dict) else {}


def active_config() -> dict:
    """Kurulu ve rolü duran ayar; yoksa boş sözlük."""
    config = raw_config()
    return config if config.get("role_id") else {}


def wears_guild_tag(user: discord.abc.User) -> bool:
    """Kullanıcı bu sunucunun etiketini taşıyor mu?"""
    primary = getattr(user, "primary_guild", None)
    if primary is None or primary.id != GUILD_ID:
        return False
    # identity_enabled None ise kullanıcı etiket değişikliğinden sonra henüz
    # onay vermemiş demek; birincil sunucu yine biziz, o yüzden takıyor sayıyoruz.
    return primary.identity_enabled is not False


async def apply_guild_role(
    member: discord.Member, config: dict, *, wearing: bool | None = None
) -> str | None:
    """Üyenin guild rolünü etiket durumuna göre günceller.

    "verildi" / "alındı" döner, bir şey değişmediyse None.
    """
    role = member.guild.get_role(int(config["role_id"]))
    if role is None:
        log.warning("Guild rolü bulunamadı (silinmiş olabilir): %s", config["role_id"])
        return None

    problem = role_problem(member.guild.me, role)
    if problem:
        log.warning("Guild rolü uygulanamıyor: %s", problem)
        return None

    if wearing is None:
        wearing = wears_guild_tag(member)
    has_role = role in member.roles

    try:
        if wearing and not has_role and config.get("auto_add", True):
            await member.add_roles(role, reason="Sunucu etiketi takıldı")
            return "verildi"
        if not wearing and has_role and config.get("auto_remove", True):
            await member.remove_roles(role, reason="Sunucu etiketi kaldırıldı")
            return "alındı"
    except discord.Forbidden:
        log.warning("%s rolü yönetilemedi: yetki veya rol hiyerarşisi engelliyor", role.name)
    except discord.HTTPException as exc:
        log.warning("%s rolü güncellenemedi: %s", role.name, exc)
    return None


def config_embed(guild: discord.Guild, config: dict) -> discord.Embed:
    role = guild.get_role(int(config["role_id"])) if config.get("role_id") else None
    embed = discord.Embed(title="Guild Rol Ayarı", color=EMBED_COLOR)
    embed.add_field(name="Rol", value=role.mention if role else "*silinmiş rol*", inline=False)
    embed.add_field(
        name="Durum", value="açık" if config.get("enabled", True) else "kapalı", inline=True
    )
    embed.add_field(
        name="Etiketi takana ver",
        value="evet" if config.get("auto_add", True) else "hayır",
        inline=True,
    )
    embed.add_field(
        name="Etiketi kaldırandan al",
        value="evet" if config.get("auto_remove", True) else "hayır",
        inline=True,
    )
    return embed


# ------------------- olaylar -------------------

# register() ile dolduruluyor; on_user_update bize sadece User verdiği için
# üyeyi bulmak üzere client'a ihtiyacımız var.
_client: discord.Client | None = None


async def on_user_update(before: discord.User, after: discord.User):
    """Etiket takıldığında/çıkarıldığında rolü otomatik ver/al."""
    config = active_config()
    if not config or not config.get("enabled", True):
        return

    wearing = wears_guild_tag(after)
    if wears_guild_tag(before) == wearing:
        return  # değişen başka bir şey (isim, avatar...)

    guild = _client.get_guild(GUILD_ID) if _client else None
    member = guild.get_member(after.id) if guild else None
    if member is None or member.bot:
        return

    result = await apply_guild_role(member, config, wearing=wearing)
    if result:
        log.info("Guild etiketi: %s (%s) -> rol %s", member, member.id, result)


async def on_member_join(member: discord.Member):
    """Sunucuya etiketi zaten takılı gelen üyeye rolü ver."""
    if member.bot or member.guild.id != GUILD_ID:
        return

    config = active_config()
    if not config or not config.get("enabled", True):
        return

    await apply_guild_role(member, config)


def register(bot) -> None:
    """Olay dinleyicilerini bağlar (guildrolesetup.py içinden çağrılıyor)."""
    global _client
    _client = bot
    bot.add_listener(on_user_update)
    bot.add_listener(on_member_join)
