# 667main

Discord Bot For Server 667

Project created for our own requirements. Turkish lang based.

## Komutlar

**Tüm slash komutlar yalnızca yetkili rol tarafından çalıştırılabilir** (`ADMIN_ROLE_ID`).
Sunucu yöneticiliği muafiyet sağlamaz — yetki tek bir role bağlıdır.

| Komut | Açıklama |
|---|---|
| `/join` | Botu ses kanalına sokar |
| `/leave` | Botu ses kanalından çıkarır |
| `/mesajyaz` | Bot mesaj gönderir |
| `/help` | Komut yardım menüsü |
| `/sunucubilgisi` | Sunucu hakkında bilgi verir |
| `/nuke` | Yazılı kanalı siler ve yeniden oluşturur |
| `/ban` | Kullanıcıyı banlar |
| `/rolpanel` | Butonla rol alma mesajı oluşturur (5 role kadar) |
| `/roltepki` | Bir mesaja emoji tepkisiyle rol ekler |
| `/roltepkisil` | Emoji-rol eşleşmesini kaldırır |

Rol panelindeki **butonlara ve emojilere sunucudaki herkes** tıklayabilir — rol dağıtımının
amacı bu. Kısıtlanan şey panelin *kurulması*, kullanılması değil.

## Güvenlik

- Bot yalnızca `GUILD_ID` sunucusunda çalışır; başka bir sunucuya eklenirse otomatik ayrılır.
- Yetkili rolü olmayan komut denemeleri reddedilir ve loglanır.
- `Administrator`, `Manage Roles`, `Ban Members` gibi yetkiler taşıyan roller panelden
  dağıtılamaz — aksi halde herkesin tıklayabildiği bir buton yetki yükseltme aracına dönerdi.
  Bu kontrol hem panel kurulurken hem de her tıklamada tekrar yapılır.

Rol dağıtımının iki yolu var:

- **`/rolpanel`** — mesajın altına buton koyar. Tıklayan rolü alır, tekrar tıklayan bırakır.
- **`/roltepki`** — klasik emoji tepkisi. `mesaj_id` verirsen **var olan herhangi bir mesaja**
  ekler (kendi yazdığın duyuru, eski bir mesaj, fark etmez); boş bırakırsan yeni bir mesaj
  oluşturur. Aynı mesaja birden çok emoji-rol eklemek için komutu aynı `mesaj_id` ile tekrarla.
  Komutu, mesajın bulunduğu kanalda çalıştır.

İkisi de bot yeniden başladıktan sonra çalışmaya devam eder.

## Kurulum

Ayarlar ortam değişkenlerinden okunur, koda gömülü değildir — bkz. `.env.example`.

| Değişken | Zorunlu | Açıklama |
|---|---|---|
| `DISCORD_TOKEN` | evet | Bot token'ı |
| `GUILD_ID` | evet | Komutların senkronlanacağı sunucu |
| `ADMIN_ROLE_ID` | hayır | Admin rolünün ID'si |
| `ADMIN_ROLE_NAME` | hayır | `ADMIN_ROLE_ID` boşsa kullanılır (varsayılan: `admin rolü`) |
| `CONFIG_CHANNEL_ID` | Heroku'da evet | Tepki-rol eşleşmelerinin saklandığı kanal |
| `DATA_PATH` | hayır | `CONFIG_CHANNEL_ID` boşsa kullanılan yerel dosya |

Sunucu yöneticisi yetkisi olanlar `ADMIN_ROLE_*` ayarından bağımsız olarak admin sayılır.

Deploy ve çalıştırma adımları için [DEPLOY.md](DEPLOY.md).

2026
