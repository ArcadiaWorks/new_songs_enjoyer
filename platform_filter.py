"""PlatformFilter class for filtering tracks against music platforms."""

import logging
from typing import List, Optional, Set
import difflib
import re
import time
from requests.exceptions import RequestException, Timeout, ConnectionError

from entities import Track, FilterResult
from adapter.soundcloud_adapter import SoundCloudAdapter, SoundCloudTrack

logger = logging.getLogger(__name__)


class PlatformFilterError(Exception):
    """Base exception for platform filtering errors."""

    pass


class SoundCloudAPIError(PlatformFilterError):
    """Exception for SoundCloud API related errors."""

    pass


class FilteringTimeoutError(PlatformFilterError):
    """Exception for filtering operation timeouts."""

    pass


class PlatformFilter:
    """Handles filtering tracks against music platforms."""

    def __init__(self, soundcloud_adapter: Optional[SoundCloudAdapter] = None):
        """Initialize PlatformFilter with optional SoundCloud adapter.

        Args:
            soundcloud_adapter: Optional SoundCloudAdapter for fetching liked tracks
        """
        self.soundcloud_adapter = soundcloud_adapter
        self._soundcloud_favorites_cache: Optional[List[Track]] = None

    def filter_tracks(self, tracks: List[Track]) -> FilterResult:
        """Remove tracks matching SoundCloud favorites.

        Args:
            tracks: List of tracks to filter

        Returns:
            FilterResult with filtering statistics and results
        """
        if not tracks:
            logger.warning("No tracks provided for filtering")
            return FilterResult.create_empty([])

        logger.info(f"Starting platform filtering for {len(tracks)} tracks")
        start_time = time.time()

        original_count = len(tracks)
        filtered_tracks = []
        removed_tracks = []
        soundcloud_matches = 0
        spotify_matches = 0  # Not implemented yet
        errors = []

        try:
            # Validate input tracks
            if not all(isinstance(track, Track) for track in tracks):
                error_msg = "Invalid track objects provided for filtering"
                logger.error(error_msg)
                errors.append(error_msg)
                return FilterResult.create_empty(tracks)

            # Get SoundCloud favorites if adapter is available
            soundcloud_favorites = []
            if self.soundcloud_adapter:
                try:
                    logger.debug("Attempting to fetch SoundCloud favorites")
                    soundcloud_favorites = self.get_soundcloud_favorites()

                    if soundcloud_favorites:
                        logger.info(
                            f"Successfully loaded {len(soundcloud_favorites)} SoundCloud favorites for filtering"
                        )
                    else:
                        logger.warning(
                            "No SoundCloud favorites found or could not fetch them"
                        )

                except SoundCloudAPIError as e:
                    error_msg = (
                        f"SoundCloud API error while fetching favorites: {str(e)}"
                    )
                    logger.error(error_msg)
                    errors.append(
                        "Unable to connect to SoundCloud. Please check your OAuth token."
                    )

                except FilteringTimeoutError as e:
                    error_msg = f"Timeout while fetching SoundCloud favorites: {str(e)}"
                    logger.error(error_msg)
                    errors.append(
                        "SoundCloud request timed out. Please try again later."
                    )

                except Exception as e:
                    error_msg = (
                        f"Unexpected error fetching SoundCloud favorites: {str(e)}"
                    )
                    logger.error(error_msg, exc_info=True)
                    errors.append(
                        "Failed to fetch SoundCloud favorites due to an unexpected error."
                    )

            # Perform filtering if we have favorites
            if soundcloud_favorites:
                logger.info(
                    f"Filtering {len(tracks)} tracks against {len(soundcloud_favorites)} SoundCloud favorites"
                )

                try:
                    for i, track in enumerate(tracks):
                        try:
                            if self._match_tracks(track, soundcloud_favorites):
                                removed_tracks.append(track)
                                soundcloud_matches += 1
                                logger.debug(
                                    f"Removed SoundCloud match: {track.name} by {track.artist}"
                                )
                            else:
                                filtered_tracks.append(track)

                            # Log progress for large track lists
                            if len(tracks) > 100 and (i + 1) % 50 == 0:
                                logger.debug(
                                    f"Processed {i + 1}/{len(tracks)} tracks for filtering"
                                )

                        except Exception as e:
                            logger.warning(f"Error matching track '{track}': {str(e)}")
                            # Include track in filtered list if matching fails
                            filtered_tracks.append(track)
                            errors.append(
                                f"Could not process track: {track.name} by {track.artist}"
                            )

                except Exception as e:
                    error_msg = f"Error during track matching process: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    errors.append("Track matching process failed unexpectedly.")
                    # Fall back to returning all tracks
                    filtered_tracks = tracks.copy()
                    removed_tracks = []
                    soundcloud_matches = 0

            else:
                # No SoundCloud favorites available, return all tracks
                logger.debug("No SoundCloud favorites available, returning all tracks")
                filtered_tracks = tracks.copy()

                if self.soundcloud_adapter and not errors:
                    # Only add this error if we haven't already logged specific errors
                    errors.append("Could not fetch SoundCloud favorites")

        except Exception as e:
            error_msg = f"Critical error during platform filtering: {str(e)}"
            logger.error(error_msg, exc_info=True)
            errors.append("Platform filtering failed due to a critical error.")
            # Return original tracks if filtering fails completely
            filtered_tracks = tracks.copy()
            removed_tracks = []
            soundcloud_matches = 0

        # Calculate processing time
        processing_time = time.time() - start_time
        logger.info(f"Platform filtering completed in {processing_time:.2f} seconds")

        # Create result with comprehensive error handling
        try:
            result = FilterResult(
                original_count=original_count,
                filtered_tracks=filtered_tracks,
                removed_tracks=removed_tracks,
                soundcloud_matches=soundcloud_matches,
                spotify_matches=spotify_matches,
                errors=errors,
            )
        except Exception as e:
            logger.error(f"Error creating FilterResult: {str(e)}")
            # Return a safe fallback result
            result = FilterResult.create_empty(tracks)
            result.add_error("Failed to create filtering result")

        # Log comprehensive results
        if result.has_filtering_applied():
            logger.info(
                f"Platform filtering results: {len(result.filtered_tracks)}/{original_count} tracks remaining "
                f"({len(result.removed_tracks)} removed, {result.get_removal_percentage():.1f}% filtered)"
            )
            logger.info(f"SoundCloud matches: {soundcloud_matches}")
        else:
            logger.info("No tracks were filtered - all tracks passed through")

        if errors:
            logger.warning(f"Platform filtering completed with {len(errors)} errors")
            for error in errors:
                logger.warning(f"  - {error}")
        else:
            logger.info("Platform filtering completed successfully without errors")

        return result

    def get_soundcloud_favorites(self) -> List[Track]:
        """Fetch and cache liked tracks from SoundCloud.

        Returns:
            List of Track objects representing SoundCloud favorites

        Raises:
            SoundCloudAPIError: When SoundCloud API requests fail
            FilteringTimeoutError: When requests timeout
        """
        if not self.soundcloud_adapter:
            logger.debug("No SoundCloud adapter available for fetching favorites")
            return []

        # Return cached favorites if available
        if self._soundcloud_favorites_cache is not None:
            cache_size = len(self._soundcloud_favorites_cache)
            logger.debug(f"Using cached SoundCloud favorites ({cache_size} tracks)")
            return self._soundcloud_favorites_cache

        start_time = time.time()
        logger.info("Fetching SoundCloud liked tracks from API")

        try:
            # Validate adapter has required token
            if (
                not hasattr(self.soundcloud_adapter, "oauth_token")
                or not self.soundcloud_adapter.oauth_token
            ):
                error_msg = "SoundCloud adapter missing OAuth token"
                logger.error(error_msg)
                raise SoundCloudAPIError(error_msg)

            # Test connection with user profile first
            try:
                logger.debug("Validating SoundCloud OAuth token")
                profile = self.soundcloud_adapter.get_user_profile()
                if not profile:
                    error_msg = (
                        "Invalid SoundCloud OAuth token - could not fetch user profile"
                    )
                    logger.error(error_msg)
                    raise SoundCloudAPIError(error_msg)
                else:
                    username = profile.get("username", "Unknown")
                    logger.info(
                        f"Successfully authenticated with SoundCloud as user: {username}"
                    )
            except Exception as e:
                if "401" in str(e) or "403" in str(e):
                    error_msg = "SoundCloud OAuth token is invalid or expired"
                    logger.error(error_msg)
                    raise SoundCloudAPIError(error_msg)
                elif "timeout" in str(e).lower():
                    error_msg = "SoundCloud authentication request timed out"
                    logger.error(error_msg)
                    raise FilteringTimeoutError(error_msg)
                else:
                    logger.warning(
                        f"Could not validate SoundCloud token, proceeding anyway: {e}"
                    )

            # Fetch liked tracks with timeout and retry logic
            max_retries = 3
            retry_delay = 1.0
            soundcloud_tracks = []

            for attempt in range(max_retries):
                try:
                    logger.debug(
                        f"Fetching SoundCloud liked tracks (attempt {attempt + 1}/{max_retries})"
                    )
                    soundcloud_tracks = self.soundcloud_adapter.get_user_liked_tracks(
                        limit=500
                    )
                    break  # Success, exit retry loop

                except (RequestException, ConnectionError, Timeout) as e:
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"SoundCloud API request failed (attempt {attempt + 1}), retrying in {retry_delay}s: {e}"
                        )
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        error_msg = f"SoundCloud API request failed after {max_retries} attempts: {e}"
                        logger.error(error_msg)
                        raise SoundCloudAPIError(error_msg)

                except Exception as e:
                    if "timeout" in str(e).lower():
                        if attempt < max_retries - 1:
                            logger.warning(
                                f"SoundCloud request timed out (attempt {attempt + 1}), retrying: {e}"
                            )
                            time.sleep(retry_delay)
                            retry_delay *= 2
                        else:
                            error_msg = f"SoundCloud requests timed out after {max_retries} attempts"
                            logger.error(error_msg)
                            raise FilteringTimeoutError(error_msg)
                    else:
                        # Re-raise unexpected errors immediately
                        raise

            if not soundcloud_tracks:
                logger.warning("No liked tracks found in SoundCloud account")
                self._soundcloud_favorites_cache = []
                return []

            logger.info(
                f"Retrieved {len(soundcloud_tracks)} liked tracks from SoundCloud"
            )

            # Convert SoundCloud tracks to Track objects for matching
            favorites = []
            conversion_errors = 0

            for i, sc_track in enumerate(soundcloud_tracks):
                try:
                    normalized_track = (
                        self.soundcloud_adapter._normalize_track_for_matching(sc_track)
                    )
                    favorites.append(normalized_track)

                    # Log progress for large collections
                    if len(soundcloud_tracks) > 100 and (i + 1) % 100 == 0:
                        logger.debug(
                            f"Converted {i + 1}/{len(soundcloud_tracks)} SoundCloud tracks"
                        )

                except Exception as e:
                    conversion_errors += 1
                    logger.warning(f"Could not convert SoundCloud track {i + 1}: {e}")
                    # Continue processing other tracks

            if conversion_errors > 0:
                logger.warning(
                    f"Failed to convert {conversion_errors} SoundCloud tracks"
                )

            # Cache the results
            self._soundcloud_favorites_cache = favorites

            fetch_time = time.time() - start_time
            logger.info(
                f"Successfully fetched and cached {len(favorites)} SoundCloud favorites in {fetch_time:.2f} seconds"
            )

            if conversion_errors > 0:
                logger.info(
                    f"Note: {conversion_errors} tracks could not be processed and were skipped"
                )

            return favorites

        except SoundCloudAPIError:
            # Re-raise our custom exceptions
            self._soundcloud_favorites_cache = []
            raise

        except FilteringTimeoutError:
            # Re-raise timeout exceptions
            self._soundcloud_favorites_cache = []
            raise

        except Exception as e:
            error_msg = f"Unexpected error fetching SoundCloud favorites: {str(e)}"
            logger.error(error_msg, exc_info=True)
            # Cache empty list to avoid repeated failures
            self._soundcloud_favorites_cache = []
            raise SoundCloudAPIError(error_msg)

    def _match_tracks(self, lastfm_track: Track, platform_tracks: List[Track]) -> bool:
        """Check if a Last.fm track matches any platform track using fuzzy matching.

        Args:
            lastfm_track: Track from Last.fm to check
            platform_tracks: List of platform tracks to match against

        Returns:
            True if a match is found, False otherwise
        """
        if not platform_tracks:
            return False

        # Normalize the Last.fm track for comparison
        normalized_lastfm = self._normalize_track_for_comparison(lastfm_track)

        for platform_track in platform_tracks:
            normalized_platform = self._normalize_track_for_comparison(platform_track)

            # Check for exact match first (case-insensitive)
            if (
                normalized_lastfm.name.lower() == normalized_platform.name.lower()
                and normalized_lastfm.artist.lower()
                == normalized_platform.artist.lower()
            ):
                logger.debug(f"Exact match found: {lastfm_track} == {platform_track}")
                return True

            # Check for fuzzy match using similarity scoring
            if (
                self._calculate_track_similarity(normalized_lastfm, normalized_platform)
                >= 0.85
            ):
                logger.debug(f"Fuzzy match found: {lastfm_track} ~= {platform_track}")
                return True

        return False

    def _normalize_track_for_comparison(self, track: Track) -> Track:
        """Normalize track data for better matching accuracy.

        Args:
            track: Track to normalize

        Returns:
            Track with normalized name and artist
        """
        normalized_name = self._clean_track_name(track.name)
        normalized_artist = self._clean_artist_name(track.artist)

        return Track(name=normalized_name, artist=normalized_artist, url=track.url)

    def _clean_track_name(self, name: str) -> str:
        """Clean track name for better matching."""
        # Remove common patterns that interfere with matching
        name = re.sub(r"\s*\([^)]*\)\s*", " ", name)  # Remove parentheses content
        name = re.sub(r"\s*\[[^\]]*\]\s*", " ", name)  # Remove bracket content
        name = re.sub(
            r"\s*-\s*remaster.*$", "", name, flags=re.IGNORECASE
        )  # Remove remaster info
        name = re.sub(r"\s*-\s*\d{4}.*$", "", name)  # Remove years
        name = re.sub(
            r"\s*\(?\s*feat\.?\s+[^)]*\)?", "", name, flags=re.IGNORECASE
        )  # Remove featuring
        name = re.sub(
            r"\s*\(?\s*ft\.?\s+[^)]*\)?", "", name, flags=re.IGNORECASE
        )  # Remove ft.
        name = re.sub(
            r"\s*\(?\s*with\s+[^)]*\)?", "", name, flags=re.IGNORECASE
        )  # Remove with
        name = re.sub(r"\s+", " ", name)  # Normalize whitespace

        return name.strip()

    def _clean_artist_name(self, artist: str) -> str:
        """Clean artist name for better matching."""
        # Remove common patterns
        artist = re.sub(r"\s*\([^)]*\)\s*", " ", artist)  # Remove parentheses content
        artist = re.sub(r"\s*\[[^\]]*\]\s*", " ", artist)  # Remove bracket content
        artist = re.sub(r"\s+", " ", artist)  # Normalize whitespace

        return artist.strip()

    def _calculate_track_similarity(self, track1: Track, track2: Track) -> float:
        """Calculate similarity score between two tracks.

        Args:
            track1: First track to compare
            track2: Second track to compare

        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Calculate similarity for track names and artists
        name_similarity = difflib.SequenceMatcher(
            None, track1.name.lower(), track2.name.lower()
        ).ratio()

        artist_similarity = difflib.SequenceMatcher(
            None, track1.artist.lower(), track2.artist.lower()
        ).ratio()

        # Weight track name more heavily than artist (70/30 split)
        combined_similarity = (name_similarity * 0.7) + (artist_similarity * 0.3)

        # Bonus points for partial matches
        if (
            track1.name.lower() in track2.name.lower()
            or track2.name.lower() in track1.name.lower()
        ):
            combined_similarity += 0.1

        if (
            track1.artist.lower() in track2.artist.lower()
            or track2.artist.lower() in track1.artist.lower()
        ):
            combined_similarity += 0.05

        # Cap at 1.0
        return min(combined_similarity, 1.0)
