"""Birden fazla komutun paylaştığı yardımcılar."""

import discord

from src.config import log

# Rol dağıtımıyla yetki yükseltilmesini engellemek için: bu yetkilerden birine
# sahip bir rol butonla/tepkiyle/toplu komutla dağıtılamaz.
DANGEROUS_PERMISSIONS = (
    "administrator",
    "manage_guild",
    "manage_roles",
    "manage_channels",
    "manage_webhooks",
    "manage_messages",
    "ban_members",
    "kick_members",
    "moderate_members",
    "mention_everyone",
)


def role_problem(me: discord.Member, role: discord.Role) -> str | None:
    """Rol dağıtıma uygun mu? Uygunsa None, değilse sebebi döner."""
    if not me.guild_permissions.manage_roles:
        return "Rol dağıtabilmem için `Rolleri Yönet` yetkisine ihtiyacım var."
    if role.is_default():
        return "@everyone rolü dağıtılamaz."
    if role.managed:
        return f"**{role.name}** bir entegrasyon rolü, Discord elle verilmesine izin vermiyor."
    if role >= me.top_role:
        return (
            f"**{role.name}** benim rolümden yüksek, veremem. "
            "Sunucu ayarlarından benim rolümü bu rolün üstüne taşı."
        )

    granted = [p for p in DANGEROUS_PERMISSIONS if getattr(role.permissions, p)]
    if granted:
        return (
            f"**{role.name}** yetkili bir rol ({', '.join(granted)}). "
            "Herkesin tıklayabildiği bir panelden dağıtılırsa yetki yükseltmeye "
            "açık hale gelir, bu yüzden engellendi."
        )
    return None


async def bulk_add_role(
    members: list[discord.Member],
    role: discord.Role,
    reason: str,
    progress=None,
) -> tuple[int, int]:
    """Birden fazla üyeye rol verir. (verilen, hata) sayısını döner.

    progress verilirse her 25 üyede bir `await progress(sayac, toplam)` çağrılır.
    Yetki hatasında herkeste aynı sonuç çıkacağı için döngü erken biter.
    """
    given = failed = 0
    for index, member in enumerate(members, start=1):
        try:
            await member.add_roles(role, reason=reason)
            given += 1
        except discord.Forbidden:
            failed += 1
            log.warning("%s rolü verilemedi: yetki veya rol hiyerarşisi engelliyor", role.name)
            break
        except discord.HTTPException as exc:
            failed += 1
            log.warning("%s rolü %s üyesine verilemedi: %s", role.name, member, exc)

        if progress is not None and index % 25 == 0:
            await progress(index, len(members))
    return given, failed


async def ensure_members(guild: discord.Guild) -> None:
    """Üye listesinin önbellekte tam olduğundan emin olur (toplu tarama öncesi)."""
    if not guild.chunked:
        await guild.chunk()


class ConfirmView(discord.ui.View):
    """Tek kullanımlık onay penceresi (geri alması zor toplu işlemler için)."""

    def __init__(self, user_id: int, timeout: float = 60):
        super().__init__(timeout=timeout)
        self.user_id = user_id
        self.value: bool | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Bu onay sana ait değil.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Onayla", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="İptal", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        await interaction.response.defer()
        self.stop()
