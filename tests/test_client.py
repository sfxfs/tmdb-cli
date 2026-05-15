"""Tests for TMDB HTTP client with mock responses."""

from __future__ import annotations

import pytest
from pytest_httpx import HTTPXMock

from tmdb_cli.client import TMDbClient, TMDbError, get_image_url


class TestGetImageUrl:
    def test_original_size(self) -> None:
        url = get_image_url("/abc.jpg")
        assert url == "https://image.tmdb.org/t/p/original/abc.jpg"

    def test_custom_size(self) -> None:
        url = get_image_url("/poster.jpg", "w500")
        assert url == "https://image.tmdb.org/t/p/w500/poster.jpg"


class TestClientWithMock:
    def test_get_success(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url="https://api.themoviedb.org/3/movie/550",
            json={"id": 550, "title": "Fight Club"},
        )
        with TMDbClient(token="test-token") as c:
            data = c.get("/movie/550")
        assert data["id"] == 550
        assert data["title"] == "Fight Club"

    def test_401_error(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url="https://api.themoviedb.org/3/movie/999",
            status_code=401,
            json={"status_message": "Invalid API key"},
        )
        with TMDbClient(token="bad-token") as c:
            with pytest.raises(TMDbError) as exc:
                c.get("/movie/999")
            assert exc.value.status_code == 401

    def test_429_retry(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url="https://api.themoviedb.org/3/movie/1",
            status_code=429,
            headers={"Retry-After": "0"},
        )
        httpx_mock.add_response(
            url="https://api.themoviedb.org/3/movie/1",
            json={"id": 1},
        )
        with TMDbClient(token="test-token") as c:
            data = c.get("/movie/1")
        assert data["id"] == 1

    def test_404_error(self, httpx_mock: HTTPXMock) -> None:
        httpx_mock.add_response(
            url="https://api.themoviedb.org/3/movie/999999",
            status_code=404,
            json={"status_message": "The resource you requested could not be found."},
        )
        with TMDbClient(token="test-token") as c:
            with pytest.raises(TMDbError) as exc:
                c.get("/movie/999999")
            assert exc.value.status_code == 404

    def test_missing_token(self) -> None:
        """Client without token must raise on construction."""
        import typer

        with pytest.raises(typer.BadParameter):
            TMDbClient(token="")
