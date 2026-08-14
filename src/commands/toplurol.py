"""/toplurol — seçilen rolü sunucudaki herkese verir (onay adımıyla)."""

import discord
from discord import app_commands

from src.helpers import ConfirmView, bulk_add_role, ensure_members, role_problem


@app_commands.command(name="toplurol", description="Seçilen rolü sunucudaki herkese ver")
@app_commands.describe(
    rol="Herkese verilecek rol", botlar="Botlara da verilsin mi (varsayılan: hayır)"
)
async def toplurol(interaction: discord.Interaction, rol: discord.Role, botlar: bool = False):
    problem = role_problem(interaction.guild.me, rol)
    if problem:
        await interaction.response.send_message(problem, ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    guild = interaction.guild
    await ensure_members(guild)

    targets = [m for m in guild.members if (botlar or not m.bot) and rol not in m.roles]
    if not targets:
        await interaction.followup.send(f"**{rol.name}** rolü zaten herkeste var.", ephemeral=True)
        return

    # Geri alması zahmetli bir işlem: önce onay iste.
    view = ConfirmView(interaction.user.id)
    prompt = await interaction.followup.send(
        f"**{len(targets)}** kişiye **{rol.name}** rolü verilecek. Onaylıyor musun?",
        view=view,
        ephemeral=True,
        wait=True,
    )
    await view.wait()

    if not view.value:
        await prompt.edit(
            content="İptal edildi." if view.value is False else "Süre doldu, işlem yapılmadı.",
            view=None,
        )
        return

    await prompt.edit(content=f"Dağıtılıyor... 0/{len(targets)}", view=None)

    async def progress(done: int, total: int) -> None:
        try:
            await prompt.edit(content=f"Dağıtılıyor... {done}/{total}")
        except discord.HTTPException:
            pass  # interaction token'ı 15 dakikada dolabilir, işlemi durdurma

    given, failed = await bulk_add_role(
        targets, rol, reason=f"/toplurol - {interaction.user}", progress=progress
    )

    summary = f"**{rol.name}**: {given} kişiye verildi."
    if failed:
        summary += f" {failed} kişide hata oldu (yetki/rol hiyerarşisi)."
    try:
        await prompt.edit(content=summary)
    except discord.HTTPException:
        await interaction.followup.send(summary, ephemeral=True)


def setup(bot):
    bot.tree.add_command(toplurol)
