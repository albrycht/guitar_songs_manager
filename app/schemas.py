from __future__ import annotations

from typing import Dict, List, Literal, Optional, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator

ChordType = Literal["manual", "auto"]


class ChordEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    type: ChordType = "manual"


class LineContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    chords: Dict[int, ChordEntry] = Field(default_factory=dict)
    section: Optional[Literal["verse", "chorus"]] = None

    @field_validator("chords", mode="before")
    @classmethod
    def normalize_chords(cls, value: object) -> Dict[int, ChordEntry]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise TypeError("chords must be a dict")
        normalized: Dict[int, ChordEntry] = {}
        for key, raw in value.items():
            if isinstance(key, int):
                index = key
            elif isinstance(key, str):
                index = int(key)
            else:
                raise TypeError("chord indices must be int-compatible")
            if isinstance(raw, ChordEntry):
                normalized[index] = raw
            elif isinstance(raw, str):
                normalized[index] = ChordEntry(text=raw.strip(), type="manual")
            elif isinstance(raw, dict):
                raw_dict = cast(dict[str, object], raw)
                text_value = raw_dict.get("text")
                chord_type_value = raw_dict.get("type", "manual")
                text = str(text_value or "").strip()
                chord_type: ChordType = "manual"
                if chord_type_value == "auto":
                    chord_type = "auto"
                elif chord_type_value == "manual":
                    chord_type = "manual"
                normalized[index] = ChordEntry(text=text, type=chord_type)
            else:
                raise TypeError("invalid chord value")
        return normalized


class SongSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    title: str
    updated_at: str


class SongDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    title: str
    content: List[LineContent]
    created_at: str
    updated_at: str


class LyricsPrepareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    lyrics: str
    existing_content: Optional[List[LineContent]] = None
    language: Optional[str] = None


class LyricsPrepareResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    content: List[LineContent]
    language: str


class ChordPreviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: List[LineContent]
    line_index: int
    char_index: int
    chord: Optional[str] = None
    language: Optional[str] = None


class ChordPreviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: List[LineContent]


class SongCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    content: List[LineContent]


class LyricsUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    lyrics: str
    existing_content: Optional[List[LineContent]] = None
    language: Optional[str] = None


class ChordsUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    content: List[LineContent]
