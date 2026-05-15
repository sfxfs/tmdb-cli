"""TMDB API v3 HTTP client wrapper.

Features:
- Automatic Bearer Token attachment
- Unified error handling (HTTP status code -> friendly message)
- Rate limit awareness (429 auto retry)
- Connection timeout and reuse
"""

from __future__ import annotations

import time
from typing import Any, Self

import httpx
import typer

from .config import get_token

BASE_URL = "https://api.themoviedb.org/3"
DEFAULT_TIMEOUT = 15.0


class TMDbError(Exception):
    """Business error returned by the TMDB API."""

    def __init__(self, status_code: int, message: str):
        super().__init__(f"[{status_code}] {message}")
        self.status_code = status_code


class TMDbClient:
    """TMDB API client wrapping authentication, requests, and error handling."""

    def __init__(self, token: str | None = None) -> None:
        self._token = token or get_token()
        if not self._token:
            raise typer.BadParameter("API Key not set. Run `tmdb config set <KEY>` first")
        self._client = httpx.Client(
            base_url=BASE_URL,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Accept": "application/json",
            },
            timeout=httpx.Timeout(DEFAULT_TIMEOUT),
        )

    def close(self) -> None:
        self._client.close()

    def get(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Send a GET request and return the JSON body."""
        r = self._request_with_retry("GET", path, params=params)
        return r.json()  # type: ignore[no-any-return]

    def _request_with_retry(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        max_retries: int = 3,
    ) -> httpx.Response:
        for attempt in range(max_retries):
            try:
                r = self._client.request(method, path, params=params)
            except httpx.TimeoutException:
                raise TMDbError(0, "Request timed out. Please check your network connection")

            if r.status_code == 429:
                retry_after = int(r.headers.get("Retry-After", "2"))
                if attempt < max_retries - 1:
                    time.sleep(retry_after)
                    continue
                raise TMDbError(429, "Too many requests. Please try again later")

            if r.status_code >= 400:
                self._raise_http_error(r)

            return r

        raise TMDbError(500, "All retries exhausted")  # unreachable

    @staticmethod
    def _raise_http_error(r: httpx.Response) -> None:
        body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        msg = body.get("status_message", r.reason_phrase or f"HTTP {r.status_code}")
        raise TMDbError(r.status_code, msg)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


def get_image_url(file_path: str, size: str = "original") -> str:
    """Build a full image URL.

    `size` must be a valid size string (e.g. "w500", "original"); no validation is performed.
    Depends on the image base URL, which is a well-known hardcoded constant.
    """
    return f"https://image.tmdb.org/t/p/{size}{file_path}"
