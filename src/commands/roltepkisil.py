"""/roltepkisil — emoji-rol eşleşmesini kaldırır."""

import discord
from discord import app_commands

import storage
from src.bot import store


@app_commands.command(name="roltepkisil", description="Emoji-rol eşleşmesini kaldır")
@app_commands.describe(mesaj_id="Mesajın ID'si", emoji="Kaldırılacak emoji")
async def roltepkisil(interaction: discord.Interaction, mesaj_id: str, emoji: str):
    try:
        message_id = int(mesaj_id)
    except ValueError:
        await interaction.response.send_message("Geçersiz mesaj ID'si.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    if not await store.remove(message_id, storage.emoji_key(emoji)):
        await interaction.followup.send("Böyle bir eşleşme yok.", ephemeral=True)
        return

    # Mesaj başka kanalda olabilir; tepkiyi temizleyebilirsek temizleyelim.
    try:
        message = await interaction.channel.fetch_message(message_id)
        await message.clear_reaction(emoji)
    except discord.HTTPException:
        pass

    await interaction.followup.send("Eşleşme kaldırıldı.", ephemeral=True)


def setup(bot):
    bot.tree.add_command(roltepkisil)
