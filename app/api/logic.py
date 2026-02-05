from __future__ import annotations

from fastapi import APIRouter

from ..logic.chords import propagate_chords
from ..schemas import (
    ChordPreviewRequest,
    ChordPreviewResponse,
    LyricsPrepareRequest,
    LyricsPrepareResponse,
)
from ..services.content import prepare_lyrics

router = APIRouter(prefix="/api", tags=["logic"])


@router.post("/lyrics/prepare", response_model=LyricsPrepareResponse)
def prepare_lyrics_endpoint(payload: LyricsPrepareRequest) -> LyricsPrepareResponse:
    title, content, language = prepare_lyrics(
        payload.title, payload.lyrics, payload.existing_content, payload.language
    )
    return LyricsPrepareResponse(title=title, content=content, language=language)


@router.post("/chords/preview", response_model=ChordPreviewResponse)
def preview_chords(payload: ChordPreviewRequest) -> ChordPreviewResponse:
    updated = propagate_chords(
        payload.content,
        payload.line_index,
        payload.char_index,
        payload.chord,
        payload.language,
    )
    return ChordPreviewResponse(content=updated)
