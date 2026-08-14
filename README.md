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
| `/help` | Komut yardım menüsü (liste otomatik üretilir) |
| `/sunucubilgisi` | Sunucu hakkında bilgi verir |
| `/nuke` | Yazılı kanalı siler ve yeniden oluşturur |
| `/ban` | Kullanıcıyı banlar |
| `/rolpanel` | Butonla rol alma mesajı oluşturur (5 role kadar) |
| `/roltepki` | Bir mesaja emoji tepkisiyle rol ekler |
| `/roltepkisil` | Emoji-rol eşleşmesini kaldırır |
| `/guildrolesetup` | Sunucu etiketini takanlara otomatik rol verir, kaldıranlardan alır |
| `/guildrolegive` | Guild rolünü etiketi takan herkese veya tek kişiye verir |
| `/toplurol` | Seçilen rolü sunucudaki herkese verir |

Rol panelindeki **butonlara ve emojilere sunucudaki herkes** tıklayabilir — rol dağıtımının
amacı bu. Kısıtlanan şey panelin *kurulması*, kullanılması değil.

## Proje yapısı

```
main.py                    giriş noktası (bot kurulumu + komutları yükle + çalıştır)
storage.py                 kalıcı depolama (tepki-rol eşleşmeleri ve ayarlar)
src/
  config.py                ortam değişkenleri ve sabitler
  bot.py                   bot sınıfı, yetki kontrolü, ortak `store`
  helpers.py               paylaşılan yardımcılar (role_problem, toplu rol verme, onay penceresi)
  guildtag.py              sunucu etiketi rol otomasyonunun mantığı ve olayları
  commands/
    __init__.py            komut dosyalarını otomatik bulup yükler
    _ornek.py              yeni komut şablonu (alt çizgi ile başladığı için yüklenmez)
    join.py, ban.py, ...   her komut kendi dosyasında
```

### Yeni komut ekleme

1. `src/commands/_ornek.py` dosyasını kopyala, `src/commands/komutadi.py` olarak kaydet.
2. Komutu yaz, dosyanın altındaki `setup(bot)` içinde `bot.tree.add_command(...)` ile ekle.
3. Botu yeniden başlat.

`main.py`'ye hiçbir şey eklemene gerek yok — `src/commands/` içindeki her dosya otomatik
yükleniyor. Alt çizgiyle başlayan dosyalar atlanır. Yetki kontrolü merkezi olduğu için
komut dosyasında ayrıca yazman gerekmez.

Olay dinlemek istersen aynı dosyada:

```python
async def on_member_join(member):
    ...

def setup(bot):
    bot.tree.add_command(komutum)
    bot.add_listener(on_member_join)
```

`bot.add_listener` sayesinde **aynı olayı birden fazla dosya dinleyebilir**; düz
`@bot.event` kullansaydın ikinci dosya birincisini ezerdi.

## Sunucu etiketi (guild) rolü

Discord'un "Sunucu Etiketi" özelliğinde kullanıcı bir sunucuyu birincil sunucu seçip
etiketini profilinde taşır. Bot bunu izleyip rol dağıtır:

- `/guildrolesetup rol:@Rol` — sistemi kurar. `otomatik_ver`, `otomatik_al` ve `aktif`
  parametreleriyle davranışı ayarlarsın; parametresiz çalıştırınca mevcut ayarı gösterir.
- Etiketi takan rolü **anında** alır, kaldıran kaybeder. Sunucuya etiketi zaten takılı
  gelen yeni üyeler de yakalanır.
- `/guildrolegive` — sistem kurulmadan önce etiketi takmış olanlara rolü toplu verir.
  `kullanici` parametresiyle tek bir kişiye elle de verebilirsin.

Ayar, tepki-rol eşleşmeleriyle aynı yerde saklanır (bkz. `CONFIG_CHANNEL_ID`), yani bot
yeniden başlayınca kaybolmaz.

## Güvenlik

- Bot yalnızca `GUILD_ID` sunucusunda çalışır; başka bir sunucuya eklenirse otomatik ayrılır.
- Yetkili rolü olmayan komut denemeleri reddedilir ve loglanır.
- `Administrator`, `Manage Roles`, `Ban Members` gibi yetkiler taşıyan roller dağıtılamaz —
  aksi halde herkesin tıklayabildiği bir buton veya toplu komut yetki yükseltme aracına
  dönerdi. Bu kontrol panel kurulurken, her tıklamada ve toplu komutlarda tekrar yapılır.
- `/toplurol` herkesi etkilediği için dağıtımdan önce onay butonu sorar.

Rol dağıtımının yolları:

- **`/rolpanel`** — mesajın altına buton koyar. Tıklayan rolü alır, tekrar tıklayan bırakır.
- **`/roltepki`** — klasik emoji tepkisi. `mesaj_id` verirsen **var olan herhangi bir mesaja**
  ekler (kendi yazdığın duyuru, eski bir mesaj, fark etmez); boş bırakırsan yeni bir mesaj
  oluşturur. Aynı mesaja birden çok emoji-rol eklemek için komutu aynı `mesaj_id` ile tekrarla.
  Komutu, mesajın bulunduğu kanalda çalıştır.
- **`/guildrolesetup`** — sunucu etiketine göre otomatik.
- **`/toplurol`** — tek seferlik toplu dağıtım.

İlk üçü bot yeniden başladıktan sonra da çalışmaya devam eder.

## Kurulum

Ayarlar ortam değişkenlerinden okunur, koda gömülü değildir — bkz. `.env.example`.

| Değişken | Zorunlu | Açıklama |
|---|---|---|
| `DISCORD_TOKEN` | evet | Bot token'ı |
| `GUILD_ID` | evet | Komutların senkronlanacağı sunucu |
| `ADMIN_ROLE_ID` | hayır | Admin rolünün ID'si |
| `ADMIN_ROLE_NAME` | hayır | `ADMIN_ROLE_ID` boşsa kullanılır (varsayılan: `admin rolü`) |
| `CONFIG_CHANNEL_ID` | Heroku'da evet | Eşleşmelerin ve ayarların saklandığı kanal |
| `DATA_PATH` | hayır | `CONFIG_CHANNEL_ID` boşsa kullanılan yerel dosya |

Deploy ve çalıştırma adımları için [DEPLOY.md](DEPLOY.md).

2026
