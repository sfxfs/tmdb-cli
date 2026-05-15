"""TMDB API Key Configuration: storage, reading, and validation.

Configuration stored under `~/.config/tmdb-cli/config.toml` (XDG Base Directory):

    [api]
    bearer_token = "eyJ..."

    [preferences]
    language = "zh-CN"
    fallback_language = "en"
"""

from __future__ import annotations

import json as _json
import tomllib
from pathlib import Path
from typing import Any, cast

import typer

CONFIG_DIR = Path.home() / ".config" / "tmdb-cli"
CONFIG_FILE = CONFIG_DIR / "config.toml"


def _ensure_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict[str, Any]:
    """Load full configuration, return empty dict if file does not exist."""
    if not CONFIG_FILE.exists():
        return {}
    return tomllib.loads(CONFIG_FILE.read_text(encoding="utf-8"))


def save_config(data: dict[str, Any]) -> None:
    """Overwrite configuration to disk."""
    _ensure_dir()
    lines = _toml_dumps(data)
    CONFIG_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def get_token() -> str | None:
    """Return stored Bearer Token, or None if not set."""
    cfg = load_config()
    return cast(str | None, cfg.get("api", {}).get("bearer_token"))


def get_language() -> str:
    """Return preferred language, defaults to zh-CN."""
    cfg = load_config()
    return cast(str, cfg.get("preferences", {}).get("language", "zh-CN"))


def get_fallback_language() -> str | None:
    """Return fallback image/download language, or None if not set."""
    cfg = load_config()
    return cast(str | None, cfg.get("preferences", {}).get("fallback_language"))


# ---- Minimal TOML serialization (avoids tomli_w dependency) ----


def _toml_dumps(data: dict[str, Any], *, _prefix: str = "") -> list[str]:
    lines: list[str] = []
    for key, val in data.items():
        full_key = f"{_prefix}.{key}" if _prefix else key
        if isinstance(val, dict):
            if val:
                lines.append(f"[{full_key}]")
                for k, v in val.items():
                    lines.append(f"{k} = {_toml_value(v)}")
            else:
                lines.append(f"[{full_key}]")
        else:
            if not _prefix:
                lines.append(f"{key} = {_toml_value(val)}")
            else:
                lines.append(f"{key} = {_toml_value(val)}")
    return lines


def _toml_value(v: str | int | float | bool) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, str):
        return f'"{v}"'
    return str(v)


# ---- CLI subcommands ----


config_app = typer.Typer(name="config", help="Manage API key and preferences")
set_app = typer.Typer(name="set", help="Set configuration values")


@set_app.command(name="token")
def config_set_token(
    key: str = typer.Argument(..., help="TMDB API Read Access Token"),
) -> None:
    """Set the TMDB API Bearer Token."""
    cfg = load_config()
    cfg.setdefault("api", {})["bearer_token"] = key
    save_config(cfg)
    typer.echo(f"API Key saved to {CONFIG_FILE}")


@set_app.command(name="language")
def config_set_language(
    language: str = typer.Argument(..., help="Preferred metadata language (e.g. zh-CN, en)"),
    fallback: str | None = typer.Argument(None, help="Fallback language for images (e.g. en, null)"),
) -> None:
    """Set preferred language and optional fallback."""
    cfg = load_config()
    prefs = cfg.setdefault("preferences", {})
    prefs["language"] = language
    if fallback is not None:
        prefs["fallback_language"] = fallback
    elif "fallback_language" in prefs:
        del prefs["fallback_language"]
    save_config(cfg)
    msg = f"Language set to: {language}"
    if fallback:
        msg += f" (fallback: {fallback})"
    typer.echo(msg)


config_app.add_typer(set_app)


@config_app.command(name="show")
def config_show() -> None:
    """Show current configuration."""
    cfg = load_config()
    if not cfg:
        typer.echo("No settings configured.")
        return
    typer.echo(_json.dumps(cfg, ensure_ascii=False, indent=2))


@config_app.command(name="validate")
def config_validate() -> None:
    """Validate the stored API Key."""
    import httpx

    token = get_token()
    if not token:
        typer.echo("API Key is not set. Run `tmdb config set token <KEY>` first", err=True)
        raise typer.Exit(1)

    try:
        r = httpx.get(
            "https://api.themoviedb.org/3/authentication",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        r.raise_for_status()
        typer.echo("API Key is valid")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            typer.echo("API Key is invalid (401 Unauthorized)", err=True)
        else:
            typer.echo(f"Request failed: {e}", err=True)
        raise typer.Exit(1)
    except httpx.RequestError as e:
        typer.echo(f"Network error: {e}", err=True)
        raise typer.Exit(1)
