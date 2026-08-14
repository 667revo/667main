"""/help — komut listesini komut ağacından üretir.

Liste elle tutulmuyor: src/commands altına yeni bir dosya eklediğinde
komut burada da kendiliğinden görünür.
"""

import discord
from discord import app_commands

from src.config import EMBED_COLOR

_bot = None


@app_commands.command(name="help", description="Komut yardım menüsü")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Yardım Menüsü",
        description="Mevcut komutlar (hepsi yalnızca yetkili rolde çalışır):",
        color=EMBED_COLOR,
    )

    commands = sorted(_bot.tree.get_commands(), key=lambda c: c.name)
    for command in commands:
        embed.add_field(
            name=f"/{command.name}",
            value=command.description or "—",
            inline=False,
        )

    embed.set_footer(text=f"{len(commands)} komut")
    await interaction.response.send_message(embed=embed)


def setup(bot):
    global _bot
    _bot = bot
    bot.tree.add_command(help_command)
