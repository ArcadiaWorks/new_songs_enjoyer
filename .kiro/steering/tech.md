# Technology Stack

## Core Technologies

- **Python 3.8+**: Main programming language
- **uv**: Modern Python package manager for dependency management
- **Flask**: Web framework for SoundCloud integration interface
- **Requests**: HTTP client for Last.fm and SoundCloud API calls
- **PyYAML**: Configuration file parsing
- **Jinja2**: HTML template rendering for playlist output
- **python-dotenv**: Environment variable management

## Build System & Package Management

- **uv**: Primary package manager (preferred over pip)
- **pyproject.toml**: Modern Python project configuration
- **requirements.txt**: Fallback for pip compatibility
- **uv.lock**: Dependency lock file for reproducible builds

## Common Commands

### Development Setup
```bash
# Install uv package manager first
curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS/Linux
# or
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# Install dependencies
uv sync

# Run application
uv run python main.py
```

### Task Runner
```bash
# Use run.py for common tasks (alternative to make/just)
python run.py setup          # Initial setup
python run.py generate       # Generate playlist
python run.py server         # Start web server
python run.py clean          # Clean cache files
python run.py help           # Show all commands
```

### Configuration
- Environment variables in `.env` file (copy from `.env.example`)
- Application settings in `config.yaml`
- Command-line argument overrides supported

## API Integrations

- **Last.fm API**: Music data source (requires API key)
- **SoundCloud API v2**: Playlist import (requires OAuth token)
- Both APIs use OAuth/API key authentication stored in `.env`

## Development Practices

- Use dataclasses for entity models
- Comprehensive logging with configurable levels
- Error handling with graceful degradation
- Type hints encouraged but not strictly enforced
- Modular architecture with clear separation of concerns