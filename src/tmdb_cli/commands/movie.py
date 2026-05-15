"""Movie subcommands: details, credits, images, similar, recommendations, keywords."""

from __future__ import annotations

from typing import Any

import typer

from ..client import TMDbClient
from ..config import get_language
from ..models import Credits, ImageCollection, MovieDetail, MovieSearchResponse
from ..utils import display_json, display_table

movie_app = typer.Typer(name="movie", help="Movie details")


def _resolve_lang(language: str | None) -> str:
    return language or get_language()


@movie_app.command(name="info")
def movie_info(
    ctx: typer.Context,
    movie_id: int = typer.Argument(..., help="TMDB movie ID"),
    language: str | None = typer.Option(None, "--language", "-l", help="Response language"),
    fmt: str = typer.Option("table", "--format", "-f", help="Output format: table|json"),
) -> None:
    """View full movie details."""
    lang = _resolve_lang(language)
    with TMDbClient() as c:
        data = c.get(f"/movie/{movie_id}", params={"language": lang})
    movie = MovieDetail(**data)

    if ctx.obj["json"]:
        display_json(movie)
        return

    if fmt == "json":
        display_json(movie)
        return

    display_table(
        [
            {
                "field": "Title",
                "value": movie.title,
            },
            {
                "field": "Original title",
                "value": movie.original_title,
            },
            {
                "field": "Release date",
                "value": str(movie.release_date) if movie.release_date else "",
            },
            {
                "field": "Runtime",
                "value": f"{movie.runtime} min" if movie.runtime else "",
            },
            {
                "field": "Rating",
                "value": f"{movie.vote_average:.1f} ({movie.vote_count} votes)",
            },
            {
                "field": "Status",
                "value": movie.status,
            },
            {
                "field": "Budget",
                "value": f"${movie.budget:,}" if movie.budget else "",
            },
            {
                "field": "Revenue",
                "value": f"${movie.revenue:,}" if movie.revenue else "",
            },
            {
                "field": "IMDB",
                "value": movie.imdb_id or "",
            },
            {
                "field": "Genres",
                "value": ", ".join(g.name for g in movie.genres),
            },
            {
                "field": "Tagline",
                "value": movie.tagline,
            },
            {
                "field": "Website",
                "value": movie.homepage,
            },
            {
                "field": "Overview",
                "value": movie.overview,
            },
        ],
        [("field", ""), ("value", "")],
        title=f"{movie.title}",
    )


@movie_app.command(name="credits")
def movie_credits(
    ctx: typer.Context,
    movie_id: int = typer.Argument(..., help="TMDB movie ID"),
    language: str | None = typer.Option(None, "--language", "-l", help="Response language"),
    fmt: str = typer.Option("table", "--format", "-f", help="Output format: table|json"),
) -> None:
    """View movie credits."""
    lang = _resolve_lang(language)
    with TMDbClient() as c:
        data = c.get(f"/movie/{movie_id}/credits", params={"language": lang})
    credits = Credits(**data)

    if ctx.obj["json"]:
        display_json(credits)
        return

    if fmt == "json":
        display_json(credits)
        return

    cast_rows = [{"actor": m.name, "character": m.character} for m in credits.cast[:20]]
    display_table(
        cast_rows,
        [("actor", "Actor"), ("character", "Character")],
        title=f"Cast ({len(credits.cast)})",
    )

    if credits.crew:
        director = next((m.name for m in credits.crew if m.job == "Director"), "")
        writer = next((m.name for m in credits.crew if m.job == "Screenplay"), "")
        typer.echo(f"Director: {director or '-'}  Writer: {writer or '-'}")


@movie_app.command(name="images")
def movie_images(
    ctx: typer.Context,
    movie_id: int = typer.Argument(..., help="TMDB movie ID"),
    img_type: str = typer.Option("poster", "--type", "-t", help="Image type: poster|backdrop|logo"),
    language: str | None = typer.Option(None, "--language", "-l", help="Image language filter (e.g. zh, en, null)"),
) -> None:
    """List movie images and sizes."""
    params: dict[str, Any] = {}
    if language:
        params["include_image_language"] = language
    with TMDbClient() as c:
        data = c.get(f"/movie/{movie_id}/images", params=params)
    img = ImageCollection(**data)

    if ctx.obj["json"]:
        display_json(img)
        return

    items = getattr(img, img_type + "s", [])
    if not items:
        typer.echo(f"No {img_type} images for this movie.")
        return

    rows = [
        {
            "vote": f"{i.vote_average:.1f}",
            "size": f"{i.width}x{i.height}",
            "lang": i.iso_639_1 or "none",
            "path": i.file_path,
        }
        for i in items
    ]
    display_table(
        rows,
        [("vote", "Score"), ("size", "Size"), ("lang", "Lang"), ("path", "Path")],
        title=f"{img_type} ({len(items)})",
    )


@movie_app.command(name="similar")
def movie_similar(
    ctx: typer.Context,
    movie_id: int = typer.Argument(..., help="TMDB movie ID"),
    language: str | None = typer.Option(None, "--language", "-l", help="Response language"),
    fmt: str = typer.Option("table", "--format", "-f", help="Output format: table|json"),
) -> None:
    """View similar movie recommendations."""
    lang = _resolve_lang(language)
    with TMDbClient() as c:
        data = c.get(f"/movie/{movie_id}/similar", params={"language": lang})
    resp = MovieSearchResponse(**data)

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
        }
        for r in resp.results
    ]
    display_table(
        rows,
        [("id", "ID"), ("title", "Title"), ("release_date", "Release Date"), ("vote", "Rating")],
    )


@movie_app.command(name="recommendations")
def movie_recommendations(
    ctx: typer.Context,
    movie_id: int = typer.Argument(..., help="TMDB movie ID"),
    language: str | None = typer.Option(None, "--language", "-l", help="Response language"),
    fmt: str = typer.Option("table", "--format", "-f", help="Output format: table|json"),
) -> None:
    """View recommended movies."""
    lang = _resolve_lang(language)
    with TMDbClient() as c:
        data = c.get(f"/movie/{movie_id}/recommendations", params={"language": lang})
    resp = MovieSearchResponse(**data)

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
        }
        for r in resp.results
    ]
    display_table(
        rows,
        [("id", "ID"), ("title", "Title"), ("release_date", "Release Date"), ("vote", "Rating")],
    )
