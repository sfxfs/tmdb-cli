"""TMDB CLI — movie and TV series metadata scraper.

Entry point: `tmdb` command registered via pyproject.toml [project.scripts].

Global option `--json` forces JSON output on all commands instead of terminal tables.
"""

from __future__ import annotations

import typer

from .commands.discover import discover_app
from .commands.genre import genre_app
from .commands.images import images_app
from .commands.movie import movie_app
from .commands.search import search_app
from .commands.trending import trending_app
from .config import config_app
from .export import export_app
from .organize import organize_app

app = typer.Typer(
    name="tmdb",
    help="TMDB API CLI — movie and TV series metadata tool",
    no_args_is_help=True,
)


@app.callback(invoke_without_command=False)
def main_callback(
    ctx: typer.Context,
    json: bool = typer.Option(False, "--json", help="Output raw JSON (for agentic AI consumption)"),
) -> None:
    ctx.obj = {"json": json}


app.add_typer(config_app)
app.add_typer(search_app)
app.add_typer(movie_app)
app.add_typer(discover_app)
app.add_typer(trending_app)
app.add_typer(genre_app)
app.add_typer(images_app)
app.add_typer(organize_app)
app.add_typer(export_app)


def main() -> None:
    app()
