"""667bot — giriş noktası.

Bu dosya bilerek ince tutuldu: bot burada kuruluyor, komutlar
src/commands/ klasöründen otomatik yükleniyor ve bot çalıştırılıyor.

Yeni komut eklemek için buraya dokunmana gerek yok:
src/commands/ içine `setup(bot)` fonksiyonu olan bir .py dosyası koyman
yeterli (şablon: src/commands/_ornek.py).
"""

import discord

from src.bot import MyBot
from src.commands import load_all
from src.config import GUILD_ID, TOKEN, log

bot = MyBot()


@bot.event
async def on_ready():
    log.info("Giriş yapıldı: %s", bot.user)
    activity = discord.Game(name="revorevorevorevo")
    await bot.change_presence(status=discord.Status.online, activity=activity)


@bot.event
async def on_guild_join(guild: discord.Guild):
    """Bot başka bir sunucuya eklenirse orada çalışmasın."""
    if guild.id != GUILD_ID:
        log.warning("İzinsiz sunucuya eklendi, çıkılıyor: %s (%s)", guild.name, guild.id)
        await guild.leave()


load_all(bot)

# log_handler=None: discord.py kendi handler'ını kurmasın, config.py'deki
# basicConfig yeterli (aksi halde her satır iki kez basılıyor).
bot.run(TOKEN, log_handler=None)
