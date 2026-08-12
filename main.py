import logging
import os

import discord
from discord import app_commands
from dotenv import load_dotenv

import storage

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("667bot")


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"{name} tanımlı değil. .env dosyasını kontrol et.")
    return value


TOKEN = _require("DISCORD_TOKEN")
GUILD_ID = int(_require("GUILD_ID"))
ADMIN_ROLE_ID = os.getenv("ADMIN_ROLE_ID")
ADMIN_ROLE_NAME = os.getenv("ADMIN_ROLE_NAME", "admin rolü")
CONFIG_CHANNEL_ID = os.getenv("CONFIG_CHANNEL_ID")
DATA_PATH = os.getenv("DATA_PATH", "data/roles.json")

# Tüm embed'lerin kenar rengi (koyu mor)
EMBED_COLOR = 0x5B2C6F

store = storage.ReactionRoleStore(
    int(CONFIG_CHANNEL_ID) if CONFIG_CHANNEL_ID else None, DATA_PATH
)

# message_content'e ihtiyacımız yok (prefix komut kullanmıyoruz), members ise
# tepki kaldırıldığında üyeyi bulabilmek için gerekli.
intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
intents.reactions = True


class MyBot(discord.Client):
    """Sadece slash komut kullandığımız için commands.Bot yerine düz Client.

    commands.Bot prefix komutları için message_content intent'i bekliyor ve
    her açılışta gereksiz bir uyarı basıyordu.
    """

    def __init__(self):
        super().__init__(intents=intents)
        self.tree = RestrictedTree(self)

    async def setup_hook(self):
        await store.load(self)
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)


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
    komut eklendiğinde kontrolü koymayı unutmak mümkün olmuyor.
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


bot = MyBot()


# Rol dağıtımıyla yetki yükseltilmesini engellemek için: bu yetkilerden birine
# sahip bir rol butonla/tepkiyle dağıtılamaz.
DANGEROUS_PERMISSIONS = (
    "administrator",
    "manage_guild",
    "manage_roles",
    "manage_channels",
    "manage_webhooks",
    "manage_messages",
    "ban_members",
    "kick_members",
    "moderate_members",
    "mention_everyone",
)


def role_problem(me: discord.Member, role: discord.Role) -> str | None:
    """Rol dağıtıma uygun mu? Uygunsa None, değilse sebebi döner."""
    if not me.guild_permissions.manage_roles:
        return "Rol dağıtabilmem için `Rolleri Yönet` yetkisine ihtiyacım var."
    if role.is_default():
        return "@everyone rolü dağıtılamaz."
    if role.managed:
        return f"**{role.name}** bir entegrasyon rolü, Discord elle verilmesine izin vermiyor."
    if role >= me.top_role:
        return (
            f"**{role.name}** benim rolümden yüksek, veremem. "
            "Sunucu ayarlarından benim rolümü bu rolün üstüne taşı."
        )

    granted = [p for p in DANGEROUS_PERMISSIONS if getattr(role.permissions, p)]
    if granted:
        return (
            f"**{role.name}** yetkili bir rol ({', '.join(granted)}). "
            "Herkesin tıklayabildiği bir panelden dağıtılırsa yetki yükseltmeye "
            "açık hale gelir, bu yüzden engellendi."
        )
    return None


@bot.event
async def on_ready():
    log.info("Giriş yapıldı: %s", bot.user)
    activity = discord.Game(name="revorevorevorevo")
    await bot.change_presence(status=discord.Status.online, activity=activity)


@bot.event
async def on_guild_join(guild: discord.Guild):
    """Bot başka bir sunucuya eklenirse orada çalışmasın."""
    if guild.id != GUILD_ID:
        log.warning("İzinsiz sunucuya eklendi, çıkılıyor: %s (%s)", guild.name, guild.id)
        await guild.leave()


# ------------------- /join -------------------
@app_commands.command(name="join", description="Botu ses kanalına sok")
@app_commands.describe(channel="Katılmak istediğiniz ses kanalı (opsiyonel)")
async def join(interaction: discord.Interaction, channel: discord.VoiceChannel = None):
    if channel is None:
        if interaction.user.voice is None:
            await interaction.response.send_message("ses kanalinda degilsin", ephemeral=True)
            return
        channel = interaction.user.voice.channel

    # Ses bağlantısı 3 saniyelik interaction penceresini aşabiliyor.
    await interaction.response.defer()

    voice_client = interaction.guild.voice_client
    if voice_client:
        await voice_client.move_to(channel)
    else:
        await channel.connect()

    await interaction.followup.send(f"**{channel.name}** joined")


