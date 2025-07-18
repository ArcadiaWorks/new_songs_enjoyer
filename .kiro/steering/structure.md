# Project Structure

## Root Directory Layout

```
new_songs_enjoyer/
├── main.py                 # Main application entry point
├── config.py              # Configuration management and CLI parsing
├── run.py                 # Task runner (alternative to make/just)
├── web_server.py          # Flask web interface for SoundCloud integration
├── config.yaml            # Application configuration
├── .env                   # Environment variables (API keys)
├── .env.example           # Environment template
├── pyproject.toml         # Python project configuration
├── requirements.txt       # Pip fallback dependencies
├── uv.lock               # Dependency lock file
└── README.md             # Main documentation
```

## Core Modules

### `/entities/` - Data Models
- `track.py` - Track entity with Last.fm data parsing
- `playlist.py` - Playlist and metadata entities
- `api_response.py` - Last.fm API response wrapper
- `__init__.py` - Package exports

### `/adapter/` - External Integrations
- `soundcloud_adapter.py` - SoundCloud API integration
- `__init__.py` - Package exports

### `/templates/` - HTML Templates
- `playlist_template.html` - Jinja2 template for playlist HTML output

### `/tests/` - Test Suite
- `test_*.py` - Various test modules
- `run_tests.py` - Test runner

## Generated Content

### `/output/` - Generated Files
- `music_history.json` - Track history for duplicate prevention
- `playlist_YYYY-MM-DD_HH-MM-SS.json` - JSON playlist files
- `playlist_YYYY-MM-DD_HH-MM-SS.html` - HTML playlist files

## Architecture Patterns

### Entity-Adapter Pattern
- **Entities**: Pure data models with validation and serialization
- **Adapters**: External service integrations (SoundCloud, Last.fm)
- **Main**: Orchestration and business logic

### Configuration Hierarchy
1. Default values in `config.py`
2. YAML file overrides (`config.yaml`)
3. Command-line argument overrides
4. Environment variables for secrets

### File Naming Conventions
- Snake_case for Python files and variables
- Timestamped output files: `playlist_YYYY-MM-DD_HH-MM-SS.{json,html}`
- Configuration files use lowercase with extensions

### Import Structure
- Relative imports within packages (`from .track import Track`)
- Absolute imports for cross-package dependencies
- Main modules import from package `__init__.py` files

## Development Guidelines

- Keep main.py focused on orchestration
- Business logic in dedicated modules
- Configuration centralized in config.py
- All external API calls go through adapter classes
- HTML generation uses Jinja2 templates
- JSON serialization handled by entity `to_dict()` methods