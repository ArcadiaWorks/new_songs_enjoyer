# Implementation Plan

- [x] 1. Extend SoundCloudAdapter with liked tracks functionality

  - Add `get_user_liked_tracks()` method to fetch user's liked songs from SoundCloud API
  - Add `get_user_profile()` method to validate OAuth token and get user info
  - Add `_normalize_track_for_matching()` method to convert SoundCloudTrack to Track format
  - Write unit tests for new SoundCloudAdapter methods with mocked API responses
  - _Requirements: 1.3, 1.4, 2.1_

- [x] 2. Create PlatformFilter class for track filtering logic

  - Implement PlatformFilter class with constructor accepting SoundCloudAdapter
  - Add `filter_tracks()` method that removes tracks matching SoundCloud favorites
  - Add `get_soundcloud_favorites()` method to fetch and cache liked tracks
  - Add `_match_tracks()` method with fuzzy string matching algorithm (case-insensitive artist/title comparison)
  - Write unit tests for filtering logic with various track combinations
  - _Requirements: 2.2, 2.3_

- [x] 3. Create FilterResult entity for tracking filtering statistics

  - Implement FilterResult dataclass with original_count, filtered_tracks, removed_tracks fields
  - Add soundcloud_matches, spotify_matches, and errors fields for statistics
  - Add `to_dict()` method for JSON serialization
  - Write unit tests for FilterResult entity creation and serialization
  - _Requirements: 4.1, 4.2, 4.3_

- [x] 4. Extend configuration system for platform filtering

  - Add platform_filtering section to config.yaml with soundcloud and spotify subsections
  - Update config.py to load and validate platform filtering configuration
  - Add CLI arguments for --soundcloud-token and --spotify-token parameters
  - Update environment variable loading for SOUNDCLOUD_OAUTH_TOKEN
  - Write unit tests for configuration loading and CLI argument parsing
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 5. Integrate filtering into main playlist generation workflow

  - Modify main.py to create PlatformFilter instance when filtering is enabled
  - Add filtering step before track selection in `create_playlist()` function
  - Update playlist generation to use FilterResult and log filtering statistics
  - Ensure graceful fallback when no platform credentials are available
  - Write integration tests for complete filtering workflow
  - _Requirements: 2.1, 2.4, 2.5_

- [x] 6. Add filtering statistics to playlist output

  - Update Playlist entity to include filtering statistics in metadata
  - Modify `display_playlist()` function to show filtering results
  - Update HTML template to display filtering statistics
  - Add filtering info to JSON playlist output
  - Write tests for statistics display in various output formats
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 7. Enhance web interface with SoundCloud OAuth token input

  - Add SoundCloud OAuth token input field to playlist generation form
  - Add instructions and help text for extracting token from browser cookies
  - Update `/api/generate` endpoint to accept and use SoundCloud token parameter
  - Add filtering statistics display to web interface results
  - Write tests for web interface token handling and filtering display
  - _Requirements: 1.4, 1.8_

- [x] 8. Implement error handling and logging for filtering operations

  - Add comprehensive error handling for SoundCloud API failures
  - Implement graceful degradation when filtering partially fails
  - Add detailed logging for filtering operations and statistics
  - Add user-friendly error messages for common failure scenarios
  - Write tests for error handling scenarios and logging output
  - _Requirements: 2.5, 3.4_

- [ ] 9. Add optional Spotify integration as secondary platform

  - Create SpotifyAdapter class with client credentials authentication
  - Add `get_user_liked_tracks()` method for Spotify Web API
  - Extend PlatformFilter to support both SoundCloud and Spotify filtering
  - Update configuration to support optional Spotify credentials
  - Write unit tests for SpotifyAdapter and multi-platform filtering
  - _Requirements: 1.1, 1.2, 1.7_

- [x] 10. Create comprehensive documentation and setup instructions

  - Write documentation for SoundCloud OAuth token extraction from browser cookies
  - Add setup instructions for optional Spotify integration
  - Update README.md with filtering feature documentation
  - Create troubleshooting guide for common filtering issues
  - Add example configuration files with filtering settings
  - _Requirements: 1.8, 3.4_
