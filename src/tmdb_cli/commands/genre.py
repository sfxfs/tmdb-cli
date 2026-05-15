"""genre subcommand: movie/TV genre list."""

from __future__ import annotations

import typer

from ..client import TMDbClient
from ..config import get_language
from ..models import GenreListResponse
from ..utils import display_json, display_table

genre_app = typer.Typer(name="genre", help="Genre list")


@genre_app.command(name="movie-list")
def genre_movie_list(
    ctx: typer.Context,
    language: str | None = typer.Option(None, "--language", "-l", help="Return language"),
) -> None:
    """List movie genres."""
    lang = language or get_language()
    with TMDbClient() as c:
        data = c.get("/genre/movie/list", params={"language": lang})
    resp = GenreListResponse(**data)

    if ctx.obj["json"]:
        display_json(resp)
        return

    rows = [{"id": g.id, "name": g.name} for g in resp.genres]
    display_table(rows, [("id", "ID"), ("name", "Genre name")], title="Movie genres")


@genre_app.command(name="tv-list")
def genre_tv_list(
    ctx: typer.Context,
    language: str | None = typer.Option(None, "--language", "-l", help="Return language"),
) -> None:
    """List TV genres."""
    lang = language or get_language()
    with TMDbClient() as c:
        data = c.get("/genre/tv/list", params={"language": lang})
    resp = GenreListResponse(**data)

    if ctx.obj["json"]:
        display_json(resp)
        return

    rows = [{"id": g.id, "name": g.name} for g in resp.genres]
    display_table(rows, [("id", "ID"), ("name", "Genre name")], title="TV genres")
