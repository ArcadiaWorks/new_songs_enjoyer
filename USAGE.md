# Usage Guide for new_songs_enjoyer

This guide provides detailed examples and usage instructions for the new_songs_enjoyer music recommendation system.

## Basic Usage

### Run with Default Settings

```bash
# Use configuration from config.yaml
uv run python main.py

# Or use the installed script
uv run new-songs-enjoyer
```

### Quick Start with Custom Tags

```bash
# Generate recommendations for jazz and blues
uv run python main.py --tags jazz blues

# Electronic music with more tracks
uv run python main.py --tags electronic ambient techno --num-tracks 30
```

## Command Line Arguments

### Tags Selection

```bash
# Single tag
uv run python main.py --tags chill

# Multiple tags
uv run python main.py --tags jazz blues rock classical

# Genre exploration
uv run python main.py --tags "indie rock" alternative "post rock"
```

### Output Configuration

```bash
# Custom output directory
uv run python main.py --output-dir my_playlists

# Specific number of tracks
uv run python main.py --num-tracks 15

# Combine output options
uv run python main.py --tags lofi --num-tracks 25 --output-dir chill_music
```

### Configuration Management

```bash
# Use custom config file
uv run python main.py --config production_config.yaml

# Override config with arguments
uv run python main.py --config minimal_config.yaml --tags "drum and bass" --num-tracks 20
```

### Logging Control

```bash
# Verbose logging
uv run python main.py --log-level DEBUG

# Quiet mode (errors only)
uv run python main.py --log-level ERROR

# Standard logging
uv run python main.py --log-level INFO
```

## Advanced Usage Examples

### Daily Workflow

```bash
# Morning chill session
uv run python main.py --tags chill ambient "lo-fi hip hop" --num-tracks 20 --output-dir morning_playlist

# Work focus music
uv run python main.py --tags instrumental "post rock" ambient --num-tracks 15 --output-dir work_music

# Evening exploration
uv run python main.py --tags jazz "experimental" "new wave" --num-tracks 10 --output-dir evening_discovery
```

### Genre-Specific Playlists

```bash
# Electronic music exploration
uv run python main.py --tags electronic techno house "drum and bass" --num-tracks 25 --output-dir electronic

# Rock and alternative
uv run python main.py --tags rock alternative indie "post punk" --num-tracks 20 --output-dir rock

# World music discovery
uv run python main.py --tags world reggae afrobeat bossa --num-tracks 15 --output-dir world_music
```

### Development and Testing

```bash
# Debug mode with verbose logging
uv run python main.py --log-level DEBUG --tags test --num-tracks 5 --output-dir debug_output

# Test configuration
uv run python main.py --config test_config.yaml --log-level DEBUG

# Quick validation (minimal tracks)
uv run python main.py --tags ambient --num-tracks 3 --log-level WARNING
```

## Traditional Python Environment

If you prefer using pip instead of uv:

```bash
# Activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py --tags chill ambient --num-tracks 15
```

## Environment Setup Examples

### Development Environment

```bash
# Create development environment
uv sync

# Run with debug logging
uv run python main.py --log-level DEBUG --tags "indie rock" --num-tracks 5
```

### Production Environment

```bash
# Use production config
uv run python main.py --config production.yaml --log-level WARNING

# Automated daily run
uv run python main.py --log-level ERROR --output-dir /data/daily_playlists
```

## Output Structure Examples

After running commands, you'll find files organized like this:

```
output/
├── music_history.json           # Global history across all days
├── playlist_2025-07-12.json    # Today's playlist
├── playlist_2025-07-11.json    # Yesterday's playlist
└── ...

# With custom output directory:
my_playlists/
├── music_history.json
├── playlist_2025-07-12.json
└── ...
```

## Common Use Cases

### 1. Daily Music Discovery

```bash
# Create your daily discovery routine
uv run python main.py --tags "new music" indie experimental --num-tracks 20
```

### 2. Mood-Based Playlists

```bash
# Relaxing evening
uv run python main.py --tags chill ambient "lo-fi" --num-tracks 30 --output-dir relaxing

# Energetic workout
uv run python main.py --tags electronic "drum and bass" techno --num-tracks 25 --output-dir workout
```

### 3. Genre Deep Dive

```bash
# Explore jazz subgenres
uv run python main.py --tags jazz bebop "cool jazz" fusion --num-tracks 15 --output-dir jazz_exploration
```

### 4. Custom Configuration

Create `my_config.yaml`:
```yaml
default_tags: ["shoegaze", "dream pop", "ambient"]
num_tracks: 25
output:
  directory: "dreamy_music"
  daily_playlist_format: "dreams_{date}.json"
display:
  language: "en"
logging:
  level: "WARNING"
```

Then run:
```bash
uv run python main.py --config my_config.yaml
```

## Troubleshooting Commands

```bash
# Check if API key is working
uv run python main.py --tags ambient --num-tracks 1 --log-level DEBUG

# Reset today's recommendations (delete output/music_history.json first)
rm output/music_history.json
uv run python main.py --tags chill --num-tracks 10

# Test with minimal output
uv run python main.py --tags test --num-tracks 1 --log-level ERROR
```

## Integration Examples

### Shell Scripts

Create `daily_music.sh`:
```bash
#!/bin/bash
echo "Generating daily music recommendations..."
uv run python main.py --tags chill ambient lofi --num-tracks 20 --log-level WARNING
echo "Check output/ directory for your playlist!"
```

### Cron Job

```bash
# Add to crontab for daily 9 AM recommendations
0 9 * * * cd /path/to/new_songs_enjoyer && uv run python main.py --tags chill ambient --num-tracks 15 --log-level ERROR
```

## Help and Documentation

```bash
# Show all available options
uv run python main.py --help

# Check version and dependencies
uv run python -c "import main; print('Application ready')"
