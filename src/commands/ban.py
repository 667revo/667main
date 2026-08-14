"""/ban — kullanıcıyı sunucudan yasaklar."""

import discord
from discord import app_commands


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


def setup(bot):
    bot.tree.add_command(ban)
