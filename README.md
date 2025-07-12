# new_songs_enjoyer

Crafts you a playlist to discover new songs based on preferences using the Last.fm API.

## Features

- 🎵 Fetches tracks from Last.fm based on configurable tags (chill, ambient, lofi)
- 📅 Daily recommendations with duplicate prevention
- 📝 Maintains history of previously suggested tracks
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

```bash
# Install dependencies
uv sync

# Run with default settings
uv run python main.py

# Run with custom tags
uv run python main.py --tags jazz blues --num-tracks 15
```

For detailed usage instructions, examples, and advanced configuration, see **[USAGE.md](USAGE.md)**.

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
  language: "fr"  # fr or en
```

### Command Line Options

- `--tags`: Override default tags (e.g., `--tags jazz blues`)
- `--num-tracks`: Override number of tracks (e.g., `--num-tracks 15`)
- `--output-dir`: Override output directory (e.g., `--output-dir playlists`)
- `--config`: Use different config file (e.g., `--config my_config.yaml`)

## How it works

1. The application fetches tracks from Last.fm for each configured tag
2. It maintains a history file (`music_history.json`) to avoid duplicate recommendations
3. For each day, it generates a new set of recommendations that haven't been suggested before
4. If recommendations for today already exist, it displays the cached results

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
├── main.py              # Main application code
├── config.py            # Configuration and argument parsing
├── config.yaml          # YAML configuration file
├── pyproject.toml       # Project configuration and dependencies
├── requirements.txt     # Fallback for pip users
├── .env.example         # Environment variables template
├── .gitignore          # Git ignore rules
├── README.md           # Project overview and setup
├── USAGE.md            # Detailed usage guide and examples
├── output/             # Output directory (auto-created)
│   ├── music_history.json      # History of all recommendations
│   └── playlist_YYYY-MM-DD.json # Daily playlist files
└── uv.lock             # Dependency lock file (auto-generated)
```

## Troubleshooting

- **API Key Issues**: Make sure your `.env` file contains a valid Last.fm API key
- **Network Issues**: Check your internet connection if track fetching fails
- **Permission Issues**: Ensure the application can write to the current directory for the history file

## 📜 License

This project is licensed under the Business Source License 1.1 (BUSL-1.1).
You may use this code for **non-commercial purposes only** (e.g., personal, academic).
**Commercial use is prohibited** unless explicitly authorized by the author.

➡️ See [LICENSE.md](./LICENSE.md) for full terms.
