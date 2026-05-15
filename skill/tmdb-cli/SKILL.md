---
name: tmdb-cli
description: TMDB movie and TV metadata CLI — search, discover, organize media with NFO/artwork. Use when the user needs to look up movie/TV information, organize media libraries, generate Kodi NFO files, download posters/backdrops, or scrape TMDB metadata. Also use when the user mentions "movie database", "TMDB", "media server", "Plex", "Jellyfin", "Emby", "Kodi metadata", "movie scraper", or wants to automate media organization.
---

# TMDB CLI Skill

Use the `tmdb` CLI tool to interact with The Movie Database (TMDB) API v3. All metadata, images, and organization commands go through this single tool.

## Installation

If `tmdb` is not already available, install it:

```bash
pip install tmdb-cli
# or
pipx install tmdb-cli
# or via uv
uv tool install tmdb-cli
```

Verify with `tmdb --help`.

## Setup

Before first use, get a TMDB API Read Access Token from https://www.themoviedb.org/settings/api.


```bash
tmdb config set token <TOKEN>
tmdb config validate
```

Set language preferences once so commands don't need to repeat `--language`:

```bash
tmdb config set language zh-CN en
```

## Global Flag

Every command that produces output accepts `--json` for raw JSON:

```bash
tmdb --json search movie "Fight Club"
```

## Core Commands

### Search movies and TV series

```bash
tmdb search movie "Inception" --year 2010 --language zh-CN
tmdb search movie "Fight Club" --format json --output results.json
tmdb search tv "Game of Thrones" --first-air-year 2011
```

### Movie details

```bash
tmdb movie info 550                       # basic info (Fight Club)
tmdb movie info 550 --language zh-CN      # Chinese metadata
tmdb movie credits 550                    # cast and crew
tmdb movie images 550 --type poster       # list posters by vote score
tmdb movie images 550 --type poster --language zh
tmdb movie similar 550                    # similar movies
tmdb movie recommendations 550            # AI recommendations
```

### Discover (advanced filtering)

```bash
tmdb discover movie --genre 28 --year 2023 --sort vote_average.desc
tmdb discover movie --genre 28 --genre 12 --vote-gte 7.5 --page 1
```

### Trending and genres

```bash
tmdb trending movie --window week
tmdb genre movie-list --language zh-CN
tmdb genre tv-list
```

### Image download

```bash
tmdb images download 550 --type poster --size w500 --output-dir ./posters
tmdb images download 550 --type backdrop --size original --language zh
```

### Export (NFO for Kodi/Plex/Jellyfin/Emby)

```bash
tmdb export nfo 550 --output-dir .              # Kodi-compatible movie NFO
tmdb export json 550 --output-dir ./data        # full JSON dump
tmdb export csv 550 --output-dir .              # CSV summary
```

### Organize — create media library directory structure

Creates properly-named directories with artwork and NFO metadata for media servers.

```bash
# Movie: creates Movies/Fight Club (1999)/ with poster, fanart, logo, NFO
tmdb organize movie 550 --base-dir /Volumes/Untitled/媒体库

# TV: creates TVs/Game of Thrones (2011)/ with all seasons, episodes, artwork
tmdb organize tv 1399 --base-dir /Volumes/Untitled/媒体库 --seasons 1,2,3

# Preview only
tmdb organize movie 550 --dry-run
```

The `organize` command produces this structure:
```
Movies/Fight Club (1999)/
├── Fight Club (1999) poster.jpg
├── Fight Club (1999) fanart.jpg
├── Fight Club (1999) clearlogo.png
├── Fight Club (1999) banner.jpg
├── Fight Club (1999) landscape.jpg
└── Fight Club (1999).nfo
```

For TV:
```
TVs/Game of Thrones (2011)/
├── poster.jpg
├── fanart.jpg
├── clearlogo.png
├── banner.jpg
├── tvshow.nfo
├── season01-poster.jpg
├── Season 1/
│   ├── Game of Thrones - S01E01 - Winter Is Coming.nfo
│   └── Game of Thrones - S01E01 - Winter Is Coming-thumb.jpg
└── Season 2/ ...
```

## Key Details

- **Config path**: `~/.config/tmdb-cli/config.toml` (XDG)
- **TMDB IDs**: use numeric TMDB IDs (e.g., 550 = Fight Club, 1399 = Game of Thrones)
- **Language format**: ISO 639-1 with optional region (e.g., `zh-CN`, `en`, `ja`)
- **Image sizes**: `w92`, `w154`, `w185`, `w342`, `w500`, `w780`, `original`
- **Image types**: `poster`, `backdrop`, `logo`
- **Output formats**: `table` (default), `json`, `csv`
- **Sort options**: `popularity.asc`, `popularity.desc`, `vote_average.asc`, `vote_average.desc`, `release_date.asc`, `release_date.desc`, etc.

## Common Workflows

**Full media organization pipeline:**
```bash
tmdb config set token <TOKEN>
tmdb config set language zh-CN en
tmdb search movie "The Matrix"
# note the ID (e.g., 603)
tmdb organize movie 603 --base-dir /path/to/media
```

**Batch TV series organization:**
```bash
tmdb search tv "Breaking Bad"
# note the ID (e.g., 1396)
tmdb organize tv 1396 --base-dir /path/to/media
```

**Quick metadata lookup for a known movie:**
```bash
tmdb --json movie info 550
```
