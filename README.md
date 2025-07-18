# new_songs_enjoyer

Crafts you a playlist to discover new songs based on preferences using the Last.fm API.

## Features

- 🎵 Fetches tracks from Last.fm based on configurable tags (chill, ambient, lofi)
- 📅 Daily recommendations with duplicate prevention
- 📝 Maintains history of previously suggested tracks
- 🎧 **Platform Filtering**: Excludes tracks you've already liked on SoundCloud/Spotify
- 🔄 Multi-platform integration (SoundCloud + optional Spotify)
- 🌐 **Web interface** for easy playlist generation and platform integration
- 🔒 Secure API key management with environment variables
- ⚡ Fast dependency management with uv

## Prerequisites

- Python 3.8 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- Last.fm API key (free from [Last.fm API](https://www.last.fm/api))

## Installation

1. **Install uv** (if not already installed):

   ```bash
   # On macOS and Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # On Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **Clone the repository**:

   ```bash
   git clone https://github.com/ArcadiaWorks/new_songs_enjoyer.git
   cd new_songs_enjoyer
   ```

3. **Install dependencies using uv**:

   ```bash
   uv sync
   ```

4. **Set up your API key**:

   ```bash
   # Copy the example environment file
   cp .env.example .env

   # Edit .env and add your Last.fm API key
   # LASTFM_API_KEY=your_actual_api_key_here
   ```

## Quick Start

### Command Line Usage

```bash
# Install dependencies
uv sync

# Run with default settings
uv run python main.py

# Run with custom tags
uv run python main.py --tags jazz blues --num-tracks 15
```

### Web Interface Usage

Launch the web server for an easy-to-use interface with SoundCloud integration:

```bash
# Start the web server
python run.py server

# Or alternatively
uv run python web_server.py
```

Then open your browser to **http://localhost:5000** to:

- Generate playlists with a user-friendly form
- View existing playlists with embedded SoundCloud players
- Import playlists directly to SoundCloud
- Extract SoundCloud OAuth tokens with step-by-step guidance

The web interface is perfect for:

- **First-time users** who want a guided experience
- **SoundCloud integration** with visual playlist import
- **Easy token extraction** with built-in instructions
- **Playlist browsing** with embedded audio players

For detailed usage instructions, examples, and advanced configuration, see **[docs/USAGE.md](docs/USAGE.md)**.

## Configuration

The application uses a YAML configuration file (`config.yaml`) for settings:

```yaml
# Default music tags
default_tags:
  - "chill"
  - "ambient"
  - "lofi"

# Number of tracks per day
num_tracks: 20

# API settings
api:
  limit_per_tag: 100
  base_url: "https://ws.audioscrobbler.com/2.0/"

# Output settings
output:
  directory: "output"
  history_filename: "music_history.json"
  daily_playlist_format: "playlist_{date}.json"

# Display settings
display:
  show_fetching_progress: true
  language: "fr" # fr or en
```

### Platform Filtering Configuration

Enable platform filtering to exclude tracks you've already liked on SoundCloud or Spotify:

```yaml
# Platform filtering settings
platform_filtering:
  enabled: true # Enable filtering against user's liked songs
  soundcloud:
    enabled: true # Filter against SoundCloud liked tracks
    oauth_token: "${SOUNDCLOUD_OAUTH_TOKEN}" # OAuth token from browser cookies
  spotify:
    enabled: false # Filter against Spotify liked tracks (optional)
    client_id: "${SPOTIFY_CLIENT_ID}" # Spotify app client ID
    client_secret: "${SPOTIFY_CLIENT_SECRET}" # Spotify app client secret
    access_token: "${SPOTIFY_ACCESS_TOKEN}" # User access token for liked songs
```

**Setup Instructions:**

- **SoundCloud**: See [docs/SOUNDCLOUD_OAUTH_SETUP.md](docs/SOUNDCLOUD_OAUTH_SETUP.md) for token extraction
- **Spotify**: See [docs/SPOTIFY_SETUP.md](docs/SPOTIFY_SETUP.md) for API credentials setup

### Command Line Options

- `--tags`: Override default tags (e.g., `--tags jazz blues`)
- `--num-tracks`: Override number of tracks (e.g., `--num-tracks 15`)
- `--output-dir`: Override output directory (e.g., `--output-dir playlists`)
- `--config`: Use different config file (e.g., `--config my_config.yaml`)
- `--soundcloud-token`: Provide SoundCloud OAuth token directly
- `--spotify-token`: Provide Spotify access token directly

## How it works

### Basic Workflow

1. The application fetches tracks from Last.fm for each configured tag
2. It maintains a history file (`music_history.json`) to avoid duplicate recommendations
3. **Platform Filtering** (if enabled): Excludes tracks you've already liked on connected platforms
4. For each day, it generates a new set of recommendations that haven't been suggested before
5. If recommendations for today already exist, it displays the cached results

### Platform Filtering Process

When platform filtering is enabled:

1. **Authentication**: Connects to SoundCloud/Spotify using your credentials
2. **Fetch Liked Songs**: Retrieves your liked/saved tracks from connected platforms
3. **Track Matching**: Compares Last.fm recommendations against your liked songs using fuzzy matching
4. **Filtering**: Removes any tracks that match your existing library
5. **Statistics**: Reports how many tracks were filtered and from which platforms

**Matching Algorithm:**

- Case-insensitive artist and track name comparison
- Handles variations in track titles (feat., remixes, etc.)
- Uses fuzzy string matching for slight differences
- Prioritizes artist name accuracy over track title

## Development

### Adding dependencies

```bash
# Add a new dependency
uv add package-name

# Add a development dependency
uv add --dev package-name
```

### Project structure

```
new_songs_enjoyer/
├── main.py                      # Main application code
├── run.py                       # Task runner with server command
├── web_server.py                # Flask web interface
├── config.py                    # Configuration and argument parsing
├── config.yaml                  # YAML configuration file
├── config.example.yaml          # Example configuration with all options
├── config.soundcloud-only.yaml  # Example: SoundCloud filtering only
├── config.multi-platform.yaml   # Example: Multi-platform filtering
├── pyproject.toml               # Project configuration and dependencies
├── requirements.txt             # Fallback for pip users
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
├── README.md                    # Project overview and setup
├── docs/                        # Documentation
│   ├── USAGE.md                 # Detailed usage guide and examples
│   ├── SOUNDCLOUD_OAUTH_SETUP.md # SoundCloud token extraction guide
│   ├── SPOTIFY_SETUP.md         # Spotify API setup guide
│   └── TROUBLESHOOTING.md       # Comprehensive troubleshooting guide
├── entities/                    # Data models
│   ├── track.py                 # Track entity
│   ├── playlist.py              # Playlist entity
│   └── filter_result.py         # Filtering statistics
├── adapter/                     # External API integrations
│   └── soundcloud_adapter.py    # SoundCloud API integration
├── templates/                   # HTML templates
│   └── playlist_template.html   # Playlist HTML output
├── tests/                       # Test suite
│   └── test_*.py                # Various test modules
├── output/                      # Output directory (auto-created)
│   ├── music_history.json       # History of all recommendations
│   └── playlist_YYYY-MM-DD.json # Daily playlist files
└── uv.lock                      # Dependency lock file (auto-generated)
```

## Troubleshooting

### Basic Issues

- **API Key Issues**: Make sure your `.env` file contains a valid Last.fm API key
- **Network Issues**: Check your internet connection if track fetching fails
- **Permission Issues**: Ensure the application can write to the current directory for the history file

### Platform Filtering Issues

- **SoundCloud Authentication**: See [docs/SOUNDCLOUD_OAUTH_SETUP.md](docs/SOUNDCLOUD_OAUTH_SETUP.md) for token extraction help
- **Spotify Authentication**: See [docs/SPOTIFY_SETUP.md](docs/SPOTIFY_SETUP.md) for API setup troubleshooting
- **No Filtering Applied**: Check that `platform_filtering.enabled: true` in config.yaml
- **Partial Filtering**: Some platforms may fail while others work - check logs for details

For comprehensive troubleshooting, see [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

## 📜 License

This project is licensed under the Business Source License 1.1 (BUSL-1.1).
You may use this code for **non-commercial purposes only** (e.g., personal, academic).
**Commercial use is prohibited** unless explicitly authorized by the author.

➡️ See [LICENSE.md](./LICENSE.md) for full terms.
