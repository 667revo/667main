# Deploy

## 1. Discord tarafı

Discord Developer Portal > uygulaman > **Bot**:

- **Reset Token** — eski token `main.py` içinde düz metin olarak git geçmişine girdi, mutlaka yenile.
- **Privileged Gateway Intents > SERVER MEMBERS INTENT: açık.** Tepki kaldırıldığında üyeyi bulmak için gerekli, kapalıysa bot açılışta hata verip durur.
- MESSAGE CONTENT INTENT gerekmiyor (prefix komut kullanmıyoruz).

**OAuth2 > URL Generator** ile davet linki: `bot` + `applications.commands` scope'ları, yetkiler:
`Manage Roles`, `Manage Channels`, `Ban Members`, `Send Messages`, `Add Reactions`, `Read Message History`, `Connect`.

Sunucu ayarlarında **botun rolünü dağıtacağı rollerin üstüne taşı.** Discord, kendi rolünden yüksek bir rolü vermene izin vermez.

## 2. Heroku

Bot bir HTTP sunucusu değil, o yüzden `web` değil **`worker`** dyno olarak çalışır — `Procfile` bunu belirtiyor.

```bash
heroku login
```

```bash
heroku git:remote -a z667dev
```

Config vars (`.env` yerine bunlar geçiyor):

```bash
heroku config:set DISCORD_TOKEN=yeni_token GUILD_ID=sunucu_id ADMIN_ROLE_ID=admin_rol_id
```

Deploy:

```bash
git add -A && git commit -m "Heroku worker deploy" && git push heroku main
```

Worker dyno'yu başlat — yeni uygulamalarda otomatik başlamaz:

```bash
heroku ps:scale worker=1
```

Logları izle:

```bash
heroku logs --tail -a z667dev
```

`Logged in as ...` satırını gördüysen bot ayakta.

### Dyno planı

Ücretsiz katman 2022'de kalktı. **Basic ($7/ay)** uykuya geçmez, 7/24 çalışır — güvenli seçim.
Eco ($5/ay, 1000 saat havuzu) da 730 saatlik aylık ihtiyacı karşılar, ancak Eco dyno'ların
uyku davranışı web dışı dyno'larda net değil; kredin varsa Basic'te kal.

Heroku dyno'ları günde en az bir kez yeniden başlatır. Bot otomatik olarak yeniden bağlanır,
birkaç saniyelik kesinti dışında etkisi olmaz.

### Kalıcılık — `CONFIG_CHANNEL_ID`

Heroku'nun dosya sistemi geçicidir; her yeniden başlatmada sıfırlanır. Bu yüzden emoji-rol
eşleşmeleri diske değil, **Discord'un kendisine** yazılır: bot, `CONFIG_CHANNEL_ID` ile
verdiğin kanalda tek bir "durum mesajı" tutar ve eşleşmeler değiştikçe onu günceller.
Veritabanı eklentisi gerekmiyor, deploy'lar ve dyno döngüsü eşleşmeleri bozmuyor.

Üyelere kapalı bir kanal aç (örn. `#bot-config`), ID'sini kopyala ve ayarla:

```bash
heroku config:set CONFIG_CHANNEL_ID=kanal_id
```

Bu kanaldaki `667bot-state` ile başlayan mesajı **silme** — tüm eşleşmeler orada.
Durum mesajı 2000 karakterle sınırlı; pratikte ~50 eşleşme sığar, dolarsa bot uyarır.

`CONFIG_CHANNEL_ID` boş bırakılırsa yerel `data/roles.json` dosyasına düşer. Bu yalnızca
kendi sunucunda veya yerelde işe yarar; Heroku'da her yeniden başlatmada eşleşmeler silinir.

## 3. Yerelde çalıştırma

```bash
python3 -m venv venv && ./venv/bin/pip install -r requirements.txt
```

`.env.example`'ı `.env` olarak kopyalayıp doldur, sonra:

```bash
./venv/bin/python main.py
```

## 4. Kendi sunucunda (VM) çalıştırma

Heroku yerine bir Linux sunucu kullanacaksan `667bot.service` hazır. Kodu `/opt/667bot` altına
koy, `.env` dosyasını oluştur, sonra:

```bash
sudo cp 667bot.service /etc/systemd/system/ && sudo systemctl enable --now 667bot
```

Servis boot'ta başlar, çökerse 10 saniyede geri gelir. `journalctl -u 667bot -f` ile log izlenir.
