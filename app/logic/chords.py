from __future__ import annotations

from dataclasses import dataclass
import re
from typing import List, Literal, Optional, Tuple

import pyphen

from ..schemas import ChordEntry, LineContent
from ..settings import DEFAULT_LANGUAGE, LANGUAGE_TO_PYPHEN

_WORD_PATTERN = r"[^\W\d_]+"
_POLISH_VOWELS = set("aeiouyąęó")
_VERSE_START_RE = re.compile(r"^\s*\d+\s*\.?\s+")
_CHORUS_START_RE = re.compile(r"^\s*(ref\s?[.:]|chorus\s*[:.])", re.IGNORECASE)


def _is_chorus_marker_only(text: str) -> bool:
    match = _CHORUS_START_RE.match(text)
    if match is None:
        return False
    remainder = text[match.end() :]
    return remainder.strip() == ""


@dataclass(frozen=True)
class Block:
    start_line_index: int
    end_line_index: int
    lines: List[LineContent]
    content_str: str
    type: Literal["verse", "chorus"]


@dataclass(frozen=True)
class SyllableSpan:
    text: str
    start: int
    end: int


_HYPHENATORS: dict[str, pyphen.Pyphen] = {}


def _get_hyphenator(language: str) -> Optional[pyphen.Pyphen]:
    lang = LANGUAGE_TO_PYPHEN.get(language)
    if not lang:
        return None
    if lang not in _HYPHENATORS:
        _HYPHENATORS[lang] = pyphen.Pyphen(lang=lang)
    return _HYPHENATORS[lang]


def _normalize_language(language: Optional[str]) -> str:
    if language and language in LANGUAGE_TO_PYPHEN:
        return language
    return DEFAULT_LANGUAGE


def detect_structure(lines: List[LineContent]) -> List[Block]:
    blocks: List[Block] = []
    current_lines: List[LineContent] = []
    start_line_index = 0
    explicit_block_type: Optional[Literal["chorus"]] = None

    def flush_block(end_index: int) -> None:
        nonlocal current_lines, start_line_index, explicit_block_type
        if not current_lines:
            return
        content_str = "\n".join(line_item.text.strip() for line_item in current_lines)
        block_type: Literal["verse", "chorus"] = (
            "chorus" if explicit_block_type == "chorus" else "verse"
        )
        blocks.append(
            Block(
                start_line_index=start_line_index,
                end_line_index=end_index,
                lines=current_lines,
                content_str=content_str,
                type=block_type,
            )
        )
        current_lines = []
        explicit_block_type = None

    for index, line in enumerate(lines):
        text = line.text
        if text.strip() == "":
            flush_block(index - 1)
            start_line_index = index + 1
            continue

        is_chorus_start = _CHORUS_START_RE.match(text) is not None
        is_verse_start = _VERSE_START_RE.match(text) is not None

        if (is_chorus_start or is_verse_start) and current_lines:
            flush_block(index - 1)
            start_line_index = index

        if not current_lines:
            if is_chorus_start:
                explicit_block_type = "chorus"
            else:
                explicit_block_type = None

        current_lines.append(line)

    if current_lines:
        flush_block(len(lines) - 1)

    content_counts: dict[str, int] = {}
    for block in blocks:
        content_counts[block.content_str] = content_counts.get(block.content_str, 0) + 1

    final_blocks: List[Block] = []
    for block in blocks:
        if block.type == "chorus":
            block_type: Literal["verse", "chorus"] = "chorus"
        else:
            block_type = "chorus" if content_counts[block.content_str] > 1 else "verse"
        final_blocks.append(
            Block(
                start_line_index=block.start_line_index,
                end_line_index=block.end_line_index,
                lines=block.lines,
                content_str=block.content_str,
                type=block_type,
            )
        )
    return final_blocks


def apply_structure(lines: List[LineContent]) -> List[LineContent]:
    updated = [line.model_copy(deep=True) for line in lines]
    blocks = detect_structure(updated)
    for block in blocks:
        for line_index in range(block.start_line_index, block.end_line_index + 1):
            if 0 <= line_index < len(updated):
                updated[line_index].section = block.type
    return updated


def expand_chorus_references(lines: List[LineContent]) -> List[LineContent]:
    if not lines:
        return []

    structured = apply_structure(lines)
    blocks = detect_structure(structured)
    template_lines: Optional[List[LineContent]] = None

    for block in blocks:
        if block.type != "chorus":
            continue
        non_marker_lines = [
            line for line in block.lines if not _is_chorus_marker_only(line.text)
        ]
        if non_marker_lines:
            template_lines = [line.model_copy(deep=True) for line in non_marker_lines]
            break

    if not template_lines:
        return structured

    expanded: List[LineContent] = []
    current_index = 0

    for block in blocks:
        while current_index < block.start_line_index:
            expanded.append(structured[current_index].model_copy(deep=True))
            current_index += 1

        if block.type != "chorus":
            for idx in range(block.start_line_index, block.end_line_index + 1):
                expanded.append(structured[idx].model_copy(deep=True))
            current_index = block.end_line_index + 1
            continue

        block_lines = [
            structured[idx]
            for idx in range(block.start_line_index, block.end_line_index + 1)
        ]
        non_marker_lines = [
            line for line in block_lines if not _is_chorus_marker_only(line.text)
        ]

        if non_marker_lines:
            for line in non_marker_lines:
                line_copy = line.model_copy(deep=True)
                line_copy.section = "chorus"
                expanded.append(line_copy)
        else:
            for line in template_lines:
                line_copy = line.model_copy(deep=True)
                line_copy.section = "chorus"
                expanded.append(line_copy)

        current_index = block.end_line_index + 1

    while current_index < len(structured):
        expanded.append(structured[current_index].model_copy(deep=True))
        current_index += 1

    return expanded


