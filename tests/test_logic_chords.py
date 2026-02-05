from __future__ import annotations

from app.logic.chords import (
    apply_structure,
    detect_structure,
    expand_chorus_references,
    propagate_chords,
)
from app.schemas import ChordEntry, LineContent
from app.services.content import build_content_from_lyrics


def test_detect_structure_marks_repeated_blocks_as_chorus() -> None:
    lines = [
        LineContent(text="Verse line 1", chords={}),
        LineContent(text="Verse line 2", chords={}),
        LineContent(text="", chords={}),
        LineContent(text="Chorus line 1", chords={}),
        LineContent(text="Chorus line 2", chords={}),
        LineContent(text="", chords={}),
        LineContent(text="Verse line 3", chords={}),
        LineContent(text="Verse line 4", chords={}),
        LineContent(text="", chords={}),
        LineContent(text="Chorus line 1", chords={}),
        LineContent(text="Chorus line 2", chords={}),
    ]

    blocks = detect_structure(lines)

    assert len(blocks) == 4
    assert blocks[0].type == "verse"
    assert blocks[1].type == "chorus"
    assert blocks[2].type == "verse"
    assert blocks[3].type == "chorus"


def test_detect_structure_uses_markers() -> None:
    lines = [
        LineContent(text="1. First verse line", chords={}),
        LineContent(text="Second line", chords={}),
        LineContent(text="chorus: Loud line", chords={}),
        LineContent(text="More chorus", chords={}),
        LineContent(text="Ref.: Soft line", chords={}),
        LineContent(text="More ref", chords={}),
        LineContent(text="2. Second verse line", chords={}),
        LineContent(text="Outro", chords={}),
    ]

    blocks = detect_structure(lines)

    assert len(blocks) == 4
    assert blocks[0].type == "verse"
    assert blocks[1].type == "chorus"
    assert blocks[2].type == "chorus"
    assert blocks[3].type == "verse"


def test_expand_chorus_references_replaces_placeholders() -> None:
    lines = [
        LineContent(text="Verse line 1", chords={}),
        LineContent(text="Verse line 2", chords={}),
        LineContent(text="", chords={}),
        LineContent(text="Ref.", chords={}),
        LineContent(text="Chorus line 1", chords={}),
        LineContent(text="Chorus line 2", chords={}),
        LineContent(text="", chords={}),
        LineContent(text="Verse line 3", chords={}),
        LineContent(text="", chords={}),
        LineContent(text="Ref.", chords={}),
        LineContent(text="", chords={}),
        LineContent(text="Verse line 4", chords={}),
    ]

    structured = apply_structure(lines)
    expanded = expand_chorus_references(structured)

    expanded_text = [line.text for line in expanded]
    assert expanded_text == [
        "Verse line 1",
        "Verse line 2",
        "",
        "Chorus line 1",
        "Chorus line 2",
        "",
        "Verse line 3",
        "",
        "Chorus line 1",
        "Chorus line 2",
        "",
        "Verse line 4",
    ]


def test_propagate_chords_applies_to_same_block_type() -> None:
    lines = [
        LineContent(text="Verse one", chords={}),
        LineContent(text="", chords={}),
        LineContent(text="Chorus", chords={}),
        LineContent(text="", chords={}),
        LineContent(text="Verse two", chords={}),
        LineContent(text="", chords={}),
        LineContent(text="Chorus", chords={}),
    ]

    lines[0].chords[0] = ChordEntry(text="G", type="manual")

    updated = propagate_chords(lines, 0, 0, "G", "en")

    assert updated[0].chords[0].text == "G"
    assert updated[4].chords[0].text == "G"
    assert 0 not in updated[2].chords
    assert 0 not in updated[6].chords


def test_propagate_chords_glues_single_letter_consonants() -> None:
    lines = [
        LineContent(text="W pierwszym swietle dnia", chords={}),
        LineContent(text="Świecie czeka cud", chords={}),
        LineContent(text="Przywitać nowy czas", chords={}),
        LineContent(text="", chords={}),
        LineContent(text="W drugim swietle dnia", chords={}),
        LineContent(text="Z wszystkimi znaki", chords={}),
        LineContent(text="W wielkiej ciszy trwac", chords={}),
    ]

    source_c_index = lines[1].text.index("cie")
    updated = propagate_chords(lines, 1, source_c_index, "C", "pl")

    target_c_line = updated[5]
    wszystkich_index = target_c_line.text.index("wszystkimi")
    expected_c_index = wszystkich_index + len("wszyst")
    assert expected_c_index in target_c_line.chords
    assert target_c_line.chords[expected_c_index].text == "C"

    source_g_index = updated[2].text.index("wi")
    updated = propagate_chords(updated, 2, source_g_index, "G", "pl")

    target_g_line = updated[6]
    wielkiej_index = target_g_line.text.index("wielkiej")
    expected_g_index = wielkiej_index + len("wiel")
    assert expected_g_index in target_g_line.chords
    assert target_g_line.chords[expected_g_index].text == "G"


def test_inline_chords_attach_to_syllable_starts() -> None:
    lyrics = "{G}W śród {D}nocnej ciszy"
    content = build_content_from_lyrics(lyrics, None, language="pl")

    assert content[0].text == "W śród nocnej ciszy"
    assert content[0].chords[0].text == "G"
    assert content[0].chords[7].text == "D"


def test_inline_chords_at_line_end_attach_to_eol() -> None:
    lyrics = "A witając zawołali{G}{D}\nNastępna linia"
    content = build_content_from_lyrics(lyrics, None, language="pl")

    assert content[0].text == "A witając zawołali"
    eol_index = len(content[0].text)
    assert content[0].chords[eol_index].text == "D"
    assert content[1].chords == {}
