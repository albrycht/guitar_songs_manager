from __future__ import annotations

from pathlib import Path
from typing import Final

BASE_DIR: Final = Path(__file__).resolve().parent
DATA_DIR: Final = BASE_DIR.parent / "data"
DB_PATH: Final = DATA_DIR / "songs.db"

SUPPORTED_LANGUAGES: Final = ("pl", "en", "de", "es", "fr", "pt", "ru")
DEFAULT_LANGUAGE: Final = "pl"

LANGUAGE_TO_PYPHEN: Final = {
    "pl": "pl_PL",
    "en": "en_US",
    "de": "de_DE",
    "es": "es_ES",
    "fr": "fr_FR",
    "pt": "pt_PT",
    "ru": "ru_RU",
}