def transform_for_syllables(text: str) -> Tuple[str, List[int]]:
    word_regex = re.compile(_WORD_PATTERN, flags=re.UNICODE)
    matches = list(word_regex.finditer(text))
    if not matches:
        return text, list(range(len(text)))

    remove_indices: set[int] = set()
    for index, match in enumerate(matches[:-1]):
        word = match.group(0)
        if len(word) != 1:
            continue
        if word.lower() in _POLISH_VOWELS:
            continue
        gap_start = match.end()
        next_start = matches[index + 1].start()
        gap = text[gap_start:next_start]
        if gap and gap.isspace():
            remove_indices.update(range(gap_start, next_start))

    if not remove_indices:
        return text, list(range(len(text)))

    transformed_chars: List[str] = []
    index_map: List[int] = []
    for idx, char in enumerate(text):
        if idx in remove_indices:
            continue
        transformed_chars.append(char)
        index_map.append(idx)
    return "".join(transformed_chars), index_map


def get_syllables(text: str, language: Optional[str]) -> List[SyllableSpan]:
    import re

    syllables: List[SyllableSpan] = []
    transformed_text, index_map = transform_for_syllables(text)
    word_regex = re.compile(_WORD_PATTERN, flags=re.UNICODE)
    hyphenator = _get_hyphenator(_normalize_language(language))

    for match in word_regex.finditer(transformed_text):
        word = match.group(0)
        word_start = match.start()
        if hyphenator is None:
            parts = [word]
        else:
            parts = hyphenator.inserted(word).split("-")

        current_offset = 0
        for part in parts:
            part_start = word_start + current_offset
            part_end = part_start + len(part)
            original_start = index_map[part_start]
            original_end = index_map[part_end - 1] + 1
            syllables.append(
                SyllableSpan(
                    text=part,
                    start=original_start,
                    end=original_end,
                )
            )
            current_offset += len(part)
    return syllables


def get_syllable_info(
    text: str, char_index: int, language: Optional[str]
) -> Tuple[int, int]:
    syllables = get_syllables(text, language)
    for index, syllable in enumerate(syllables):
        if syllable.start <= char_index < syllable.end:
            return index, char_index - syllable.start
    return -1, 0


def get_char_index_for_syllable(
    text: str, syllable_index: int, language: Optional[str]
) -> int:
    syllables = get_syllables(text, language)
    if syllable_index < 0:
        return -1
    if syllable_index == len(syllables):
        return len(text)
    if syllable_index > len(syllables) - 1:
        return -1
    return syllables[syllable_index].start


def propagate_chords(
    lines: List[LineContent],
    changed_line_index: int,
    changed_char_index: int,
    new_chord_value: Optional[str],
    language: Optional[str],
) -> List[LineContent]:
    if not lines:
        return lines
    if changed_line_index < 0 or changed_line_index >= len(lines):
        return lines

    normalized_language = _normalize_language(language)
    updated = [line.model_copy(deep=True) for line in lines]
    blocks = detect_structure(updated)

    source_block = next(
        (
            block
            for block in blocks
            if block.start_line_index <= changed_line_index <= block.end_line_index
        ),
        None,
    )
    if source_block is None:
        return updated

    same_type_blocks = [block for block in blocks if block.type == source_block.type]
    if not same_type_blocks or same_type_blocks[0] != source_block:
        return updated

    relative_line_index = changed_line_index - source_block.start_line_index
    source_line_text = updated[changed_line_index].text
    is_eol_chord = changed_char_index == len(source_line_text)
    if is_eol_chord:
        syllable_index = len(get_syllables(source_line_text, normalized_language))
    else:
        syllable_index, _ = get_syllable_info(
            source_line_text, changed_char_index, normalized_language
        )
        if syllable_index == -1:
            return updated

    for target_block in same_type_blocks[1:]:
        if relative_line_index >= len(target_block.lines):
            continue
        target_abs_line_index = target_block.start_line_index + relative_line_index
        if target_abs_line_index < 0 or target_abs_line_index >= len(updated):
            continue
        target_line = updated[target_abs_line_index]
        target_char_index = get_char_index_for_syllable(
            target_line.text, syllable_index, normalized_language
        )
        if target_char_index == -1:
            continue
        if is_eol_chord:
            if target_char_index > len(target_line.text):
                continue
        else:
            if target_char_index >= len(target_line.text):
                continue

        chords = dict(target_line.chords)
        if new_chord_value:
            chords[target_char_index] = ChordEntry(text=new_chord_value, type="auto")
        else:
            existing = chords.get(target_char_index)
            if existing and existing.type == "auto":
                del chords[target_char_index]
        target_line.chords = chords

    return updated
