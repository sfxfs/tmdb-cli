# tmdb-cli

TMDB API v3 command-line tool for scraping movie and TV series metadata.

## Installation

```sh
pip install tmdb-cli
# or
pipx install tmdb-cli
# or use uv
uv tool install tmdb-cli
# skill for coding agent
npx skills add https://github.com/sfxfs/tmdb-cli --skill tmdb-cli
```

Requires Python 3.11+. From source: `git clone <repo-url> && cd tmdb-cli && uv sync`.

## Setup

Get a **TMDB API Read Access Token** from [themoviedb.org/settings/api](https://www.themoviedb.org/settings/api).

```sh
tmdb config set token <YOUR_BEARER_TOKEN>
tmdb config validate
tmdb config set language zh-CN en    # optional: set preferred languages

Token is stored at `~/.config/tmdb-cli/config.toml`.

## Usage

```sh
tmdb COMMAND [OPTIONS] [ARGS]
```

Global flag `--json` forces raw JSON output on any command:

```sh
tmdb --json search movie "Inception" --language zh-CN
```

### Search

```sh
tmdb search movie "Inception" --year 2010 --language zh-CN
tmdb search movie "Fight Club" --format json --output result.json
tmdb search tv "Game of Thrones" --first-air-year 2011
```

### Movie Details

```sh
tmdb movie info 550                       # Fight Club
tmdb movie info 550 --language zh-CN      # Chinese metadata
tmdb movie credits 550                    # Cast & crew
tmdb movie images 550 --type poster       # List posters by vote score
tmdb movie images 550 --type poster --language zh
tmdb movie similar 550                    # Similar movies
tmdb movie recommendations 550            # AI recommendations
```

### Discover

```sh
tmdb discover movie --genre 28 --year 2023 --sort vote_average.desc
tmdb discover movie --genre 28 --genre 12 --vote-gte 7.5 --page 1
```

### Trending

```sh
tmdb trending movie --window day
tmdb trending movie --window week
```

### Genres

```sh
tmdb genre movie-list --language zh-CN
tmdb genre tv-list
```

### Images

```sh
tmdb images download 550 --type poster --size w500 --output-dir ./posters
tmdb images download 550 --type backdrop --size original --language zh
```

### Export

```sh
tmdb export nfo 550 --output-dir .              # Kodi-compatible NFO
tmdb export json 550 --output-dir ./data        # Full JSON dump
tmdb export csv 550 --output-dir .              # CSV summary
```

### Organize — Media Library Directory Structure

Creates directories with artwork and NFO metadata, following the convention used by Plex/Jellyfin/Emby.

```sh
# Movie: create Movies/Fight Club (1999)/ with poster, fanart, logo, banner, landscape, NFO
tmdb organize movie 550 --base-dir /path/to/media

# TV: create TVs/Game of Thrones (2011)/ with artwork, tvshow.nfo, per-season posters, per-episode thumbnails + NFO
tmdb organize tv 1399 --base-dir /path/to/media --seasons 1,2,3

# Preview only (no files written)
tmdb organize movie 550 --base-dir /path/to/media --dry-run
```

#### Movie directory template

```
Movies/Fight Club (1999)/
├── Fight Club (1999) poster.jpg
├── Fight Club (1999) fanart.jpg
├── Fight Club (1999) clearlogo.png
├── Fight Club (1999) banner.jpg
├── Fight Club (1999) landscape.jpg
└── Fight Club (1999).nfo
```

#### TV directory template

```
TVs/Game of Thrones (2011)/
├── poster.jpg
├── fanart.jpg
├── clearlogo.png
├── banner.jpg
├── tvshow.nfo
├── season01-poster.jpg
├── season02-poster.jpg
├── Season 1/
│   ├── Game of Thrones - S01E01 - Winter Is Coming.nfo
│   └── Game of Thrones - S01E01 - Winter Is Coming-thumb.jpg
└── Season 2/
    └── ...
```

## Development

```sh
uv sync --extra dev
uv run pytest
uv run ruff check .
uv run mypy src/
```
