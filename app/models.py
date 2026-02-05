from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SongRow:
    id: int
    title: str
    content_json: str
    created_at: str
    updated_at: str
