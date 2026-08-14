"""/mesajyaz — bot ağzından mesaj gönderir."""

import discord
from discord import app_commands


@app_commands.command(name="mesajyaz", description="Bot mesaj gönderir")
@app_commands.describe(mesaj="Botun göndereceği mesaj")
async def mesajyaz(interaction: discord.Interaction, mesaj: str):
    # Botun @everyone ping'i için kullanılmasını engelle.
    await interaction.response.send_message(
        mesaj, allowed_mentions=discord.AllowedMentions.none()
    )


def setup(bot):
    bot.tree.add_command(mesajyaz)
