"""Trending subcommand: popular/trending movies."""

from __future__ import annotations

import typer

from ..client import TMDbClient
from ..config import get_language
from ..models import TrendingResponse
from ..utils import display_json, display_table

trending_app = typer.Typer(name="trending", help="Popular/trending movies")


@trending_app.command(name="movie")
def trending_movie(
    ctx: typer.Context,
    window: str = typer.Option("day", "--window", "-w", help="Time window: day|week"),
    language: str | None = typer.Option(None, "--language", "-l", help="Response language"),
    fmt: str = typer.Option("table", "--format", "-f", help="Output format: table|json"),
) -> None:
    """View popular trending movies."""
    lang = language or get_language()
    with TMDbClient() as c:
        data = c.get(f"/trending/movie/{window}", params={"language": lang})
    resp = TrendingResponse(**data)
    if ctx.obj["json"]:
        display_json(resp)
        return

    if fmt == "json":
        display_json(resp)
        return

    rows = [
        {
            "id": r.id,
            "title": r.title[:40],
            "release_date": str(r.release_date) if r.release_date else "",
            "vote": f"{r.vote_average:.1f}",
            "popularity": f"{r.popularity:.0f}",
        }
        for r in resp.results
    ]
    display_table(
        rows,
        [
            ("id", "ID"),
            ("title", "Title"),
            ("release_date", "Release Date"),
            ("vote", "Rating"),
            ("popularity", "Popularity"),
        ],
        title=f"{window.title()} Trending ({len(rows)} movies)",
    )
