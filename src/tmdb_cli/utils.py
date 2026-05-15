"""Utility functions: output formatting, safe filenames."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel
from rich.console import Console
from rich.table import Table

console = Console()


def sanitize_filename(name: str) -> str:
    """Replace filesystem-illegal characters in a string with safe characters."""
    return re.sub(r'[<>:"/\\|?*]', " ", name).strip()


def display_table(
    rows: list[dict[str, Any]],
    columns: list[tuple[str, str]],  # (key, header)
    title: str | None = None,
) -> None:
    """Output a list of dictionary rows as a Rich table."""
    table = Table(title=title, show_lines=False)
    for _, header in columns:
        table.add_column(header, no_wrap=True)
    for row in rows:
        table.add_row(*[str(row.get(k, "")) for k, _ in columns])
    console.print(table)


def display_json(data: BaseModel | list[BaseModel] | dict[str, Any], indent: int = 2) -> None:
    """Output model data as highlighted JSON."""
    import json as _json

    if isinstance(data, BaseModel):
        text = data.model_dump_json(indent=indent)
    elif isinstance(data, list):
        text = _json.dumps(
            [d.model_dump() if isinstance(d, BaseModel) else d for d in data],
            ensure_ascii=False,
            indent=indent,
            default=str,
        )
    else:
        text = _json.dumps(data, ensure_ascii=False, indent=indent, default=str)
    console.print_json(text)
