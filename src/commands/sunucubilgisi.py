"""/sunucubilgisi — sunucu istatistikleri."""

import discord
from discord import app_commands

from src.config import EMBED_COLOR


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


def setup(bot):
    bot.tree.add_command(sunucubilgisi)
