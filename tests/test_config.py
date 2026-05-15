"""Tests for TMDB CLI configuration management."""

from __future__ import annotations

from pathlib import Path

import pytest

from tmdb_cli.config import (
    _toml_dumps,
    _toml_value,
    get_token,
    load_config,
    save_config,
)


@pytest.fixture(autouse=True)
def clean_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Redirect config to temp directory for isolation."""
    monkeypatch.setattr("tmdb_cli.config.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("tmdb_cli.config.CONFIG_FILE", tmp_path / "config.toml")


class TestConfigIO:
    def test_load_empty(self) -> None:
        assert load_config() == {}

    def test_save_and_load(self) -> None:
        save_config({"api": {"bearer_token": "abc123"}})
        cfg = load_config()
        assert cfg["api"]["bearer_token"] == "abc123"

    def test_get_token_none(self) -> None:
        assert get_token() is None

    def test_get_token_set(self) -> None:
        save_config({"api": {"bearer_token": "xyz"}})
        assert get_token() == "xyz"


class TestTomlSerialization:
    def test_simple_keys(self) -> None:
        result = _toml_dumps({"key": "val"})
        assert 'key = "val"' in result

    def test_nested_section(self) -> None:
        result = _toml_dumps({"api": {"bearer_token": "tok"}})
        joined = "\n".join(result)
        assert "[api]" in joined
        assert 'bearer_token = "tok"' in joined

    def test_bool_value(self) -> None:
        assert _toml_value(True) == "true"
        assert _toml_value(False) == "false"

    def test_int_value(self) -> None:
        assert _toml_value(42) == "42"

    def test_string_value(self) -> None:
        assert _toml_value("hello") == '"hello"'
