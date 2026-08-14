"""/leave — botu ses kanalından çıkarır."""

import discord
from discord import app_commands


@app_commands.command(name="leave", description="Botu ses kanalından çıkar")
async def leave(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client is None:
        await interaction.response.send_message("ses kanalinda degilim.", ephemeral=True)
        return

    await interaction.response.defer()
    await voice_client.disconnect()
    await interaction.followup.send("leave")


def setup(bot):
    bot.tree.add_command(leave)
