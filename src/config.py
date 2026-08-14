"""Ortam değişkenleri ve sabitler.

Hiçbir şeye bağımlı olmayan en alt katman: diğer bütün modüller buradan okur,
burası hiçbir modülü import etmez. Böylece döngüsel import riski kalmıyor.
"""

import logging
import os

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("667bot")


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"{name} tanımlı değil. .env dosyasını kontrol et.")
    return value


TOKEN = _require("DISCORD_TOKEN")
GUILD_ID = int(_require("GUILD_ID"))
ADMIN_ROLE_ID = os.getenv("ADMIN_ROLE_ID")
ADMIN_ROLE_NAME = os.getenv("ADMIN_ROLE_NAME", "admin rolü")
CONFIG_CHANNEL_ID = os.getenv("CONFIG_CHANNEL_ID")
DATA_PATH = os.getenv("DATA_PATH", "data/roles.json")

# Tüm embed'lerin kenar rengi (koyu mor)
EMBED_COLOR = 0x5B2C6F
