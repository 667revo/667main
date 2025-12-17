import discord
from discord import app_commands
from discord.ext import commands

# Bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

# Bot sınıfı
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        GUILD_ID =   # kendi sunucunun ID
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

bot = MyBot()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    activity = discord.Game(name="revorevorevorevo")
    await bot.change_presence(status=discord.Status.online, activity=activity)

# ------------------- /join -------------------
@app_commands.command(name="join", description="Botu ses kanalına sok")
@app_commands.describe(channel="Katılmak istediğiniz ses kanalı (opsiyonel)")
async def join(interaction: discord.Interaction, channel: discord.VoiceChannel = None):
    if channel is None:
        if interaction.user.voice is None:
            await interaction.response.send_message("ses kanalinda degilsin", ephemeral=True)
            return
        channel = interaction.user.voice.channel

    voice_client = interaction.guild.voice_client
    if voice_client:
        await voice_client.move_to(channel)
    else:
        await channel.connect()

    await interaction.response.send_message(f"**{channel.name}** joined")

# ------------------- /leave -------------------
@app_commands.command(name="leave", description="Botu ses kanalından çıkar")
async def leave(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client is None:
        await interaction.response.send_message("ses kanalinda degilim.", ephemeral=True)
        return

    await voice_client.disconnect()
    await interaction.response.send_message("leave")

# ------------------- /mesajyaz -------------------
@app_commands.command(name="mesajyaz", description="Bot mesaj gönderir")
@app_commands.describe(mesaj="Botun göndereceği mesaj")
async def mesajyaz(interaction: discord.Interaction, mesaj: str):
    await interaction.response.send_message(f"{mesaj}")

# ------------------- /nuke -------------------
@app_commands.command(name="nuke", description="Yazılı kanalı temizle")
@app_commands.describe(channel="Temizlenecek yazılı kanal")
async def nuke(interaction: discord.Interaction, channel: discord.TextChannel):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(" Bu komutu kullanmak için yönetici olmalısın.", ephemeral=True)
        return

    category = channel.category
    position = channel.position
    overwrites = channel.overwrites

    await interaction.response.send_message(f"nukelaniyor {channel.name}", ephemeral=True)


    # Kanalı sil
    await channel.delete()

    new_channel = await interaction.guild.create_text_channel(
        name=channel.name,
        category=category,
        overwrites=overwrites,
        position=position
    )

    await new_channel.send(f"nuked by {interaction.user.mention}")


bot.tree.add_command(join)
bot.tree.add_command(leave)
bot.tree.add_command(mesajyaz)
bot.tree.add_command(nuke)

# Botu çalıştır
bot.run("tokengos here")
