"""/rolpanel — butonla rol alınan kalıcı panel."""

import discord
from discord import app_commands

from src.config import EMBED_COLOR, GUILD_ID, log
from src.helpers import role_problem

CUSTOM_ID_PREFIX = "rr:"


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
                    custom_id=f"{CUSTOM_ID_PREFIX}{role.id}",
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


async def on_interaction(interaction: discord.Interaction):
    """Panel butonlarına gelen tıklamalar."""
    if interaction.type is not discord.InteractionType.component:
        return

    custom_id = (interaction.data or {}).get("custom_id", "")
    if not custom_id.startswith(CUSTOM_ID_PREFIX):
        return

    # Butonlar sunucu üyelerine açık (rol panelinin amacı bu), ama yalnızca
    # kendi sunucumuzda ve yalnızca güvenli roller için.
    if interaction.guild_id != GUILD_ID or not isinstance(interaction.user, discord.Member):
        return

    role = interaction.guild.get_role(int(custom_id[len(CUSTOM_ID_PREFIX) :]))
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


def setup(bot):
    bot.tree.add_command(rolpanel)
    bot.add_listener(on_interaction)
