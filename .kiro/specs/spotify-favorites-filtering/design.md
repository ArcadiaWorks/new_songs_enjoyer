# Design Document

## Overview

This design extends the new_songs_enjoyer application to integrate with SoundCloud (and optionally Spotify) to filter out tracks that users have already liked/saved before generating daily playlists. The primary focus is leveraging the existing SoundCloud adapter to fetch user's liked tracks, with Spotify as an additional option. The solution follows the existing adapter pattern and configuration hierarchy while adding new filtering capabilities to the playlist generation workflow.

## Architecture

### High-Level Flow

1. User provides SoundCloud OAuth token (from browser cookies) via CLI/web interface
2. System uses existing SoundCloud adapter to fetch user's liked tracks
3. During playlist generation, system filters out any Last.fm tracks that match SoundCloud favorites
4. Final playlist contains only fresh recommendations not already in user's library
5. Optional: Spotify integration as secondary filtering source

### Integration Points

- **Configuration Layer**: Extends existing config.py and config.yaml with filtering settings
- **Adapter Layer**: Extends existing SoundCloudAdapter with liked tracks functionality
- **Main Orchestration**: Modifies main.py playlist generation to include filtering step
- **Web Interface**: Extends web_server.py with OAuth token input and filtering UI

## Components and Interfaces

### 1. Extended SoundCloudAdapter Methods

```python
class SoundCloudAdapter:
    """Extended with liked tracks functionality."""

    def get_user_liked_tracks(self, limit: int = 200) -> List[SoundCloudTrack]
    def get_user_profile(self) -> Optional[Dict[str, Any]]
    def _normalize_track_for_matching(self, track: SoundCloudTrack) -> Track
```

### 2. Optional SpotifyAdapter Class

```python
class SpotifyAdapter:
    """Optional Spotify Web API integration."""

    def __init__(self, client_id: str, client_secret: str)

    @classmethod
    def from_env(cls) -> "SpotifyAdapter"

    def authenticate_with_client_credentials(self) -> bool
    def get_user_liked_tracks(self, access_token: str, limit: int = 50) -> List[SpotifyTrack]
```

### 3. PlatformFilter Class

```python
class PlatformFilter:
    """Handles filtering tracks against music platforms."""

    def __init__(self, soundcloud_adapter: Optional[SoundCloudAdapter] = None,
                 spotify_adapter: Optional[SpotifyAdapter] = None)

    def filter_tracks(self, tracks: List[Track]) -> FilterResult
    def get_soundcloud_favorites(self) -> List[Track]
    def get_spotify_favorites(self, access_token: str) -> List[Track]
    def _match_tracks(self, lastfm_track: Track, platform_tracks: List[Track]) -> bool
```

### 4. FilterResult Entity

```python
@dataclass
class FilterResult:
    """Result of platform filtering operation."""

    original_count: int
    filtered_tracks: List[Track]
    removed_tracks: List[Track]
    soundcloud_matches: int
    spotify_matches: int
    errors: List[str]
```

## Data Models

### Configuration Extensions

**config.yaml additions:**

```yaml
platform_filtering:
  enabled: true
  soundcloud:
    enabled: true
    oauth_token: "${SOUNDCLOUD_OAUTH_TOKEN}"
  spotify:
    enabled: false
    client_id: "${SPOTIFY_CLIENT_ID}"
    client_secret: "${SPOTIFY_CLIENT_SECRET}"
    access_token: "${SPOTIFY_ACCESS_TOKEN}"
```

**Environment Variables:**

```
SOUNDCLOUD_OAUTH_TOKEN=your_soundcloud_oauth_token_from_cookies
SPOTIFY_CLIENT_ID=optional_spotify_client_id
SPOTIFY_CLIENT_SECRET=optional_spotify_client_secret
SPOTIFY_ACCESS_TOKEN=optional_spotify_user_access_token
```

### Track Matching Algorithm

Tracks are matched using fuzzy string comparison:

