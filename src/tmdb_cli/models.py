"""TMDB API response data models (Pydantic v2).

Covers movie search, detail, images, credits, and TV series / season info.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict


def _parse_optional_date(v: Any) -> date | None:
    """Convert empty string to None, pass through None, parse dates."""
    if v is None or v == "":
        return None
    if isinstance(v, date):
        return v
    return date.fromisoformat(str(v))


OptionalDate = Annotated[date | None, BeforeValidator(_parse_optional_date)]

# -- Common --


class Genre(BaseModel):
    id: int
    name: str = ""


class ProductionCompany(BaseModel):
    id: int
    name: str = ""
    origin_country: str = ""
    logo_path: str | None = None


class ProductionCountry(BaseModel):
    iso_3166_1: str = ""
    name: str = ""


class SpokenLanguage(BaseModel):
    iso_639_1: str = ""
    name: str = ""
    english_name: str = ""


class ImageItem(BaseModel):
    aspect_ratio: float = 0.0
    file_path: str = ""
    height: int = 0
    width: int = 0
    iso_639_1: str | None = None
    vote_average: float = 0.0
    vote_count: int = 0


class ImageCollection(BaseModel):
    """Image collection response."""

    id: int
    backdrops: list[ImageItem] = []
    posters: list[ImageItem] = []
    logos: list[ImageItem] = []


class TVImageCollection(BaseModel):
    """TV image collection response."""

    id: int
    backdrops: list[ImageItem] = []
    posters: list[ImageItem] = []
    logos: list[ImageItem] = []


# -- Movies --


class MovieSearchResult(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    title: str = ""
    original_title: str = ""
    overview: str = ""
    poster_path: str | None = None
    backdrop_path: str | None = None
    release_date: OptionalDate = None
    vote_average: float = 0.0
    vote_count: int = 0
    genre_ids: list[int] = []
    popularity: float = 0.0


class MovieSearchResponse(BaseModel):
    page: int = 1
    total_pages: int = 1
    total_results: int = 0
    results: list[MovieSearchResult] = []


class MovieDetail(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    title: str = ""
    original_title: str = ""
    overview: str = ""
    tagline: str = ""
    poster_path: str | None = None
    backdrop_path: str | None = None
    release_date: OptionalDate = None
    runtime: int = 0
    budget: int = 0
    revenue: int = 0
    vote_average: float = 0.0
    vote_count: int = 0
    popularity: float = 0.0
    status: str = ""
    homepage: str = ""
    imdb_id: str | None = None
    genres: list[Genre] = []
    spoken_languages: list[SpokenLanguage] = []
    production_companies: list[ProductionCompany] = []
    production_countries: list[ProductionCountry] = []


class CastMember(BaseModel):
    id: int
    name: str = ""
    character: str = ""
    profile_path: str | None = None
    order: int = 99
    known_for_department: str = ""


class CrewMember(BaseModel):
    id: int
    name: str = ""
    job: str = ""
    department: str = ""
    profile_path: str | None = None


class Credits(BaseModel):
    id: int
    cast: list[CastMember] = []
    crew: list[CrewMember] = []


# -- TV Series --


class TVSearchResult(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    name: str = ""
    original_name: str = ""
    overview: str = ""
    poster_path: str | None = None
    backdrop_path: str | None = None
    first_air_date: OptionalDate = None
    vote_average: float = 0.0
    vote_count: int = 0
    genre_ids: list[int] = []
    popularity: float = 0.0
    origin_country: list[str] = []


class TVSearchResponse(BaseModel):
    page: int = 1
    total_pages: int = 1
    total_results: int = 0
    results: list[TVSearchResult] = []


class Network(BaseModel):
    id: int
    name: str = ""
    logo_path: str | None = None
    origin_country: str = ""


class TVDetail(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    name: str = ""
    original_name: str = ""
    overview: str = ""
    poster_path: str | None = None
    backdrop_path: str | None = None
    first_air_date: OptionalDate = None
    last_air_date: OptionalDate = None
    status: str = ""
    number_of_seasons: int = 0
    number_of_episodes: int = 0
    genres: list[Genre] = []
    networks: list[Network] = []
    episode_run_time: list[int] = []
    vote_average: float = 0.0
    vote_count: int = 0
    popularity: float = 0.0


class Episode(BaseModel):
    episode_number: int = 0
    name: str = ""
    overview: str = ""
    still_path: str | None = None
    air_date: OptionalDate = None
    vote_average: float = 0.0
    vote_count: int = 0


class SeasonDetail(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    name: str = ""
    season_number: int = 0
    overview: str = ""
    poster_path: str | None = None
    air_date: OptionalDate = None
    episodes: list[Episode] = []


# -- Discover / Trending --


class DiscoverResponse(BaseModel):
    page: int = 1
    total_pages: int = 1
    total_results: int = 0
    results: list[MovieSearchResult] = []


class TrendingResponse(BaseModel):
    page: int = 1
    total_pages: int = 1
    total_results: int = 0
    results: list[MovieSearchResult] = []


# -- Genre --


class GenreListResponse(BaseModel):
    genres: list[Genre] = []
