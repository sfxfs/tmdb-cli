"""organize subcommand: organize movie and TV metadata into media library directory structure.

Directory template based on current structure at /Volumes/Untitled/文件归档/media:

Movies:  Movies/{title} ({year})/
        ├── {title} ({year}) {suffix}-poster.jpg
        ├── {title} ({year}) {suffix}-fanart.jpg
        ├── {title} ({year}) {suffix}-clearlogo.png
        ├── {title} ({year}) {suffix}-banner.jpg
        ├── {title} ({year}) {suffix}-landscape.jpg
        └── {title} ({year}) {suffix}.nfo

TVs:  TVs/{title} ({year})/
        ├── poster.jpg
        ├── fanart.jpg
        ├── clearlogo.png
        ├── banner.jpg
        ├── tvshow.nfo
        ├── season{N:02d}-poster.jpg
        └── Season {N}/
            ├── {title} - S{N:02d}E{NN:02d} - {ep_title}.nfo
            └── {title} - S{N:02d}E{NN:02d} - {ep_title}-thumb.jpg
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer

from .client import TMDbClient, get_image_url
from .config import get_fallback_language, get_language
from .export import _esc
from .models import (
    Episode,
    ImageCollection,
    MovieDetail,
    SeasonDetail,
    TVDetail,
    TVImageCollection,
)
from .utils import sanitize_filename

organize_app = typer.Typer(name="organize", help="Organize files into media library directory structure")

# Movie image suffix mapping: TMDB image_type -> (file_suffix, extension)
MOVIE_IMAGE_TYPES = [
    ("posters", "poster", "jpg"),
    ("backdrops", "fanart", "jpg"),
    ("logos", "clearlogo", "png"),
    ("backdrops", "banner", "jpg"),
    ("backdrops", "landscape", "jpg"),
]


def _resolve_lang(language: str | None) -> str:
    return language or get_language()


def _image_lang_filter(language: str | None) -> str:
    """Build include_image_language param from user flag or config preferences."""
    if language:
        return f"{language},null"
    fallback = get_fallback_language()
    if fallback:
        return f"{get_language()},{fallback}"
    return f"{get_language()},null"


def _pick_best(items: list[Any], *, key: Any = lambda x: x.vote_average) -> Any:
    """Pick the best item sorted by rating descending."""
    return sorted(items, key=key, reverse=True)[0] if items else None


def _dl(client_obj: TMDbClient, file_path: str, out_path: Path, size: str = "original") -> None:
    """Download image to out_path, skipping existing files."""
    if out_path.exists():
        return
    import httpx

    url = get_image_url(file_path, size)
    token = client_obj._token
    with httpx.Client(timeout=30) as dl_client:
        r = dl_client.get(url, headers={"Authorization": f"Bearer {token}"} if token else {})
        r.raise_for_status()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(r.content)


# ── organize movie ────────────────────────────────────


@organize_app.command(name="movie")
def organize_movie(
    movie_id: int = typer.Argument(..., help="TMDB movie ID"),
    base_dir: str = typer.Option(
        "/Volumes/Untitled/文件归档/media",
        "--base-dir",
        "-d",
        help="Media library root directory",
    ),
    language: str | None = typer.Option(None, "--language", "-l", help="Metadata language"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview only, do not write anything"),
) -> None:
    """Create directory per movie template and download poster/fanart/logo/banner/landscape + NFO."""
    lang = _resolve_lang(language)

    with TMDbClient() as c:
        movie_data = c.get(f"/movie/{movie_id}", params={"language": lang})
        img_data = c.get(f"/movie/{movie_id}/images")
        img_filter = _image_lang_filter(language)
        img_zh_data = c.get(
            f"/movie/{movie_id}/images",
            params={"include_image_language": img_filter},
        )
    movie = MovieDetail(**movie_data)
    img_all = ImageCollection(**img_data)
    img_zh = ImageCollection(**img_zh_data)

    year = movie.release_date.year if movie.release_date else 0
    folder_name = sanitize_filename(f"{movie.title} ({year})")
    movie_dir = Path(base_dir) / "Movies" / folder_name

    if dry_run:
        typer.echo(f"[DRY RUN] Will create: {movie_dir}/")
        _preview_movie_files(movie_dir, movie, img_all, img_zh)
        return

    movie_dir.mkdir(parents=True, exist_ok=True)

    # Download images
    for tmdb_type, suffix, ext in MOVIE_IMAGE_TYPES:
        items = getattr(img_zh if img_zh and getattr(img_zh, tmdb_type, None) else img_all, tmdb_type, [])
        best = _pick_best(items)
        if best:
            out_name = f"{folder_name} {suffix}.{ext}"
            out_path = movie_dir / out_name
            _dl(c, best.file_path, out_path)
            typer.echo(f"  Downloading {suffix}: {best.width}x{best.height}")

    # Poster handling (prefer Chinese poster)
    poster_items = img_zh.posters or img_all.posters
    best_poster = _pick_best(poster_items)
    if best_poster:
        out_path = movie_dir / f"{folder_name} poster.jpg"
        _dl(c, best_poster.file_path, out_path)
        typer.echo(f"  Downloading poster: {best_poster.width}x{best_poster.height}")

    # NFO
    nfo_path = movie_dir / f"{folder_name}.nfo"
    nfo = _build_movie_nfo(movie)
    nfo_path.write_text(nfo, encoding="utf-8")
    typer.echo(f"  Generated NFO: {nfo_path.name}")

    typer.echo(f"\nDone: {movie_dir}")


def _preview_movie_files(
    movie_dir: Path, movie: MovieDetail, img_all: ImageCollection, img_zh: ImageCollection
) -> None:
    """--dry-run preview."""
    folder_name = movie_dir.name
    img = img_zh if img_zh else img_all

    for tmdb_type, suffix, ext in MOVIE_IMAGE_TYPES:
        items = getattr(img, tmdb_type, [])
        best = _pick_best(items)
        if best:
            typer.echo(f"  {folder_name} {suffix}.{ext} ({best.width}x{best.height})")

    best_poster = _pick_best(img.posters)
    if best_poster:
        typer.echo(f"  {folder_name} poster.jpg ({best_poster.width}x{best_poster.height})")

    typer.echo(f"  {folder_name}.nfo")


# ── organize tv ───────────────────────────────────────


@organize_app.command(name="tv")
def organize_tv(
    tv_id: int = typer.Argument(..., help="TMDB TV show ID"),
    base_dir: str = typer.Option(
        "/Volumes/Untitled/文件归档/media",
        "--base-dir",
        "-d",
        help="Media library root directory",
    ),
    language: str | None = typer.Option(None, "--language", "-l", help="Metadata language"),
    seasons: str | None = typer.Option(
        None,
        "--seasons",
        help="Season numbers, comma separated (e.g. 1,2,3), default all",
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview only, do not write anything"),
) -> None:
    """Create directory per TV template and download poster/fanart/logo/banner + per-episode NFO and thumbnails."""
    lang = _resolve_lang(language)
    season_list: list[int] | None = None
    if seasons:
        season_list = [int(s.strip()) for s in seasons.split(",") if s.strip()]

    with TMDbClient() as c:
        tv_data = c.get(f"/tv/{tv_id}", params={"language": lang})
        tv_img_data = c.get(f"/tv/{tv_id}/images")
        img_filter = _image_lang_filter(language)
        tv_img_zh_data = c.get(
            f"/tv/{tv_id}/images",
            params={"include_image_language": img_filter},
        )
    tv = TVDetail(**tv_data)
    tv_img = TVImageCollection(**tv_img_data)
    tv_img_zh = TVImageCollection(**tv_img_zh_data)

    year = tv.first_air_date.year if tv.first_air_date else 0
    folder_name = sanitize_filename(f"{tv.name} ({year})")
    tv_dir = Path(base_dir) / "TVs" / folder_name

    # Determine which seasons to process
    if season_list:
        target_seasons = [s for s in season_list if 1 <= s <= tv.number_of_seasons]
    else:
        target_seasons = list(range(1, tv.number_of_seasons + 1))

    if dry_run:
        typer.echo(f"[DRY RUN] Will create: {tv_dir}/")
        _preview_tv_files(tv_dir, tv, tv_img_zh or tv_img, target_seasons)
        return

    tv_dir.mkdir(parents=True, exist_ok=True)

    # TV-level images
    img_src = tv_img_zh if (tv_img_zh and (tv_img_zh.posters or tv_img_zh.backdrops)) else tv_img
    _download_tv_art(c, tv_dir, img_src)

    # Per-season poster + data
    with TMDbClient() as c2:
        for sn in target_seasons:
            season_dir = tv_dir / f"Season {sn}"
            season_dir.mkdir(parents=True, exist_ok=True)

            # Download season poster
            season_data = c2.get(f"/tv/{tv_id}/season/{sn}", params={"language": lang})
            season = SeasonDetail(**season_data)
            if season.poster_path:
                out_path = tv_dir / f"season{sn:02d}-poster.jpg"
                _dl(c2, season.poster_path, out_path)
                typer.echo(f"  Downloading season{sn:02d}-poster.jpg")

            # Per-episode thumbnail + NFO
            for ep in season.episodes:
                if ep.episode_number == 0:
                    continue
                _write_episode_files(c2, season_dir, tv.name, sn, ep)

    # tvshow.nfo
    nfo_path = tv_dir / "tvshow.nfo"
    nfo_path.write_text(_build_tvshow_nfo(tv), encoding="utf-8")
    typer.echo(f"  Generated {nfo_path.name}")

    typer.echo(f"\nDone: {tv_dir}")


def _download_tv_art(c: TMDbClient, tv_dir: Path, img: TVImageCollection) -> None:
    """Download TV-level images: poster, fanart, clearlogo, banner."""
    best_poster = _pick_best(img.posters)
    if best_poster:
        _dl(c, best_poster.file_path, tv_dir / "poster.jpg")
        typer.echo(f"  Downloading poster.jpg ({best_poster.width}x{best_poster.height})")

    best_fanart = _pick_best(img.backdrops)
    if best_fanart:
        _dl(c, best_fanart.file_path, tv_dir / "fanart.jpg")
        typer.echo(f"  Downloading fanart.jpg ({best_fanart.width}x{best_fanart.height})")

    best_logo = _pick_best(img.logos)
    if best_logo:
        ext = Path(best_logo.file_path).suffix.lstrip(".") or "png"
        _dl(c, best_logo.file_path, tv_dir / f"clearlogo.{ext}")
        typer.echo(f"  Downloading clearlogo.{ext} ({best_logo.width}x{best_logo.height})")

    # banner: take second-best backdrop (different from fanart)
    if len(img.backdrops) > 1:
        banner_img = sorted(img.backdrops, key=lambda x: x.vote_average, reverse=True)[1]
        _dl(c, banner_img.file_path, tv_dir / "banner.jpg")
        typer.echo(f"  Downloading banner.jpg ({banner_img.width}x{banner_img.height})")
    elif best_fanart:
        _dl(c, best_fanart.file_path, tv_dir / "banner.jpg")
        typer.echo(f"  Downloading banner.jpg ({best_fanart.width}x{best_fanart.height})")


def _write_episode_files(
    c: TMDbClient,
    season_dir: Path,
    show_name: str,
    season_num: int,
    ep: Episode,
) -> None:
    """Write NFO and thumbnail for a single episode."""
    ep_prefix = sanitize_filename(f"{show_name} - S{season_num:02d}E{ep.episode_number:02d} - {ep.name}")

    # NFO
    nfo_path = season_dir / f"{ep_prefix}.nfo"
    if not nfo_path.exists():
        nfo = _build_episode_nfo(show_name, season_num, ep)
        nfo_path.write_text(nfo, encoding="utf-8")

    # Thumbnail
    if ep.still_path:
        thumb_path = season_dir / f"{ep_prefix}-thumb.jpg"
        _dl(c, ep.still_path, thumb_path)


def _preview_tv_files(tv_dir: Path, tv: TVDetail, img: TVImageCollection, target_seasons: list[int]) -> None:
    """--dry-run preview."""
    if _pick_best(img.posters):
        typer.echo("  poster.jpg")
    if _pick_best(img.backdrops):
        typer.echo("  fanart.jpg")
    if _pick_best(img.logos):
        typer.echo("  clearlogo.png")
    if len(img.backdrops) > 1 or _pick_best(img.backdrops):
        typer.echo("  banner.jpg")
    for sn in target_seasons:
        typer.echo(f"  season{sn:02d}-poster.jpg")
        typer.echo("  tvshow.nfo")
        typer.echo(f"  Season {sn}/ (episode NFO + thumb)")
    typer.echo("  tvshow.nfo")


# ── NFO generator ────────────────────────────────────────


def _build_movie_nfo(movie: MovieDetail) -> str:
    year = movie.release_date.year if movie.release_date else 0
    genres_xml = "\n".join(f"  <genre>{_esc(g.name)}</genre>" for g in movie.genres)
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


def _build_tvshow_nfo(tv: TVDetail) -> str:
    year = tv.first_air_date.year if tv.first_air_date else 0
    genres_xml = "\n".join(f"  <genre>{_esc(g.name)}</genre>" for g in tv.genres)
    networks_xml = "\n".join(f"  <studio>{_esc(n.name)}</studio>" for n in tv.networks)
    runtime = tv.episode_run_time[0] if tv.episode_run_time else 0
    return f"""<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<tvshow>
  <title>{_esc(tv.name)}</title>
  <originaltitle>{_esc(tv.original_name)}</originaltitle>
  <year>{year}</year>
  <rating>{tv.vote_average}</rating>
  <votes>{tv.vote_count}</votes>
  <plot>{_esc(tv.overview)}</plot>
  <runtime>{runtime}</runtime>
  <status>{_esc(tv.status)}</status>
  <season>{tv.number_of_seasons}</season>
  <episode>{tv.number_of_episodes}</episode>
{genres_xml}
{networks_xml}
</tvshow>
"""


def _build_episode_nfo(show_name: str, season: int, ep: Episode) -> str:
    aired = str(ep.air_date) if ep.air_date else ""
    return f"""<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<episodedetails>
  <title>{_esc(ep.name)}</title>
  <showtitle>{_esc(show_name)}</showtitle>
  <season>{season}</season>
  <episode>{ep.episode_number}</episode>
  <aired>{aired}</aired>
  <rating>{ep.vote_average}</rating>
  <votes>{ep.vote_count}</votes>
  <plot>{_esc(ep.overview)}</plot>
</episodedetails>
"""
