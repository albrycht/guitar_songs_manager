from __future__ import annotations

import json
import re
from typing import List, Optional

from ..logic.chords import SyllableSpan, apply_structure, get_syllables
from ..logic.language import detect_language
from ..schemas import ChordEntry, LineContent

_INLINE_CHORD_RE = re.compile(r"\{([^}]+)\}")


def extract_inline_chords(
    lyrics: str, language: str
) -> tuple[str, list[dict[int, str]]]:
    cleaned_lines, chords_per_line = _extract_inline_chords_lines(lyrics, language)
    return "\n".join(cleaned_lines), chords_per_line


def _extract_inline_chords_lines(
    lyrics: str, language: str
) -> tuple[list[str], list[dict[int, str]]]:
    lines = lyrics.splitlines()
    cleaned_lines: list[str] = []
    chords_per_line: list[dict[int, str]] = []

    for line in lines:
        cleaned_line, chords = _extract_inline_chords_from_line(line, language)
        cleaned_lines.append(cleaned_line)
        chords_per_line.append(chords)

    return cleaned_lines, chords_per_line


def _extract_inline_chords_from_line(
    line: str, language: str
) -> tuple[str, dict[int, str]]:
    if "{" not in line or "}" not in line:
        return line, {}

    tokens: list[tuple[int, str]] = []
    cleaned_parts: list[str] = []
    clean_length = 0
    last_index = 0

    for match in _INLINE_CHORD_RE.finditer(line):
        segment = line[last_index : match.start()]
        cleaned_parts.append(segment)
        clean_length += len(segment)

        chord_text = match.group(1).strip()
        if chord_text:
            tokens.append((clean_length, chord_text))

        last_index = match.end()

    tail = line[last_index:]
    cleaned_parts.append(tail)
    clean_length += len(tail)
    cleaned_line = "".join(cleaned_parts)

    if not tokens:
        return cleaned_line, {}

    syllables = get_syllables(cleaned_line, language)
    chords: dict[int, str] = {}
    for clean_index, chord_text in tokens:
        char_index = _resolve_inline_chord_index(clean_index, cleaned_line, syllables)
        chords[char_index] = chord_text

    return cleaned_line, chords


def _resolve_inline_chord_index(
    clean_index: int,
    text: str,
    syllables: list[SyllableSpan],
) -> int:
    if clean_index >= len(text):
        return len(text)

    for syllable in syllables:
        if syllable.start <= clean_index < syllable.end:
            return syllable.start

    for syllable in syllables:
        if syllable.start >= clean_index:
            return syllable.start

    return len(text)


def build_content_from_lyrics(
    lyrics: str,
    existing_content: Optional[List[LineContent]],
    language: Optional[str] = None,
) -> List[LineContent]:
    normalized_language = language or detect_language(lyrics)
    lines, inline_chords = _extract_inline_chords_lines(lyrics, normalized_language)
    content: List[LineContent] = []
    for index, text in enumerate(lines):
        chords: dict[int, ChordEntry] = {}
        if existing_content and index < len(existing_content):
            previous = existing_content[index]
            if previous.text == text:
                chords = dict(previous.chords)
        if index < len(inline_chords):
            for chord_index, chord_text in inline_chords[index].items():
                chords[chord_index] = ChordEntry(text=chord_text, type="manual")
        content.append(LineContent(text=text, chords=chords, section=None))
    return apply_structure(content)


def prepare_lyrics(
    title: str,
    lyrics: str,
    existing_content: Optional[List[LineContent]],
    language: Optional[str],
) -> tuple[str, List[LineContent], str]:
    detected_language = language or detect_language(lyrics)
    content = build_content_from_lyrics(lyrics, existing_content, detected_language)
    return title, content, detected_language


def serialize_content(lines: List[LineContent]) -> str:
    payload = []
    for line in lines:
        chords = {
            str(index): {"text": chord.text, "type": chord.type}
            for index, chord in line.chords.items()
        }
        payload.append(
            {
                "text": line.text,
                "section": line.section,
                "chords": chords,
            }
        )
    return json.dumps(payload, ensure_ascii=False)


def deserialize_content(content_json: str) -> List[LineContent]:
    raw = json.loads(content_json)
    if not isinstance(raw, list):
        raise ValueError("content_json must be a list")
    return [LineContent.model_validate(item) for item in raw]
