"""search sub-command: movie and TV series search."""

from __future__ import annotations

from typing import Any

import typer

from ..client import TMDbClient
from ..config import get_language
from ..models import MovieSearchResponse, TVSearchResponse
from ..utils import display_json, display_table

search_app = typer.Typer(name="search", help="Search movies or TV series")


def _resolve_lang(language: str | None) -> str:
    return language or get_language()


@search_app.command(name="movie")
def search_movie(
    ctx: typer.Context,
    query: str = typer.Argument(..., help="Search keyword"),
    year: int | None = typer.Option(None, "--year", "-y", help="Year filter"),
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    language: str | None = typer.Option(
        None,
        "--language",
        "-l",
        help="Response language (default: configured preferred language)",
    ),
    fmt: str = typer.Option("table", "--format", "-f", help="Output format: table|json|csv"),
    output: str | None = typer.Option(None, "--output", "-o", help="Save to file (.json)"),
) -> None:
    """Search movies by title."""
    lang = _resolve_lang(language)
    params: dict[str, Any] = {"query": query, "language": lang, "page": page}
    if year:
        params["year"] = year

    with TMDbClient() as c:
        data = c.get("/search/movie", params=params)
    resp = MovieSearchResponse(**data)

    if ctx.obj["json"]:
        display_json(resp)
        return
    if fmt == "json":
        display_json(resp)
    elif fmt == "csv":
        _emit_csv([r.model_dump() for r in resp.results])
    else:
        rows = [
            {
                "id": r.id,
                "title": r.title[:40],
                "original_title": r.original_title[:30],
                "release_date": str(r.release_date) if r.release_date else "",
                "vote": f"{r.vote_average:.1f}",
            }
            for r in resp.results
        ]
        display_table(
            rows,
            [
                ("id", "ID"),
                ("title", "Title"),
                ("original_title", "Original Title"),
                ("release_date", "Release Date"),
                ("vote", "Rating"),
            ],
            title=f"Search '{query}' ({resp.total_results} results, page {resp.page}/{resp.total_pages})",
        )

    if output:
        if fmt != "json":
            typer.echo(
                "--output only takes effect with --format json; will save JSON",
                err=True,
            )
        import pathlib

        pathlib.Path(output).write_text(resp.model_dump_json(indent=2), encoding="utf-8")
        typer.echo(f"Written to {output}")


@search_app.command(name="tv")
def search_tv(
    ctx: typer.Context,
    query: str = typer.Argument(..., help="Search keyword"),
    first_air_year: int | None = typer.Option(None, "--first-air-year", "-y", help="First air year filter"),
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    language: str | None = typer.Option(None, "--language", "-l", help="Response language"),
    fmt: str = typer.Option("table", "--format", "-f", help="Output format: table|json|csv"),
) -> None:
    """Search TV series by name."""
    lang = _resolve_lang(language)
    params: dict[str, Any] = {"query": query, "language": lang, "page": page}
    if first_air_year:
        params["first_air_date_year"] = first_air_year

    with TMDbClient() as c:
        data = c.get("/search/tv", params=params)
    resp = TVSearchResponse(**data)

    if ctx.obj["json"]:
        display_json(resp)
        return
    if fmt == "json":
        display_json(resp)
    elif fmt == "csv":
        _emit_csv([r.model_dump() for r in resp.results])
    else:
        rows = [
            {
                "id": r.id,
                "name": r.name[:40],
                "original_name": r.original_name[:30],
                "first_air_date": str(r.first_air_date) if r.first_air_date else "",
                "vote": f"{r.vote_average:.1f}",
            }
            for r in resp.results
        ]
        display_table(
            rows,
            [
                ("id", "ID"),
                ("name", "Name"),
                ("original_name", "Original Name"),
                ("first_air_date", "First Air Date"),
                ("vote", "Rating"),
            ],
            title=f"Search '{query}' ({resp.total_results} results, page {resp.page}/{resp.total_pages})",
        )


def _emit_csv(rows: list[dict[str, Any]]) -> None:
    import csv
    import sys

    if not rows:
        return
    w = csv.DictWriter(sys.stdout, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)
