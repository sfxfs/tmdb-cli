"""images subcommand: download movie/TV series images locally."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer

from ..client import TMDbClient, get_image_url
from ..models import ImageCollection

images_app = typer.Typer(name="images", help="Download images")


@images_app.command(name="download")
def images_download(
    movie_id: int = typer.Argument(..., help="TMDB movie ID"),
    img_type: str = typer.Option("poster", "--type", "-t", help="Image type: poster|backdrop|logo"),
    size: str = typer.Option("w500", "--size", "-s", help="Image size: w500|original|w780|w1280|..."),
    output_dir: str = typer.Option(".", "--output-dir", "-o", help="Output directory"),
    language: str | None = typer.Option(None, "--language", "-l", help="Image language filter (e.g. zh, en, null)"),
) -> None:
    """Download the best image for a movie (sorted by vote, first one)."""
    import httpx

    params: dict[str, Any] = {}
    if language:
        params["include_image_language"] = language

    with TMDbClient() as c:
        data = c.get(f"/movie/{movie_id}/images", params=params)
    img = ImageCollection(**data)

    items = getattr(img, img_type + "s", [])
    if not items:
        typer.echo(f"No {img_type} image found for this movie.")
        return

    best = sorted(items, key=lambda x: x.vote_average, reverse=True)[0]
    url = get_image_url(best.file_path, size)
    out_path = Path(output_dir) / f"{movie_id}_{img_type}_{size}.jpg"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # use httpx directly for binary download (no JSON parsing)
    token = c._token
    with httpx.Client(timeout=30) as dl_client:
        r = dl_client.get(url, headers={"Authorization": f"Bearer {token}"} if token else {})
        r.raise_for_status()
        out_path.write_bytes(r.content)

    typer.echo(f"Downloaded {best.width}x{best.height} -> {out_path}")