1. **Exact Match**: Artist + Track name (case-insensitive)
2. **Partial Match**: Levenshtein distance < 0.8 threshold
3. **Artist Priority**: Higher weight on artist name matching
4. **Normalization**: Remove special characters, "feat.", parentheses

## Error Handling

### SoundCloud Integration

- **Missing OAuth Token**: Skip SoundCloud filtering, log info message
- **Invalid Token**: Clear instructions for token extraction from browser cookies
- **API Limitations**: Handle read-only tokens gracefully, continue with available data
- **Rate Limiting**: Implement exponential backoff, partial filtering
- **Network Errors**: Retry with timeout, graceful degradation

### Optional Spotify API Errors

- **Authentication Failure**: Log warning, continue with SoundCloud-only filtering
- **Missing Credentials**: Skip Spotify filtering, use SoundCloud only
- **Rate Limiting**: Implement exponential backoff, partial filtering
- **Network Errors**: Retry with timeout, graceful degradation

### Filtering Errors

- **No Platform Available**: Continue with normal playlist generation
- **Partial Failures**: Log warnings, use available platform data
- **Empty Results**: Inform user, suggest checking credentials

## Testing Strategy

### Unit Tests

- **SoundCloudAdapter Extensions**: Mock API responses for liked tracks endpoint
- **PlatformFilter**: Test filtering logic with various track combinations
- **Track Matching**: Test fuzzy matching algorithm accuracy with SoundCloud data
- **Configuration**: Test config loading and validation

### Integration Tests

- **End-to-End Filtering**: Test complete workflow with real SoundCloud OAuth token
- **Web Interface**: Test OAuth token input and filtering UI
- **Error Scenarios**: Test graceful handling of API failures

### Manual Testing

- **SoundCloud OAuth**: Test with real OAuth tokens from browser cookies
- **Track Filtering**: Verify accuracy with known SoundCloud liked songs
- **Performance**: Test with large SoundCloud libraries (1000+ tracks)

## Implementation Phases

### Phase 1: Core SoundCloud Filtering

- Extend existing SoundCloudAdapter with liked tracks functionality
- Track matching algorithm implementation
- Configuration extensions for platform filtering
- CLI argument support for SoundCloud OAuth token

### Phase 2: Filtering Integration

- PlatformFilter class implementation
- Integration with main playlist generation workflow
- FilterResult entity and statistics tracking

### Phase 3: Web Interface Enhancement

- SoundCloud OAuth token input in web form
- Instructions for token extraction from browser cookies
- Results display with filtering statistics

### Phase 4: Optional Spotify Integration

- SpotifyAdapter implementation as secondary platform
- Spotify authentication and liked songs fetching
- Multi-platform filtering support

## Security Considerations

### API Credentials

- Store client credentials in environment variables only
- Never log or expose access tokens
- Use HTTPS for all API communications
- Implement token refresh mechanism

### User Data

- Don't store user's liked songs permanently
- Clear sensitive data after session
- Respect Spotify's rate limits and terms of service
- Provide clear privacy information to users

## Performance Considerations

### API Efficiency

- Batch requests where possible (Spotify supports up to 50 tracks per request)
- Cache liked songs for session duration
- Implement pagination for large libraries
- Use parallel requests for multiple platforms

### Memory Usage

- Stream large playlists instead of loading all in memory
- Implement lazy loading for liked songs
- Clean up temporary data structures

### Response Times

- Set reasonable timeouts for API calls (10-30 seconds)
- Implement async operations where beneficial
- Provide progress indicators for long operations

## Monitoring and Logging

### Metrics to Track

- Number of tracks filtered per platform
- API response times and error rates
- User authentication success rates
- Filtering accuracy (manual validation)

### Log Levels

- **INFO**: Successful filtering operations, track counts
- **WARNING**: API rate limits, partial failures
- **ERROR**: Authentication failures, network errors
- **DEBUG**: Detailed API responses, matching decisions
