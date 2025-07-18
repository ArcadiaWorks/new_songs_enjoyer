"""SoundCloud adapter for importing playlists to SoundCloud."""

import requests
import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from entities import Track, Playlist

logger = logging.getLogger(__name__)


@dataclass
class SoundCloudTrack:
    """Represents a SoundCloud track search result."""

    id: int
    title: str
    user: str
    permalink_url: str
    duration: int
    genre: Optional[str] = None


@dataclass
class SoundCloudPlaylistResult:
    """Result of SoundCloud playlist creation."""

    success: bool
    playlist_id: Optional[int] = None
    playlist_url: Optional[str] = None
    tracks_added: int = 0
    tracks_not_found: int = 0
    error_message: Optional[str] = None
    not_found_tracks: List[str] = None


class SoundCloudAdapter:
    """Adapter for SoundCloud API integration using OAuth tokens."""

    BASE_URL = "https://api-v2.soundcloud.com"
    PLAYLIST_NAME = "new_songs_enjoyer - Discovery"

    def __init__(self, oauth_token: str):
        """Initialize SoundCloud adapter.

        Args:
            oauth_token: User OAuth token for SoundCloud API (from browser storage)
        """
        self.oauth_token = oauth_token
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"OAuth {oauth_token}",
                "Accept": "application/json; charset=utf-8",
                "Content-Type": "application/json",
            }
        )

    @classmethod
    def from_env(cls) -> "SoundCloudAdapter":
        """Create adapter from environment variables."""
        oauth_token = os.getenv("SOUNDCLOUD_OAUTH_TOKEN")

        if not oauth_token:
            raise ValueError("SOUNDCLOUD_OAUTH_TOKEN environment variable is required")

        return cls(oauth_token)

    def search_track(self, track: Track) -> Optional[SoundCloudTrack]:
        """Search for a track on SoundCloud using enhanced search strategies.

        Args:
            track: Track to search for

        Returns:
            SoundCloudTrack if found, None otherwise
        """
        # Generate multiple search strategies
        search_queries = self._generate_search_queries(track)

        for i, query in enumerate(search_queries):
            try:
                logger.debug(
                    f"Trying search query {i + 1}/{len(search_queries)}: '{query}'"
                )

                params = {"q": query, "limit": 5, "linked_partitioning": 1}
                response = self.session.get(
                    f"{self.BASE_URL}/search/tracks", params=params
                )
                response.raise_for_status()

                data = response.json()

                # API v2 returns results in 'collection' array
                if data and "collection" in data and len(data["collection"]) > 0:
                    # Try to find the best match from multiple results
                    best_match = self._find_best_match(track, data["collection"])
                    if best_match:
                        track_data = best_match
                        sc_track = SoundCloudTrack(
                            id=track_data["id"],
                            title=track_data["title"],
                            user=track_data["user"]["username"],
                            permalink_url=track_data["permalink_url"],
                            duration=track_data["duration"],
                            genre=track_data.get("genre"),
                        )
                        logger.info(
                            f"Found SoundCloud track: '{sc_track.title}' by {sc_track.user} (query: '{query}')"
                        )
                        return sc_track

            except Exception as e:
                logger.debug(f"Search query '{query}' failed: {e}")
                continue

        logger.info(f"No SoundCloud track found for: {track.name} - {track.artist}")
        return None

    def _generate_search_queries(self, track: Track) -> List[str]:
        """Generate multiple search query variations."""
        artist = track.artist.strip()
        name = track.name.strip()

        # Clean up common patterns
        clean_artist = self._clean_search_term(artist)
        clean_name = self._clean_search_term(name)

        queries = [
            f"{clean_artist} {clean_name}",  # Standard search
            f'"{clean_artist}" "{clean_name}"',  # Exact match
            f"{clean_name} {clean_artist}",  # Reversed order
            clean_name,  # Song name only
            f"{clean_artist} {clean_name.split()[0] if clean_name.split() else clean_name}",  # First word
            f"{clean_artist} {self._remove_features(clean_name)}",  # Remove featured artists
            self._remove_features(clean_name),  # Clean song name only
        ]

        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for q in queries:
            if q and q not in seen and len(q.strip()) > 2:
                seen.add(q)
                unique_queries.append(q.strip())

        return unique_queries

    def _clean_search_term(self, term: str) -> str:
        """Clean search terms for better matching."""
        import re

        # Remove common problematic patterns
        term = re.sub(r"\s*\([^)]*\)\s*", " ", term)  # Remove parentheses content
        term = re.sub(r"\s*\[[^\]]*\]\s*", " ", term)  # Remove bracket content
        term = re.sub(
            r"\s*-\s*remaster.*$", "", term, flags=re.IGNORECASE
        )  # Remove remaster info
        term = re.sub(r"\s*-\s*\d{4}.*$", "", term)  # Remove years
        term = re.sub(r"\s+", " ", term)  # Normalize whitespace

        return term.strip()

    def _remove_features(self, name: str) -> str:
        """Remove featuring/feat/ft mentions."""
        import re

        # Remove featuring artists
        patterns = [
            r"\s*\(?\s*feat\.?\s+[^)]*\)?",
            r"\s*\(?\s*featuring\s+[^)]*\)?",
            r"\s*\(?\s*ft\.?\s+[^)]*\)?",
            r"\s*\(?\s*with\s+[^)]*\)?",
        ]

        for pattern in patterns:
            name = re.sub(pattern, "", name, flags=re.IGNORECASE)

        return name.strip()

    def _find_best_match(
        self, original_track: Track, candidates: List[Dict]
    ) -> Optional[Dict]:
        """Find the best matching track from search results."""
        if not candidates:
            return None

        # If only one result, return it
        if len(candidates) == 1:
            return candidates[0]

        import difflib

        original_artist = original_track.artist.lower()
        original_name = original_track.name.lower()

        best_score = 0
        best_match = None

        for candidate in candidates:
            # Get candidate info
            candidate_title = candidate.get("title", "").lower()
            candidate_artist = candidate.get("user", {}).get("username", "").lower()

            # Calculate similarity scores
            title_score = difflib.SequenceMatcher(
                None, original_name, candidate_title
            ).ratio()
            artist_score = difflib.SequenceMatcher(
                None, original_artist, candidate_artist
            ).ratio()

            # Combined score with title weighted more heavily
            combined_score = (title_score * 0.7) + (artist_score * 0.3)

            # Bonus points for exact artist match
            if (
                original_artist in candidate_artist
                or candidate_artist in original_artist
            ):
                combined_score += 0.2

            # Bonus points for exact title match
            if original_name in candidate_title or candidate_title in original_name:
                combined_score += 0.1

            logger.debug(
                f"Candidate: '{candidate_title}' by {candidate_artist} - Score: {combined_score:.3f}"
            )

            if combined_score > best_score:
                best_score = combined_score
                best_match = candidate

        # Only return if score is reasonable
        if best_score > 0.3:  # Threshold for acceptable match
            logger.debug(f"Best match selected with score: {best_score:.3f}")
            return best_match

        logger.debug(f"No good match found (best score: {best_score:.3f})")
        return None

    def create_playlist(
        self, title: str, description: str = None
    ) -> Optional[Dict[str, Any]]:
        """Create a new SoundCloud playlist.

        Args:
            title: Playlist title
            description: Playlist description

        Returns:
            Playlist data if successful, None otherwise
        """
        try:
            playlist_data = {
                "playlist": {
                    "title": title,
                    "sharing": "public",
                    "description": description
                    or f"Curated by new_songs_enjoyer on {datetime.now().strftime('%Y-%m-%d')}",
                }
            }

            logger.info(f"Creating SoundCloud playlist: {title}")
            response = self.session.post(
                f"{self.BASE_URL}/playlists", json=playlist_data
            )

            if response.status_code == 403:
                logger.warning(
                    "Playlist creation requires additional permissions. OAuth token may be read-only."
                )
                return None

            response.raise_for_status()

            playlist = response.json()
            logger.info(f"Created SoundCloud playlist with ID: {playlist['id']}")
            return playlist

        except Exception as e:
            logger.error(f"Error creating SoundCloud playlist: {e}")
            return None

    def add_tracks_to_playlist(self, playlist_id: int, track_ids: List[int]) -> bool:
        """Add tracks to an existing SoundCloud playlist.

        Args:
            playlist_id: SoundCloud playlist ID
            track_ids: List of SoundCloud track IDs to add

        Returns:
            True if successful, False otherwise
        """
        try:
            if not track_ids:
                logger.warning("No track IDs provided to add to playlist")
                return True

            # Get current playlist to append tracks
            playlist_response = self.session.get(
                f"{self.BASE_URL}/playlists/{playlist_id}"
            )
            playlist_response.raise_for_status()
            current_playlist = playlist_response.json()

            # Get current track IDs
            current_track_ids = [
                track["id"] for track in current_playlist.get("tracks", [])
            ]

            # Add new track IDs (avoiding duplicates)
            updated_track_ids = current_track_ids + [
                tid for tid in track_ids if tid not in current_track_ids
            ]

            # Update playlist
            update_data = {
                "playlist": {"tracks": [{"id": tid} for tid in updated_track_ids]}
            }

            logger.info(f"Adding {len(track_ids)} tracks to playlist {playlist_id}")
            response = self.session.put(
                f"{self.BASE_URL}/playlists/{playlist_id}", json=update_data
            )
            response.raise_for_status()

            logger.info(f"Successfully added tracks to playlist")
            return True

        except Exception as e:
            logger.error(f"Error adding tracks to playlist {playlist_id}: {e}")
            return False

    def find_existing_playlist(self, title: str) -> Optional[Dict[str, Any]]:
        """Find an existing playlist by title.

        Args:
            title: Playlist title to search for

        Returns:
            Playlist data if found, None otherwise
        """
        try:
            logger.debug(f"Searching for existing playlist: {title}")
            response = self.session.get(f"{self.BASE_URL}/me/playlists")
            response.raise_for_status()

            playlists = response.json()

            for playlist in playlists:
                if playlist["title"] == title:
                    logger.info(
                        f"Found existing playlist: {title} (ID: {playlist['id']})"
                    )
                    return playlist

            logger.debug(f"No existing playlist found with title: {title}")
            return None

        except Exception as e:
            logger.error(f"Error searching for existing playlist: {e}")
            return None

    def import_playlist(self, playlist: Playlist) -> SoundCloudPlaylistResult:
        """Import a playlist to SoundCloud.

        Args:
            playlist: Playlist to import

        Returns:
            SoundCloudPlaylistResult with import results
        """
        try:
            logger.info(
                f"Starting SoundCloud import for playlist with {len(playlist)} tracks"
            )

            # Search for tracks on SoundCloud
            soundcloud_tracks = []
            not_found_tracks = []

            for track in playlist.tracks:
                sc_track = self.search_track(track)
                if sc_track:
                    soundcloud_tracks.append(sc_track)
                else:
                    not_found_tracks.append(f"{track.name} - {track.artist}")

            logger.info(
                f"Found {len(soundcloud_tracks)} tracks on SoundCloud, {len(not_found_tracks)} not found"
            )

            if not soundcloud_tracks:
                return SoundCloudPlaylistResult(
                    success=False,
                    error_message="No tracks found on SoundCloud",
                    tracks_not_found=len(not_found_tracks),
                    not_found_tracks=not_found_tracks,
                )

            # For read-only tokens, we can still provide track discovery results
            if len(soundcloud_tracks) > 0:
                logger.info(f"Found {len(soundcloud_tracks)} tracks successfully")

                # Try to find or create playlist (may fail with read-only tokens)
                sc_playlist = None
                try:
                    sc_playlist = self.find_existing_playlist(self.PLAYLIST_NAME)
                except Exception as e:
                    logger.warning(
                        f"Cannot access user playlists with current token: {e}"
                    )

                if not sc_playlist:
                    # Try to create new playlist
                    description = f"Curated music discovery playlist generated on {playlist.metadata.date} using tags: {', '.join(playlist.metadata.tags_used)}"
                    try:
                        sc_playlist = self.create_playlist(
                            self.PLAYLIST_NAME, description
                        )
                    except Exception as e:
                        logger.warning(
                            f"Cannot create playlist with current token: {e}"
                        )

                if sc_playlist:
                    # Try to add tracks to playlist
                    track_ids = [track.id for track in soundcloud_tracks]
                    success = self.add_tracks_to_playlist(sc_playlist["id"], track_ids)

                    if success:
                        return SoundCloudPlaylistResult(
                            success=True,
                            playlist_id=sc_playlist["id"],
                            playlist_url=sc_playlist["permalink_url"],
                            tracks_added=len(soundcloud_tracks),
                            tracks_not_found=len(not_found_tracks),
                            not_found_tracks=not_found_tracks,
                        )
                    else:
                        logger.warning("Could not add tracks to playlist")

                # Fallback: Return successful track discovery without playlist creation
                logger.info(
                    "Returning track discovery results without playlist creation"
                )
                track_urls = [track.permalink_url for track in soundcloud_tracks]
                return SoundCloudPlaylistResult(
                    success=True,
                    playlist_id=None,
                    playlist_url=None,
                    tracks_added=len(soundcloud_tracks),
                    tracks_not_found=len(not_found_tracks),
                    error_message=f"Found {len(soundcloud_tracks)} tracks on SoundCloud. Playlist creation requires additional permissions. Track URLs: {', '.join(track_urls[:3])}{'...' if len(track_urls) > 3 else ''}",
                    not_found_tracks=not_found_tracks,
                )

            return SoundCloudPlaylistResult(
                success=False,
                error_message="Could not process tracks or create playlist",
            )

        except Exception as e:
            logger.error(f"Error importing playlist to SoundCloud: {e}")
            return SoundCloudPlaylistResult(success=False, error_message=str(e))

    def get_playlist_url(self, playlist_id: int) -> Optional[str]:
        """Get the public URL for a SoundCloud playlist.

        Args:
            playlist_id: SoundCloud playlist ID

        Returns:
            Playlist URL if found, None otherwise
        """
        try:
            response = self.session.get(f"{self.BASE_URL}/playlists/{playlist_id}")
            response.raise_for_status()

            playlist = response.json()
            return playlist.get("permalink_url")

        except Exception as e:
            logger.error(f"Error getting playlist URL: {e}")
            return None

    def get_user_profile(self) -> Optional[Dict[str, Any]]:
        """Get user profile information to validate OAuth token.

        Returns:
            User profile data if successful, None otherwise

        Raises:
            requests.exceptions.RequestException: For HTTP-related errors
        """
        try:
            logger.debug("Fetching user profile to validate OAuth token")
            response = self.session.get(f"{self.BASE_URL}/me", timeout=30)

            if response.status_code == 401:
                logger.error(
                    "SoundCloud OAuth token is invalid or expired (401 Unauthorized)"
                )
                raise requests.exceptions.HTTPError(
                    "Invalid or expired OAuth token", response=response
                )
            elif response.status_code == 403:
                logger.error(
                    "SoundCloud OAuth token lacks required permissions (403 Forbidden)"
                )
                raise requests.exceptions.HTTPError(
                    "Insufficient permissions for OAuth token", response=response
                )
            elif response.status_code == 429:
                logger.error(
                    "SoundCloud API rate limit exceeded (429 Too Many Requests)"
                )
                raise requests.exceptions.HTTPError(
                    "Rate limit exceeded", response=response
                )

            response.raise_for_status()

            profile = response.json()
            username = profile.get("username", "Unknown")
            user_id = profile.get("id", "Unknown")
            logger.info(
                f"Successfully validated OAuth token for user: {username} (ID: {user_id})"
            )
            return profile

        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout while fetching user profile: {e}")
            raise
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error while fetching user profile: {e}")
            raise
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error while fetching user profile: {e}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error while fetching user profile: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching user profile: {e}", exc_info=True)
            return None

    def get_user_liked_tracks(self, limit: int = 200) -> List[SoundCloudTrack]:
        """Fetch user's liked songs from SoundCloud API.

        Args:
            limit: Maximum number of liked tracks to fetch (default: 200)

        Returns:
            List of SoundCloudTrack objects representing liked songs

        Raises:
            requests.exceptions.RequestException: For HTTP-related errors
        """
        if limit <= 0:
            logger.warning(
                "Invalid limit provided for liked tracks, using default of 200"
            )
            limit = 200

        logger.info(f"Fetching user's liked tracks (limit: {limit})")
        start_time = datetime.now()

        try:
            liked_tracks = []
            offset = 0
            page_size = min(
                50, limit
            )  # SoundCloud API typically limits to 50 per request
            pages_fetched = 0
            max_pages = 20  # Safety limit to prevent infinite loops

            while len(liked_tracks) < limit and pages_fetched < max_pages:
                try:
                    params = {
                        "limit": page_size,
                        "offset": offset,
                        "linked_partitioning": 1,
                    }

                    logger.debug(
                        f"Fetching liked tracks page {pages_fetched + 1} (offset: {offset})"
                    )
                    response = self.session.get(
                        f"{self.BASE_URL}/me/likes", params=params, timeout=30
                    )

                    if response.status_code == 401:
                        logger.error(
                            "SoundCloud OAuth token is invalid or expired while fetching liked tracks"
                        )
                        raise requests.exceptions.HTTPError(
                            "Invalid or expired OAuth token", response=response
                        )
                    elif response.status_code == 403:
                        logger.error(
                            "SoundCloud OAuth token lacks permissions to access liked tracks"
                        )
                        raise requests.exceptions.HTTPError(
                            "Insufficient permissions to access liked tracks",
                            response=response,
                        )
                    elif response.status_code == 429:
                        logger.warning(
                            "SoundCloud API rate limit exceeded while fetching liked tracks"
                        )
                        # Wait and retry once
                        import time

                        time.sleep(5)
                        response = self.session.get(
                            f"{self.BASE_URL}/me/likes", params=params, timeout=30
                        )
                        if response.status_code == 429:
                            raise requests.exceptions.HTTPError(
                                "Rate limit exceeded", response=response
                            )

                    response.raise_for_status()
                    data = response.json()

                    # Handle paginated response
                    if "collection" not in data:
                        logger.warning(
                            "Unexpected API response format - missing 'collection' field"
                        )
                        break

                    collection = data["collection"]
                    if not collection:
                        logger.debug("No more liked tracks available")
                        break

                    tracks_processed_this_page = 0
                    for item in collection:
                        try:
                            # SoundCloud likes can include tracks, playlists, etc.
                            # We only want tracks
                            track_data = None
                            if item.get("kind") == "track":
                                track_data = item
                            elif "track" in item and item["track"]:
                                track_data = item["track"]
                            else:
                                continue

                            # Skip if not a valid track
                            if not track_data or track_data.get("kind") != "track":
                                continue

                            # Validate required fields
                            required_fields = [
                                "id",
                                "title",
                                "user",
                                "permalink_url",
                                "duration",
                            ]
                            if not all(
                                field in track_data for field in required_fields
                            ):
                                logger.debug(
                                    f"Skipping track with missing required fields: {track_data.get('title', 'Unknown')}"
                                )
                                continue

                            if (
                                not track_data["user"]
                                or "username" not in track_data["user"]
                            ):
                                logger.debug(
                                    f"Skipping track with invalid user data: {track_data.get('title', 'Unknown')}"
                                )
                                continue

                            sc_track = SoundCloudTrack(
                                id=track_data["id"],
                                title=track_data["title"],
                                user=track_data["user"]["username"],
                                permalink_url=track_data["permalink_url"],
                                duration=track_data["duration"],
                                genre=track_data.get("genre"),
                            )
                            liked_tracks.append(sc_track)
                            tracks_processed_this_page += 1

                            if len(liked_tracks) >= limit:
                                break

                        except Exception as e:
                            logger.warning(f"Error processing liked track item: {e}")
                            continue

                    logger.debug(
                        f"Processed {tracks_processed_this_page} tracks from page {pages_fetched + 1}"
                    )

                    # Check if there are more pages
                    if "next_href" not in data or not data["next_href"]:
                        logger.debug("No more pages available")
                        break

                    offset += page_size
                    pages_fetched += 1

                except requests.exceptions.Timeout as e:
                    logger.error(
                        f"Timeout while fetching liked tracks page {pages_fetched + 1}: {e}"
                    )
                    if pages_fetched == 0:
                        # If first page fails, re-raise
                        raise
                    else:
                        # If we have some tracks, log warning and continue
                        logger.warning("Continuing with partial results due to timeout")
                        break

                except requests.exceptions.ConnectionError as e:
                    logger.error(
                        f"Connection error while fetching liked tracks page {pages_fetched + 1}: {e}"
                    )
                    if pages_fetched == 0:
                        # If first page fails, re-raise
                        raise
                    else:
                        # If we have some tracks, log warning and continue
                        logger.warning(
                            "Continuing with partial results due to connection error"
                        )
                        break

                except requests.exceptions.HTTPError as e:
                    logger.error(
                        f"HTTP error while fetching liked tracks page {pages_fetched + 1}: {e}"
                    )
                    raise  # Always re-raise HTTP errors

                except Exception as e:
                    logger.error(
                        f"Unexpected error while fetching liked tracks page {pages_fetched + 1}: {e}"
                    )
                    if pages_fetched == 0:
                        # If first page fails, re-raise
                        raise
                    else:
                        # If we have some tracks, log warning and continue
                        logger.warning(
                            "Continuing with partial results due to unexpected error"
                        )
                        break

            if pages_fetched >= max_pages:
                logger.warning(
                    f"Reached maximum page limit ({max_pages}) while fetching liked tracks"
                )

            fetch_duration = datetime.now() - start_time
            logger.info(
                f"Successfully fetched {len(liked_tracks)} liked tracks in {fetch_duration.total_seconds():.2f} seconds"
            )

            if len(liked_tracks) < limit and pages_fetched > 0:
                logger.info(
                    f"Note: Requested {limit} tracks but only found {len(liked_tracks)} in user's liked tracks"
                )

            return liked_tracks

        except requests.exceptions.RequestException:
            # Re-raise request exceptions for proper handling upstream
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error fetching user's liked tracks: {e}", exc_info=True
            )
            raise

    def _normalize_track_for_matching(self, track: SoundCloudTrack) -> Track:
        """Convert SoundCloudTrack to Track format for matching purposes.

        Args:
            track: SoundCloudTrack to normalize

        Returns:
            Track object with normalized data for matching
        """
        # Clean and normalize the track title and artist name
        normalized_title = self._clean_search_term(track.title)
        normalized_artist = self._clean_search_term(track.user)

        return Track(
            name=normalized_title, artist=normalized_artist, url=track.permalink_url
        )
