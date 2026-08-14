"""/join — botu ses kanalına sokar."""

import discord
from discord import app_commands


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


def setup(bot):
    bot.tree.add_command(join)
