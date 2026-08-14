"""/guildrolegive — guild rolünü geçmişe dönük veya tek kişiye verir."""

import discord
from discord import app_commands

from src import guildtag
from src.helpers import bulk_add_role, ensure_members, role_problem


@app_commands.command(
    name="guildrolegive",
    description="Guild rolünü etiketi takanlara veya belirli bir kişiye ver",
)
@app_commands.describe(
    kullanici="Sadece bu kişiye ver. Boş bırakırsan etiketi takan herkese verilir.",
    rol="Ayarlı rol yerine bu rolü kullan (opsiyonel)",
)
async def guildrolegive(
    interaction: discord.Interaction,
    kullanici: discord.Member = None,
    rol: discord.Role = None,
):
    config = guildtag.active_config()
    role = rol or (interaction.guild.get_role(int(config["role_id"])) if config else None)
    if role is None:
        await interaction.response.send_message(
            "Ayarlı bir guild rolü yok. Önce `/guildrolesetup` çalıştır ya da `rol` "
            "parametresiyle rol seç.",
            ephemeral=True,
        )
        return

    problem = role_problem(interaction.guild.me, role)
    if problem:
        await interaction.response.send_message(problem, ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    # ---- tek kişi ----
    if kullanici is not None:
        if role in kullanici.roles:
            await interaction.followup.send(
                f"{kullanici.mention} zaten **{role.name}** rolüne sahip.",
                ephemeral=True,
                allowed_mentions=discord.AllowedMentions.none(),
            )
            return
        try:
            await kullanici.add_roles(role, reason=f"/guildrolegive - {interaction.user}")
        except discord.Forbidden:
            await interaction.followup.send(
                "Bu rolü veremedim. Rolüm hedef rolün üstünde olmalı.", ephemeral=True
            )
            return

        note = (
            ""
            if guildtag.wears_guild_tag(kullanici)
            else "\n*Not: bu kullanıcı sunucu etiketini takmıyor.*"
        )
        await interaction.followup.send(
            f"{kullanici.mention} kullanıcısına **{role.name}** verildi.{note}",
            ephemeral=True,
            allowed_mentions=discord.AllowedMentions.none(),
        )
        return

    # ---- etiketi takan herkes ----
    guild = interaction.guild
    await ensure_members(guild)

    targets = [
        m
        for m in guild.members
        if not m.bot and guildtag.wears_guild_tag(m) and role not in m.roles
    ]
    if not targets:
        await interaction.followup.send(
            "Etiketi takıp da bu role sahip olmayan kimse yok.", ephemeral=True
        )
        return

    given, failed = await bulk_add_role(
        targets, role, reason=f"/guildrolegive - {interaction.user}"
    )

    summary = f"**{role.name}**: {given} kişiye verildi."
    if failed:
        summary += f" {failed} kişide hata oldu (yetki/rol hiyerarşisi)."
    await interaction.followup.send(summary, ephemeral=True)


def setup(bot):
    bot.tree.add_command(guildrolegive)
