# Repository Guidelines

## Project Overview

`tmdb-cli` is a Python CLI tool for scraping movie and TV series metadata from the TMDB API v3. It provides search, discovery, detail lookup, image download, media library organization, and NFO/JSON/CSV export. Built with `typer`, `httpx`, `pydantic` v2, and `rich`.

## Architecture & Data Flow

```
CLI (main.py: app)
 ├── config  ── config.py (XDG toml, no API)
 ├── search  ── commands/search.py
 ├── movie   ── commands/movie.py
 ├── discover── commands/discover.py
 ├── trending── commands/trending.py
 ├── genre   ── commands/genre.py
 ├── images  ── commands/images.py
 ├── organize── organize.py
 └── export  ── export.py
              │
              ▼
        TMDbClient (client.py)
         ─ httpx sync HTTP, context manager, 429 retry
              │
              ▼
         TMDB API v3 (api.themoviedb.org/3)
         ─ Bearer token auth from ~/.config/tmdb-cli/config.toml
              │
              ▼
        Pydantic models (models.py)
         ─ OptionalDate validator handles empty-string dates
              │
              ▼
        Rich output (utils.py)
         ─ display_table() / display_json()
```

**Flow per command**: parse args → resolve language (`_resolve_lang`) → open `TMDbClient()` context → GET endpoint with `params: dict[str, Any]` → deserialize into Pydantic model → check `ctx.obj["json"]` → display table or JSON.

## Key Directories

| Path | Purpose |
|---|---|
| `src/tmdb_cli/` | Package root — core modules live here |
| `src/tmdb_cli/commands/` | Typer sub-apps (one file per command group) |
| `tests/` | pytest tests, no conftest.py |
| `.venv/` | uv-managed CPython 3.12 venv |

## Development Commands

```sh
uv sync              # install all deps
uv sync --extra dev  # install dev deps too (pytest, mypy, ruff)
uv run tmdb --help   # run CLI
uv run pytest        # run tests (25 tests, ~0.1s)
uv run ruff check .  # lint
uv run mypy src/     # type check (strict mode)
```

**Entry point**: `[project.scripts] tmdb = "tmdb_cli.main:app"` in `pyproject.toml`.

## Code Conventions & Common Patterns

### Typer Command Pattern (used in all commands)

Every command that produces table output follows this exact pattern:

```python
@xxx_app.command(name="yyy")
def yyy(
    ctx: typer.Context,                                    # always first param
    arg: int = typer.Argument(..., help="..."),            # required positional
    lang: str | None = typer.Option(None, "--language", "-l", help="..."),
    fmt: str = typer.Option("table", "--format", "-f", help="Output format: table|json|csv"),
) -> None:
    lang = language or get_language()
    with TMDbClient() as c:
        data = c.get("/endpoint", params={"language": lang, ...})
    resp = SomeModel(**data)

    if ctx.obj["json"]:        # global --json overrides --format
        display_json(resp)
        return

    if fmt == "json":
        display_json(resp)
    elif fmt == "csv":
        _emit_csv(...)
    else:
        rows = [{...}, ...]
        display_table(rows, [("key", "Header"), ...], title="...")
```

### API Client

- `TMDbClient(token)` is a **synchronous** `httpx.Client` wrapper with context manager support
- Must be used via `with TMDbClient() as c:` — never instantiate and leave open
- Reads token from `get_token()` (config module) when no explicit token given
- `c.get(path, params=...)` returns `dict[str, Any]` — no Pydantic validation at this layer
- Handles 429 with up to 3 retries via `Retry-After` header

### Config Access

- Config path: `~/.config/tmdb-cli/config.toml` (XDG spec)
- `get_token()` → `str | None`
- `get_language()` → `str` (defaults to `"zh-CN"`)
- Custom `_toml_dumps()` / `_toml_value()` avoids `tomli_w` dependency
- Reads use `tomllib` (stdlib, Python 3.11+)

### Data Models

- Use Pydantic v2 with `model_config = ConfigDict(extra="allow")` to tolerate unknown API fields
- Date fields use `OptionalDate` type alias: `Annotated[date | None, BeforeValidator(_parse_optional_date)]` — converts empty strings (`""`) to `None`
- All models defined in `models.py` — movie, TV, credits, images, genre, discover/trending responses

### Output Formatting

- `display_table(rows, columns, title)` — `rows: list[dict]`, `columns: list[tuple[key, header]]`
- `display_json(data, indent=2)` — handles `BaseModel`, `list[BaseModel]`, `dict`
- `console` is a module-level `rich.console.Console()` singleton in `utils.py`

### NFO Generation

- `export.py` and `organize.py` both contain NFO builders — not shared
- `_esc(s)` in `export.py` handles XML entity escaping, imported by `organize.py`
- `sanitize_filename()` in `utils.py` replaces `< > : " / \ | ? *` with spaces

### Naming

- Module files: lowercase, underscore-separated
- Typer app variables: `xxx_app = typer.Typer(name="xxx", ...)`
- Command functions: `verb_noun` or `noun_verb` style (e.g., `search_movie`, `organize_tv`, `genre_movie_list`)
- Test classes: `TestXxx` grouped by subsystem

## Important Files

| File | Role |
|---|---|
| `src/tmdb_cli/main.py` | Entry point, registers 9 sub-apps, `--json` callback |
| `src/tmdb_cli/client.py` | `TMDbClient` (HTTP), `TMDbError`, `get_image_url()` |
| `src/tmdb_cli/models.py` | All Pydantic models, `OptionalDate` validator |
| `src/tmdb_cli/config.py` | XDG config, `config_app` typer |
| `src/tmdb_cli/organize.py` | `organize` command (movie/tv), image download + NFO |
| `src/tmdb_cli/export.py` | `export` command (nfo/json/csv), `_esc()` XML helper |
| `src/tmdb_cli/utils.py` | `display_table()`, `display_json()`, `sanitize_filename()` |
| `pyproject.toml` | Dependencies, scripts entry, ruff/mypy config |
| `tests/test_client.py` | HTTP client tests with `pytest-httpx` |
| `tests/test_models.py` | Pydantic date-parsing edge cases |
| `tests/test_config.py` | Config I/O and TOML serialization tests |

## Runtime/Tooling Preferences

- **Package manager**: `uv` (do NOT use `pip` or `poetry`)
- **Runtime**: Python 3.11+ (venv is CPython 3.12)
- **Linter**: `ruff` — line-length 120, selects E/F/I/W, target py311
- **Type checker**: `mypy --strict` — python_version 3.11
- **Test runner**: `pytest` with `pytest-httpx` for HTTP mocking
- **CI/formatting**: `ruff format` for formatting, `ruff check --fix` for auto-fixes

## Testing & QA

- 25 tests across 3 files — client (7), config (10), models (8)
- **HTTP mocking**: `pytest-httpx` `HTTPXMock` fixture — `httpx_mock.add_response(url=..., json=..., status_code=...)`
- **Config isolation**: `monkeypatch.setattr` on `CONFIG_DIR` / `CONFIG_FILE` constants
- **Date edge cases**: Direct construction with `type: ignore[arg-type]` to test empty-string → None coercion
- No CLI integration tests, no conftest.py, no shared fixtures across test files
- Run: `uv run pytest tests/ -v`
