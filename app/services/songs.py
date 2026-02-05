from __future__ import annotations

from typing import List, Optional

from .. import db
from ..logic.chords import apply_structure, expand_chorus_references
from ..schemas import LineContent, SongDetail, SongSummary
from .content import build_content_from_lyrics, deserialize_content, serialize_content


def list_songs() -> List[SongSummary]:
    rows = db.fetch_songs()
    return [
        SongSummary(id=row.id, title=row.title, updated_at=row.updated_at)
        for row in rows
    ]


def get_song(song_id: int, expand_choruses: bool = False) -> Optional[SongDetail]:
    row = db.get_song(song_id)
    if row is None:
        return None
    content = deserialize_content(row.content_json)
    if expand_choruses:
        structured = expand_chorus_references(content)
    else:
        structured = apply_structure(content)
    return SongDetail(
        id=row.id,
        title=row.title,
        content=structured,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def create_song(title: str, content: List[LineContent]) -> SongDetail:
    structured = apply_structure(content)
    content_json = serialize_content(structured)
    row = db.create_song(title, content_json)
    return SongDetail(
        id=row.id,
        title=row.title,
        content=structured,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def update_song_lyrics(
    song_id: int,
    title: str,
    lyrics: str,
    existing_content: Optional[List[LineContent]],
) -> Optional[SongDetail]:
    content = build_content_from_lyrics(lyrics, existing_content)
    content_json = serialize_content(content)
    row = db.update_song(song_id, title, content_json)
    if row is None:
        return None
    return SongDetail(
        id=row.id,
        title=row.title,
        content=content,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def update_song_chords(
    song_id: int, title: str, content: List[LineContent]
) -> Optional[SongDetail]:
    structured = apply_structure(content)
    content_json = serialize_content(structured)
    row = db.update_song(song_id, title, content_json)
    if row is None:
        return None
    return SongDetail(
        id=row.id,
        title=row.title,
        content=structured,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
