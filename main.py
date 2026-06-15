import requests
import discord
from discord import app_commands
from discord.ext import commands


intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True


ADMIN_ROLE_NAME = "admin rolü"


class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        GUILD_ID = # GUILD ID 
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

bot = MyBot()

def is_admin(interaction: discord.Interaction) -> bool:
    return any(role.name == ADMIN_ROLE_NAME for role in interaction.user.roles)

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
    if not is_admin(interaction):
        await interaction.response.send_message("Bu komutu kullanmak için yönetici olmalısın.", ephemeral=True)
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

# ------------------- /ban -------------------
@app_commands.command(name="ban", description="Kullanıcıyı banla")
@app_commands.describe(user="Banlanacak kullanıcı", reason="Ban sebebi (opsiyonel)")
async def ban(interaction: discord.Interaction, user: discord.User, reason: str = None):
    if not is_admin(interaction):
        await interaction.response.send_message("Bu komutu kullanmak için yönetici olmalısın.", ephemeral=True)
        return
    
    try:
        await interaction.guild.ban(user, reason=reason)
        await interaction.response.send_message(f"{user.mention} başarıyla banlandı. Sebep: {reason or 'Belirtilmedi'}")
    except discord.Forbidden:
        await interaction.response.send_message("Bu kullanıcıyı banlamak için yetkim yok.", ephemeral=True)

# ------------------- /help -------------------
@app_commands.command(name="help", description="Komut yardım menüsü")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(title="Yardım Menüsü", description="Mevcut komutlar:", color=0x00ff00)
    embed.add_field(name="/join", value="Botu ses kanalına sokar", inline=False)
    embed.add_field(name="/leave", value="Botu ses kanalından çıkarır", inline=False)
    embed.add_field(name="/mesajyaz", value="Bot mesaj gönderir", inline=False)
    embed.add_field(name="/nuke", value="Yazılı kanalı temizler", inline=False)
    embed.add_field(name="/ban", value="Kullanıcıyı banlar (sadece Admin)", inline=False)
    embed.add_field(name="/sunucubilgisi", value="Sunucu hakkında bilgi verir", inline=False)
    await interaction.response.send_message(embed=embed)

# ------------------- /sunucubilgisi -------------------
@app_commands.command(name="sunucubilgisi", description="Sunucu hakkında bilgi verir")
async def sunucubilgisi(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(title=f"{guild.name} Bilgileri", color=0x00ff00)
    embed.add_field(name="Üye Sayısı", value=guild.member_count, inline=True)
    embed.add_field(name="Oluşturulma Tarihi", value=guild.created_at.strftime("%d/%m/%Y"), inline=True)
    embed.add_field(name="Boost Sayısı", value=guild.premium_subscription_count, inline=True)
    await interaction.response.send_message(embed=embed)

bot.tree.add_command(join)
bot.tree.add_command(leave)
bot.tree.add_command(mesajyaz)
bot.tree.add_command(nuke)
bot.tree.add_command(ban)
bot.tree.add_command(help)
bot.tree.add_command(sunucubilgisi)

bot.run("tokenhere")
