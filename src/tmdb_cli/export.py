"""export subcommand: export as NFO / JSON / CSV format."""

from __future__ import annotations

import csv
from pathlib import Path

import typer

from .client import TMDbClient
from .config import get_language
from .models import MovieDetail

export_app = typer.Typer(name="export", help="Export to NFO/JSON/CSV formats")


def _resolve_lang(language: str | None) -> str:
    return language or get_language()


@export_app.command(name="nfo")
def export_nfo(
    movie_id: int = typer.Argument(..., help="TMDB movie ID"),
    output_dir: str = typer.Option(".", "--output-dir", "-o", help="Output directory"),
    language: str | None = typer.Option(None, "--language", "-l", help="Response language"),
) -> None:
    """Export a Kodi-compatible movie NFO file."""
    lang = _resolve_lang(language)
    with TMDbClient() as c:
        data = c.get(f"/movie/{movie_id}", params={"language": lang})
    movie = MovieDetail(**data)

    year = movie.release_date.year if movie.release_date else 0
    out_name = f"{movie.title} ({year}).nfo"
    out_path = Path(output_dir) / out_name

    nfo = _build_movie_nfo(movie)
    out_path.write_text(nfo, encoding="utf-8")
    typer.echo(f"Generated {out_path}")


@export_app.command(name="json")
def export_json(
    movie_id: int = typer.Argument(..., help="TMDB movie ID"),
    output_dir: str = typer.Option(".", "--output-dir", "-o", help="Output directory"),
    language: str | None = typer.Option(None, "--language", "-l", help="Response language"),
) -> None:
    """Export full JSON data."""
    lang = _resolve_lang(language)
    with TMDbClient() as c:
        data = c.get(f"/movie/{movie_id}", params={"language": lang})
    movie = MovieDetail(**data)

    year = movie.release_date.year if movie.release_date else 0
    out_name = f"{movie.title} ({year}).json"
    out_path = Path(output_dir) / out_name

    out_path.write_text(movie.model_dump_json(indent=2), encoding="utf-8")
    typer.echo(f"Generated {out_path}")


@export_app.command(name="csv")
def export_csv(
    movie_id: int = typer.Argument(..., help="TMDB movie ID"),
    output_dir: str = typer.Option(".", "--output-dir", "-o", help="Output directory"),
    language: str | None = typer.Option(None, "--language", "-l", help="Response language"),
) -> None:
    """Export CSV summary."""
    lang = _resolve_lang(language)
    with TMDbClient() as c:
        data = c.get(f"/movie/{movie_id}", params={"language": lang})
    movie = MovieDetail(**data)

    out_path = Path(output_dir) / f"{movie.title}.csv"
    movie_dict = movie.model_dump()
    # flatten lists to strings
    movie_dict["genres"] = ", ".join(g["name"] for g in movie_dict.get("genres", []))
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=movie_dict.keys())
        w.writeheader()
        w.writerow(movie_dict)
    typer.echo(f"Generated {out_path}")


def _build_movie_nfo(movie: MovieDetail) -> str:
    """Build Kodi movie NFO XML."""
    year = movie.release_date.year if movie.release_date else 0
    genres_xml = "\n".join(f"  <genre>{g.name}</genre>" for g in movie.genres)
    return f"""<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<movie>
  <title>{_esc(movie.title)}</title>
  <originaltitle>{_esc(movie.original_title)}</originaltitle>
  <year>{year}</year>
  <rating>{movie.vote_average}</rating>
  <votes>{movie.vote_count}</votes>
  <plot>{_esc(movie.overview)}</plot>
  <tagline>{_esc(movie.tagline)}</tagline>
  <runtime>{movie.runtime}</runtime>
  <mpaa>{_esc(movie.status)}</mpaa>
  <imdbid>{movie.imdb_id or ""}</imdbid>
{genres_xml}
</movie>
"""


def _esc(s: str) -> str:
    """XML entity escape."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
