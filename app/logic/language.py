from __future__ import annotations

from langdetect import DetectorFactory, detect

from ..settings import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES

DetectorFactory.seed = 0


def detect_language(text: str) -> str:
    if not text.strip():
        return DEFAULT_LANGUAGE
    try:
        detected = detect(text)
    except Exception:
        return DEFAULT_LANGUAGE
    return detected if detected in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
