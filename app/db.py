from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from typing import Optional

from .models import SongRow
from .settings import DB_PATH, DATA_DIR


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_songs() -> list[SongRow]:
    with closing(_get_connection()) as conn:
        rows = conn.execute(
            "SELECT id, title, content_json, created_at, updated_at FROM songs ORDER BY updated_at DESC"
        ).fetchall()
    return [
        SongRow(
            id=row["id"],
            title=row["title"],
            content_json=row["content_json"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        for row in rows
    ]


def get_song(song_id: int) -> Optional[SongRow]:
    with closing(_get_connection()) as conn:
        row = conn.execute(
            "SELECT id, title, content_json, created_at, updated_at FROM songs WHERE id = ?",
            (song_id,),
        ).fetchone()
    if row is None:
        return None
    return SongRow(
        id=row["id"],
        title=row["title"],
        content_json=row["content_json"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def create_song(title: str, content_json: str) -> SongRow:
    now = _utc_now()
    with closing(_get_connection()) as conn:
        cursor = conn.execute(
            """
            INSERT INTO songs (title, content_json, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (title, content_json, now, now),
        )
        conn.commit()
        song_id_value = cursor.lastrowid
        if song_id_value is None:
            raise RuntimeError("Failed to create song record")
        song_id = int(song_id_value)
    created = get_song(song_id)
    if created is None:
        raise RuntimeError("Failed to create song record")
    return created


def update_song(song_id: int, title: str, content_json: str) -> Optional[SongRow]:
    now = _utc_now()
    with closing(_get_connection()) as conn:
        cursor = conn.execute(
            """
            UPDATE songs
            SET title = ?, content_json = ?, updated_at = ?
            WHERE id = ?
            """,
            (title, content_json, now, song_id),
        )
        conn.commit()
        if cursor.rowcount == 0:
            return None
    return get_song(song_id)
