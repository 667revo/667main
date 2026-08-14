"""/guildrolesetup — sunucu etiketi (guild) rol otomasyonunun ayarı.

Otomasyonun kendisi src/guildtag.py içinde; olay dinleyicileri de buradan
kaydediliyor.
"""

import discord
from discord import app_commands

from src import guildtag
from src.bot import store
from src.helpers import role_problem


@app_commands.command(
    name="guildrolesetup",
    description="Sunucu etiketini (guild) takanlara otomatik rol ver/al",
)
@app_commands.describe(
    rol="Etiketi takan kullanıcılara verilecek rol",
    otomatik_ver="Etiketi takana rol otomatik verilsin mi (varsayılan: evet)",
    otomatik_al="Etiketi kaldırandan rol otomatik alınsın mı (varsayılan: evet)",
    aktif="Sistemi aç/kapat",
)
async def guildrolesetup(
    interaction: discord.Interaction,
    rol: discord.Role = None,
    otomatik_ver: bool = None,
    otomatik_al: bool = None,
    aktif: bool = None,
):
    config = guildtag.raw_config()

    # Hiç parametre verilmediyse mevcut ayarı göster.
    if rol is None and otomatik_ver is None and otomatik_al is None and aktif is None:
        if not config.get("role_id"):
            await interaction.response.send_message(
                "Henüz bir guild rolü ayarlanmamış. `/guildrolesetup rol:@Rol` ile kur.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            embed=guildtag.config_embed(interaction.guild, config), ephemeral=True
        )
        return

    if rol is not None:
        problem = role_problem(interaction.guild.me, rol)
        if problem:
            await interaction.response.send_message(problem, ephemeral=True)
            return
        config["role_id"] = rol.id

    if not config.get("role_id"):
        await interaction.response.send_message(
            "Önce bir rol seçmelisin: `/guildrolesetup rol:@Rol`", ephemeral=True
        )
        return

    if otomatik_ver is not None:
        config["auto_add"] = otomatik_ver
    if otomatik_al is not None:
        config["auto_remove"] = otomatik_al
    if aktif is not None:
        config["enabled"] = aktif

    config.setdefault("auto_add", True)
    config.setdefault("auto_remove", True)
    config.setdefault("enabled", True)

    await interaction.response.defer(ephemeral=True)

    try:
        await store.set_setting(guildtag.SETTING_KEY, config)
    except ValueError as exc:
        await interaction.followup.send(str(exc), ephemeral=True)
        return

    embed = guildtag.config_embed(interaction.guild, config)
    embed.set_footer(text="Şu an etiketi takan üyelere de vermek için: /guildrolegive")
    await interaction.followup.send(embed=embed, ephemeral=True)


def setup(bot):
    bot.tree.add_command(guildrolesetup)
    # Etiket takma/çıkarma olaylarını dinlemeye başla.
    guildtag.register(bot)
