# Product Overview

**new_songs_enjoyer** is a music discovery tool that generates daily playlists based on Last.fm API data and user preferences.

## Core Features

- **Daily Music Recommendations**: Fetches tracks from Last.fm using configurable tags (chill, ambient, lofi, etc.)
- **Duplicate Prevention**: Maintains history to avoid recommending previously suggested tracks
- **Multi-format Output**: Generates both JSON and HTML playlist files
- **SoundCloud Integration**: Optional adapter for importing playlists to SoundCloud
- **Web Interface**: Flask-based server for playlist generation and SoundCloud import
- **Internationalization**: Supports French and English interfaces

## Key Value Propositions

- Automated music discovery based on user-defined genres/moods
- Prevents repetition through intelligent history tracking
- Beautiful HTML playlist presentation with embedded SoundCloud players
- Seamless integration with SoundCloud for playlist management
- Configurable parameters (tags, track count, API limits)

## Target Use Cases

- Personal music discovery and curation
- Daily playlist generation for specific moods or genres
- SoundCloud playlist management and automation
- Music exploration based on Last.fm's extensive tag system