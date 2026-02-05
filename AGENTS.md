Guitar Songs Manager

Overview
- FastAPI app that serves a single-page UI for storing songs with lyrics and chords.
- SQLite is the storage backend; song content is stored as JSON.
- UI remains HTML/CSS/JS, while all structure detection and chord propagation logic lives in Python.

Core features
- Create songs from title + lyrics.
- Edit lyrics and chords after save.
- View list of songs and song details.
- Auto-detect verses/choruses and highlight choruses.
- Propagate chords across verses/choruses based on line and syllable positions.

Architecture
- FastAPI serves:
  - Static assets (HTML/CSS/JS) from `app/static/`
  - JSON API for song CRUD and logic previews
- Logic is in pure Python modules for direct pytest usage.
- SQLite database is initialized on startup.

Project structure
- `app/`
  - `main.py` FastAPI entrypoint, static mounting
  - `api/` HTTP endpoints
  - `logic/` pure functions for structure detection and chord propagation
  - `services/` orchestration for content parsing and storage
  - `schemas.py` Pydantic models for requests/responses
  - `db.py` SQLite access
  - `static/` UI files
- `tests/` pytest unit tests for logic and API
- `features/` implementation plans for upcoming work
- `pyproject.toml` project metadata and tooling

Tooling
- Use `uv` for dependency management and running tools.
- Type checking uses `ty`.
- Formatting and linting uses `ruff`.

Features catalog
- Each feature plan is a separate file in `features/`.
- File names are sequential and start with 4 digits, for example `0001-python-rewrite.txt`.
- New features must increment the number and include a clear plan and test expectations.

Required checks after implementing any feature
Run all commands and fix any errors:
- `uv run ruff check`
- `uv run ruff format`
- `uv run ty check`
- `uv run pytest`
