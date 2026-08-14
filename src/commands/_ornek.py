"""ŞABLON — yeni komut eklerken bu dosyayı kopyala.

Alt çizgiyle başladığı için yüklenmez. Yeni komut için:
1. Bu dosyayı `src/commands/komutadi.py` olarak kopyala.
2. Komutu yaz, altındaki setup(bot) içinde ağaca ekle.
3. Botu yeniden başlat. main.py'ye dokunmana gerek yok.

Notlar:
- Yetki kontrolü (admin rolü) RestrictedTree'de merkezi, burada tekrar yazma.
- Rol dağıtan bir komutsa `role_problem` ile güvenlik kontrolünü yap.
- 3 saniyeden uzun sürebilecek işlerden önce `interaction.response.defer()`.
- Olay dinlemek istersen: `bot.add_listener(fonksiyonum, "on_member_join")`.
"""

import discord
from discord import app_commands

from src.config import EMBED_COLOR


@app_commands.command(name="ornek", description="Örnek komut")
@app_commands.describe(metin="Yazılacak metin")
async def ornek(interaction: discord.Interaction, metin: str):
    embed = discord.Embed(title="Örnek", description=metin, color=EMBED_COLOR)
    await interaction.response.send_message(embed=embed)


def setup(bot):
    bot.tree.add_command(ornek)
