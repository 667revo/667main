"""/nuke — kanalı silip aynı ayarlarla yeniden kurar."""

import discord
from discord import app_commands


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


def setup(bot):
    bot.tree.add_command(nuke)
