# Requirements Document

## Introduction

This feature adds music platform integration to the new_songs_enjoyer application to filter out tracks that are already in the user's liked songs before generating daily playlists. The primary focus is Spotify integration via their official API, with optional SoundCloud support using OAuth tokens extracted from user cookies (since SoundCloud's public API is discontinued). This prevents the system from recommending music the user has already discovered and saved, ensuring fresh recommendations every time.

## Requirements

### Requirement 1

**User Story:** As a music discovery user, I want to connect my Spotify or SoundCloud account so that the system can access my liked songs to filter recommendations.

#### Acceptance Criteria

1. WHEN a user provides their Spotify profile URL via command line THEN the system SHALL authenticate with Spotify API to access their liked songs
2. WHEN a user provides their Spotify profile URL via web interface THEN the system SHALL authenticate with Spotify API to access their liked songs
3. WHEN a user provides their SoundCloud OAuth token via command line THEN the system SHALL use the token to access their liked tracks
4. WHEN a user provides their SoundCloud OAuth token via web interface THEN the system SHALL use the token to access their liked tracks
5. IF authentication fails for the chosen platform THEN the system SHALL display a clear error message and continue without filtering
6. WHEN authentication succeeds THEN the system SHALL store the access credentials securely for the session
7. WHEN both Spotify and SoundCloud credentials are provided THEN the system SHALL use both platforms for filtering
8. WHEN SoundCloud integration is requested THEN the system SHALL provide clear instructions on how to extract OAuth token from browser cookies

### Requirement 2

**User Story:** As a music discovery user, I want the system to automatically exclude tracks I've already liked on my connected music platforms from my daily recommendations.

#### Acceptance Criteria

1. WHEN generating a playlist THEN the system SHALL fetch the user's liked songs from all connected platforms before searching Last.fm
2. WHEN comparing tracks THEN the system SHALL match tracks by artist name and track title (case-insensitive)
3. IF a Last.fm track matches a liked song from any connected platform THEN the system SHALL exclude it from the final playlist
4. WHEN no platform connections are available THEN the system SHALL generate playlists normally without filtering
5. WHEN API rate limits are hit for any platform THEN the system SHALL log a warning and continue with partial filtering

### Requirement 3

**User Story:** As a user, I want to configure music platform integration settings so that I can control how the filtering works.

#### Acceptance Criteria

1. WHEN configuring the application THEN the user SHALL be able to enable/disable platform filtering via config.yaml
2. WHEN configuring the application THEN the user SHALL be able to set Spotify client credentials via environment variables
3. WHEN configuring the application THEN the user SHALL be able to set SoundCloud client credentials via environment variables
4. IF platform filtering is disabled THEN the system SHALL skip all platform API calls and filtering logic
5. WHEN platform filtering is enabled but no credentials are provided THEN the system SHALL display a configuration error

### Requirement 4

**User Story:** As a user, I want to see transparency about how many tracks were filtered out so I understand the impact of platform filtering.

#### Acceptance Criteria

1. WHEN generating a playlist with platform filtering THEN the system SHALL log the number of tracks filtered out per platform
2. WHEN displaying playlist results THEN the system SHALL show statistics about platform filtering in the output
3. WHEN no tracks are filtered THEN the system SHALL indicate that no duplicates were found
4. WHEN platform filtering fails partially THEN the system SHALL indicate the filtering was incomplete

### Requirement 5

**User Story:** As a developer, I want the Spotify integration to follow the existing architecture patterns so it's maintainable and consistent.

#### Acceptance Criteria

1. WHEN implementing Spotify integration THEN the system SHALL use the adapter pattern similar to SoundCloud integration
2. WHEN handling Spotify API responses THEN the system SHALL create appropriate entity models for Spotify data
3. WHEN storing Spotify configuration THEN the system SHALL follow the existing configuration hierarchy (config.yaml, .env, CLI args)
4. WHEN handling Spotify errors THEN the system SHALL use the existing logging and error handling patterns