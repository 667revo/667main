"""/roltepki — emoji tepkisiyle rol veren mesaj + tepki olayları.

Eşleşmeleri silen komut ayrı dosyada: roltepkisil.py
"""

import discord
from discord import app_commands

import storage
from src.bot import store
from src.config import EMBED_COLOR, GUILD_ID, log
from src.helpers import role_problem

_bot = None


def render_emoji(key: str) -> str:
    """Depolama anahtarını görüntülenebilir emojiye çevirir."""
    if key.isdigit():
        emoji = _bot.get_emoji(int(key)) if _bot else None
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


async def _handle_reaction(payload: discord.RawReactionActionEvent, add: bool) -> None:
    if payload.guild_id != GUILD_ID or (_bot and payload.user_id == _bot.user.id):
        return

    role_id = store.get(payload.message_id, storage.emoji_key(payload.emoji))
    if role_id is None:
        return

    guild = _bot.get_guild(payload.guild_id) if _bot else None
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


async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    await _handle_reaction(payload, add=True)


async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    await _handle_reaction(payload, add=False)


def setup(bot):
    global _bot
    _bot = bot
    bot.tree.add_command(roltepki)
    bot.add_listener(on_raw_reaction_add)
    bot.add_listener(on_raw_reaction_remove)
