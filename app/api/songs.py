from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from ..schemas import (
    ChordsUpdateRequest,
    LyricsUpdateRequest,
    SongCreateRequest,
    SongDetail,
    SongSummary,
)
from ..services import songs as song_service

router = APIRouter(prefix="/api", tags=["songs"])


@router.get("/songs", response_model=list[SongSummary])
def list_songs() -> list[SongSummary]:
    return song_service.list_songs()


@router.get("/songs/{song_id}", response_model=SongDetail)
def show_song(song_id: int, expand_choruses: bool = False) -> SongDetail:
    song = song_service.get_song(song_id, expand_choruses=expand_choruses)
    if song is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Song not found"
        )
    return song


@router.post("/songs", response_model=SongDetail, status_code=status.HTTP_201_CREATED)
def create_song(payload: SongCreateRequest) -> SongDetail:
    return song_service.create_song(payload.title, payload.content)


@router.put("/songs/{song_id}/lyrics", response_model=SongDetail)
def update_lyrics(song_id: int, payload: LyricsUpdateRequest) -> SongDetail:
    updated = song_service.update_song_lyrics(
        song_id, payload.title, payload.lyrics, payload.existing_content
    )
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Song not found"
        )
    return updated


@router.put("/songs/{song_id}/chords", response_model=SongDetail)
def update_chords(song_id: int, payload: ChordsUpdateRequest) -> SongDetail:
    updated = song_service.update_song_chords(song_id, payload.title, payload.content)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Song not found"
        )
    return updated
