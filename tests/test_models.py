"""Tests for Pydantic data models — edge cases in TMDB API responses."""

from __future__ import annotations

from tmdb_cli.models import (
    Episode,
    ImageItem,
    MovieDetail,
    MovieSearchResult,
    SeasonDetail,
    TVDetail,
    TVSearchResult,
)


class TestMovieSearchResult:
    def test_empty_release_date(self) -> None:
        """Empty string release_date must parse as None."""
        m = MovieSearchResult(id=1, release_date="")  # type: ignore[arg-type]
        assert m.release_date is None

    def test_valid_date(self) -> None:
        m = MovieSearchResult(id=1, release_date="2023-01-15")  # type: ignore[arg-type]
        assert m.release_date is not None
        assert m.release_date.year == 2023

    def test_none_date(self) -> None:
        m = MovieSearchResult(id=1, release_date=None)
        assert m.release_date is None


class TestMovieDetail:
    def test_empty_release_date(self) -> None:
        m = MovieDetail(id=1, release_date="")  # type: ignore[arg-type]
        assert m.release_date is None


class TestTVSearchResult:
    def test_empty_first_air_date(self) -> None:
        t = TVSearchResult(id=1, first_air_date="")  # type: ignore[arg-type]
        assert t.first_air_date is None


class TestTVDetail:
    def test_empty_dates(self) -> None:
        t = TVDetail(id=1, first_air_date="", last_air_date="")  # type: ignore[arg-type]
        assert t.first_air_date is None
        assert t.last_air_date is None


class TestEpisode:
    def test_empty_air_date(self) -> None:
        e = Episode(episode_number=1, air_date="")  # type: ignore[arg-type]
        assert e.air_date is None


class TestSeasonDetail:
    def test_empty_air_date(self) -> None:
        s = SeasonDetail(id=1, season_number=1, air_date="")  # type: ignore[arg-type]
        assert s.air_date is None


class TestImageItem:
    def test_defaults(self) -> None:
        img = ImageItem(file_path="/abc.jpg")
        assert img.width == 0
        assert img.vote_average == 0.0