# ------------------- /leave -------------------
@app_commands.command(name="leave", description="Botu ses kanalından çıkar")
async def leave(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client is None:
        await interaction.response.send_message("ses kanalinda degilim.", ephemeral=True)
        return

    await interaction.response.defer()
    await voice_client.disconnect()
    await interaction.followup.send("leave")


# ------------------- /mesajyaz -------------------
@app_commands.command(name="mesajyaz", description="Bot mesaj gönderir")
@app_commands.describe(mesaj="Botun göndereceği mesaj")
async def mesajyaz(interaction: discord.Interaction, mesaj: str):
    # Botun @everyone ping'i için kullanılmasını engelle.
    await interaction.response.send_message(
        mesaj, allowed_mentions=discord.AllowedMentions.none()
    )


# ------------------- /nuke -------------------
@app_commands.command(name="nuke", description="Yazılı kanalı temizle")
@app_commands.describe(channel="Temizlenecek yazılı kanal")
async def nuke(interaction: discord.Interaction, channel: discord.TextChannel):
    category = channel.category
    position = channel.position
    overwrites = channel.overwrites

    await interaction.response.send_message(f"nukelaniyor {channel.name}", ephemeral=True)

    await channel.delete()

    new_channel = await interaction.guild.create_text_channel(
        name=channel.name,
        category=category,
        overwrites=overwrites,
        position=position,
    )

    await new_channel.send(f"nuked by {interaction.user.mention}")


# ------------------- /ban -------------------
@app_commands.command(name="ban", description="Kullanıcıyı banla")
@app_commands.describe(user="Banlanacak kullanıcı", reason="Ban sebebi (opsiyonel)")
async def ban(interaction: discord.Interaction, user: discord.User, reason: str = None):
    await interaction.response.defer()

    try:
        await interaction.guild.ban(user, reason=reason)
    except discord.Forbidden:
        await interaction.followup.send(
            "Bu kullanıcıyı banlamak için yetkim yok.", ephemeral=True
        )
        return

    await interaction.followup.send(
        f"{user.mention} başarıyla banlandı. Sebep: {reason or 'Belirtilmedi'}",
        allowed_mentions=discord.AllowedMentions.none(),
    )


# ------------------- /rolpanel -------------------
class RolePanel(discord.ui.View):
    """Kalıcı buton paneli.

    Butonlara callback bağlamıyoruz; tıklamalar custom_id üzerinden
    on_interaction içinde işleniyor. Böylece bot yeniden başladığında
    eski paneller çalışmaya devam ediyor.
    """

    def __init__(self, roles: list[discord.Role]):
        super().__init__(timeout=None)
        for role in roles:
            self.add_item(
                discord.ui.Button(
                    # Discord buton etiketini 80 karakterle sınırlıyor
                    label=role.name[:80],
                    custom_id=f"rr:{role.id}",
                    style=discord.ButtonStyle.secondary,
                )
            )


@app_commands.command(name="rolpanel", description="Butonla rol alma mesajı oluştur")
@app_commands.describe(
    baslik="Panelin başlığı",
    aciklama="Panelin açıklaması",
    rol1="Dağıtılacak rol",
    rol2="Dağıtılacak rol (opsiyonel)",
    rol3="Dağıtılacak rol (opsiyonel)",
    rol4="Dağıtılacak rol (opsiyonel)",
    rol5="Dağıtılacak rol (opsiyonel)",
)
async def rolpanel(
    interaction: discord.Interaction,
    baslik: str,
    aciklama: str,
    rol1: discord.Role,
    rol2: discord.Role = None,
    rol3: discord.Role = None,
    rol4: discord.Role = None,
    rol5: discord.Role = None,
):
    roles = [r for r in (rol1, rol2, rol3, rol4, rol5) if r is not None]

    me = interaction.guild.me
    for role in roles:
        problem = role_problem(me, role)
        if problem:
            await interaction.response.send_message(problem, ephemeral=True)
            return

    # Paneli göndermek bir HTTP çağrısı; önce defer etmezsek 3 saniyelik
    # interaction penceresi dolup 10062 (Unknown interaction) alıyoruz.
    await interaction.response.defer(ephemeral=True)

    embed = discord.Embed(title=baslik, description=aciklama, color=EMBED_COLOR)
    await interaction.channel.send(embed=embed, view=RolePanel(roles))
    await interaction.followup.send("Panel oluşturuldu.", ephemeral=True)


@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type is not discord.InteractionType.component:
        return

    custom_id = (interaction.data or {}).get("custom_id", "")
    if not custom_id.startswith("rr:"):
        return

    # Butonlar sunucu üyelerine açık (rol panelinin amacı bu), ama yalnızca
    # kendi sunucumuzda ve yalnızca güvenli roller için.
    if interaction.guild_id != GUILD_ID or not isinstance(interaction.user, discord.Member):
        return

    role = interaction.guild.get_role(int(custom_id[3:]))
    if role is None:
        await interaction.response.send_message("Bu rol artık mevcut değil.", ephemeral=True)
        return

    problem = role_problem(interaction.guild.me, role)
    if problem:
        log.warning("Panelden dağıtılamayan rol: %s (%s)", role.name, problem)
        await interaction.response.send_message(
            "Bu rol artık dağıtıma uygun değil, bir yetkiliye bildir.", ephemeral=True
        )
        return

    # Rol ekleme/çıkarma bir HTTP çağrısı; buton tıklamalarında da 3 saniyelik
    # pencere geçerli olduğu için önce defer ediyoruz.
    await interaction.response.defer(ephemeral=True)

    try:
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role, reason="Rol paneli")
            await interaction.followup.send(f"**{role.name}** rolü alındı.", ephemeral=True)
        else:
            await interaction.user.add_roles(role, reason="Rol paneli")
            await interaction.followup.send(f"**{role.name}** rolü verildi.", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send(
            "Bu rolü yönetme yetkim yok. Rolüm bu rolün üstünde olmalı.", ephemeral=True
        )


# ------------------- /roltepki -------------------
def render_emoji(key: str) -> str:
    """Depolama anahtarını görüntülenebilir emojiye çevirir."""
    if key.isdigit():
        emoji = bot.get_emoji(int(key))
        return str(emoji) if emoji else f"<:emoji:{key}>"
    return key


def describe_mapping(guild: discord.Guild, mapping: dict[str, int]) -> str:
    lines = [
        f"{render_emoji(key)} → {role.mention if (role := guild.get_role(rid)) else '*silinmiş rol*'}"
        for key, rid in mapping.items()
    ]
    return "\n".join(lines) or "—"


@app_commands.command(name="roltepki", description="Bir mesaja emoji tepkisiyle rol ekle")
@app_commands.describe(
    emoji="Tıklanacak emoji",
    rol="Verilecek rol",
    mesaj_id="Tepki eklenecek mesajın ID'si. Boş bırakırsan yeni bir mesaj oluşturur.",
    baslik="Yeni mesaj oluşturulacaksa başlığı",
)
async def roltepki(
    interaction: discord.Interaction,
    emoji: str,
    rol: discord.Role,
    mesaj_id: str = None,
    baslik: str = "Rol Al",
):
    problem = role_problem(interaction.guild.me, rol)
    if problem:
        await interaction.response.send_message(problem, ephemeral=True)
        return

    # Aşağıda birkaç HTTP çağrısı var; 3 saniyelik pencereyi aşmamak için
    # önce defer ediyoruz.
    await interaction.response.defer(ephemeral=True)

    if mesaj_id:
        try:
            message = await interaction.channel.fetch_message(int(mesaj_id))
        except (ValueError, discord.NotFound):
            await interaction.followup.send(
                "Mesaj bulunamadı. Komutu mesajın bulunduğu kanalda çalıştır.", ephemeral=True
            )
            return
    else:
        message = await interaction.channel.send(
            embed=discord.Embed(
                title=baslik,
                description="Aşağıdaki emojiye tıklayarak rolü alabilirsin.",
                color=EMBED_COLOR,
            )
        )

    try:
        await message.add_reaction(emoji)
    except discord.HTTPException:
        await interaction.followup.send(
            "Bu emojiyi ekleyemedim. Başka bir sunucunun özel emojisi olabilir.", ephemeral=True
        )
        return

    try:
        await store.set(message.id, storage.emoji_key(emoji), rol.id)
    except ValueError as exc:
        await interaction.followup.send(str(exc), ephemeral=True)
        return

    await interaction.followup.send(
        f"{emoji} → **{rol.name}** eklendi. Mesaj ID: `{message.id}`\n"
        f"Bu mesajdaki eşleşmeler:\n{describe_mapping(interaction.guild, store.mapping_for(message.id))}",
        ephemeral=True,
        allowed_mentions=discord.AllowedMentions.none(),
    )


@app_commands.command(name="roltepkisil", description="Emoji-rol eşleşmesini kaldır")
@app_commands.describe(mesaj_id="Mesajın ID'si", emoji="Kaldırılacak emoji")
async def roltepkisil(interaction: discord.Interaction, mesaj_id: str, emoji: str):
    try:
        message_id = int(mesaj_id)
    except ValueError:
        await interaction.response.send_message("Geçersiz mesaj ID'si.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    if not await store.remove(message_id, storage.emoji_key(emoji)):
        await interaction.followup.send("Böyle bir eşleşme yok.", ephemeral=True)
        return

    # Mesaj başka kanalda olabilir; tepkiyi temizleyebilirsek temizleyelim.
    try:
        message = await interaction.channel.fetch_message(message_id)
        await message.clear_reaction(emoji)
    except discord.HTTPException:
        pass

    await interaction.followup.send("Eşleşme kaldırıldı.", ephemeral=True)


async def _handle_reaction(payload: discord.RawReactionActionEvent, add: bool) -> None:
    if payload.guild_id != GUILD_ID or payload.user_id == bot.user.id:
        return

    role_id = store.get(payload.message_id, storage.emoji_key(payload.emoji))
    if role_id is None:
        return

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return

    role = guild.get_role(role_id)
    if role is None:
        return

    problem = role_problem(guild.me, role)
    if problem:
        log.warning("Tepkiyle dağıtılamayan rol: %s (%s)", role.name, problem)
        return

    member = payload.member or guild.get_member(payload.user_id)
    if member is None:
        try:
            member = await guild.fetch_member(payload.user_id)
        except discord.HTTPException:
            return

    if member.bot:
        return

    try:
        if add:
            await member.add_roles(role, reason="Tepki rolü")
        else:
            await member.remove_roles(role, reason="Tepki rolü")
    except discord.Forbidden:
        log.warning("%s rolü yönetilemedi: yetki yok veya rol hiyerarşisi engelliyor", role.name)


@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    await _handle_reaction(payload, add=True)


@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    await _handle_reaction(payload, add=False)


# ------------------- /help -------------------
@app_commands.command(name="help", description="Komut yardım menüsü")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(title="Yardım Menüsü", description="Mevcut komutlar:", color=EMBED_COLOR)
    embed.add_field(name="/join", value="Botu ses kanalına sokar", inline=False)
    embed.add_field(name="/leave", value="Botu ses kanalından çıkarır", inline=False)
    embed.add_field(name="/mesajyaz", value="Bot mesaj gönderir", inline=False)
    embed.add_field(name="/nuke", value="Yazılı kanalı temizler (sadece Admin)", inline=False)
    embed.add_field(name="/ban", value="Kullanıcıyı banlar (sadece Admin)", inline=False)
    embed.add_field(name="/sunucubilgisi", value="Sunucu hakkında bilgi verir", inline=False)
    embed.add_field(
        name="/rolpanel", value="Butonla rol alma mesajı oluşturur (sadece Admin)", inline=False
    )
    embed.add_field(
        name="/roltepki",
        value="Emoji tepkisiyle rol veren mesaj oluşturur (sadece Admin)",
        inline=False,
    )
    embed.add_field(
        name="/roltepkisil", value="Emoji-rol eşleşmesini kaldırır (sadece Admin)", inline=False
    )
    await interaction.response.send_message(embed=embed)


# ------------------- /sunucubilgisi -------------------
@app_commands.command(name="sunucubilgisi", description="Sunucu hakkında bilgi verir")
async def sunucubilgisi(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(title=f"{guild.name} Bilgileri", color=EMBED_COLOR)
    embed.add_field(name="Üye Sayısı", value=guild.member_count, inline=True)
    embed.add_field(
        name="Oluşturulma Tarihi", value=guild.created_at.strftime("%d/%m/%Y"), inline=True
    )
    embed.add_field(name="Boost Sayısı", value=guild.premium_subscription_count, inline=True)
    await interaction.response.send_message(embed=embed)


for command in (
    join,
    leave,
    mesajyaz,
    nuke,
    ban,
    help,
    sunucubilgisi,
    rolpanel,
    roltepki,
    roltepkisil,
):
    bot.tree.add_command(command)

# log_handler=None: discord.py kendi handler'ını kurmasın, yukarıdaki
# basicConfig yeterli (aksi halde her satır iki kez basılıyor).
bot.run(TOKEN, log_handler=None)
