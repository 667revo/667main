"""Komut dosyalarını otomatik bulup yükleyen katman.

Bu klasöre yeni bir .py dosyası koyup içine `setup(bot)` fonksiyonu yazman
yeterli; main.py'ye hiçbir şey eklemene gerek yok. Alt çizgiyle başlayan
dosyalar (örn. _ornek.py) yüklenmez, şablon olarak durabilir.
"""

import importlib
import pkgutil

from src.config import log


def load_all(bot) -> list[str]:
    """Klasördeki tüm komut modüllerini yükler, yüklenenlerin adını döner."""
    loaded: list[str] = []

    for module_info in sorted(pkgutil.iter_modules(__path__), key=lambda m: m.name):
        if module_info.name.startswith("_"):
            continue

        module = importlib.import_module(f"{__name__}.{module_info.name}")
        setup = getattr(module, "setup", None)
        if setup is None:
            log.warning(
                "%s içinde setup(bot) fonksiyonu yok, atlandı.", module_info.name
            )
            continue

        setup(bot)
        loaded.append(module_info.name)

    log.info("%d komut dosyası yüklendi: %s", len(loaded), ", ".join(loaded))
    return loaded
