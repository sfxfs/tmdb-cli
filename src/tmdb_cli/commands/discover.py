"""discover subcommand: advanced movie filtering."""

from __future__ import annotations

from typing import Any

import typer

from ..client import TMDbClient
from ..config import get_language
from ..models import DiscoverResponse
from ..utils import display_json, display_table

discover_app = typer.Typer(name="discover", help="Advanced movie filtering")


@discover_app.command(name="movie")
def discover_movie(
    ctx: typer.Context,
    genre: list[int] | None = typer.Option(None, "--genre", "-g", help="Genre ID (can be specified multiple times)"),
    year: int | None = typer.Option(None, "--year", "-y", help="Year"),
    vote_gte: float | None = typer.Option(None, "--vote-gte", help="Minimum vote average"),
    sort: str = typer.Option("popularity.desc", "--sort", "-s", help="Sort order"),
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    language: str | None = typer.Option(None, "--language", "-l", help="Response language"),
    fmt: str = typer.Option("table", "--format", "-f", help="Output format: table|json|csv"),
) -> None:
    """Discover movies using advanced filtering."""
    lang = language or get_language()
    params: dict[str, Any] = {
        "language": lang,
        "page": page,
        "sort_by": sort,
    }
    if genre:
        params["with_genres"] = ",".join(str(g) for g in genre)
    if year:
        params["primary_release_year"] = year
    if vote_gte is not None:
        params["vote_average.gte"] = vote_gte

    with TMDbClient() as c:
        data = c.get("/discover/movie", params=params)
    resp = DiscoverResponse(**data)
    if ctx.obj["json"]:
        display_json(resp)
        return

    if fmt == "json":
        display_json(resp)
    elif fmt == "csv":
        import csv
        import sys

        rows = [r.model_dump() for r in resp.results]
        if rows:
            w = csv.DictWriter(sys.stdout, fieldnames=rows[0].keys())
            w.writeheader()
            w.writerows(rows)
    else:
        rows = [
            {
                "id": r.id,
                "title": r.title[:40],
                "release_date": str(r.release_date) if r.release_date else "",
                "vote": f"{r.vote_average:.1f}",
            }
            for r in resp.results
        ]
        display_table(
            rows,
            [("id", "ID"), ("title", "Title"), ("release_date", "Release Date"), ("vote", "Rating")],
            title=f"Results (Page {resp.page}/{resp.total_pages}, Total {resp.total_results})",
        )
