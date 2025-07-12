"""API response entities for Last.fm integration."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from .track import Track


@dataclass
class LastFmApiResponse:
    """Represents a response from Last.fm API."""

    tag: str
    tracks: List[Track]
    total_tracks: int
    success: bool
    error_message: Optional[str] = None

    @classmethod
    def from_api_data(cls, tag: str, data: Dict[str, Any]) -> "LastFmApiResponse":
        """Create an API response from Last.fm API data."""
        try:
            tracks_data = data.get("tracks", {}).get("track", [])
            if not isinstance(tracks_data, list):
                tracks_data = [tracks_data] if tracks_data else []

            tracks = []
            for track_data in tracks_data:
                try:
                    track = Track.from_lastfm_data(track_data)
                    tracks.append(track)
                except (ValueError, KeyError) as e:
                    # Skip invalid tracks but log the issue
                    continue

            return cls(tag=tag, tracks=tracks, total_tracks=len(tracks), success=True)

        except Exception as e:
            return cls(
                tag=tag, tracks=[], total_tracks=0, success=False, error_message=str(e)
            )

    @classmethod
    def error(cls, tag: str, error_message: str) -> "LastFmApiResponse":
        """Create an error response."""
        return cls(
            tag=tag,
            tracks=[],
            total_tracks=0,
            success=False,
            error_message=error_message,
        )

    def filter_seen_tracks(self, seen_tracks: set) -> "LastFmApiResponse":
        """Filter out tracks that have been seen before."""
        filtered_tracks = [
            track
            for track in self.tracks
            if (track.name, track.artist) not in seen_tracks
        ]

        return LastFmApiResponse(
            tag=self.tag,
            tracks=filtered_tracks,
            total_tracks=len(filtered_tracks),
            success=self.success,
            error_message=self.error_message,
        )

    def get_track_count(self) -> int:
        """Get the number of tracks in the response."""
        return len(self.tracks)

    def is_empty(self) -> bool:
        """Check if the response contains no tracks."""
        return len(self.tracks) == 0

    def has_error(self) -> bool:
        """Check if the response contains an error."""
        return not self.success or self.error_message is not None

    def __str__(self) -> str:
        """String representation of the API response."""
        if self.has_error():
            return f"LastFM API Error for '{self.tag}': {self.error_message}"
        return f"LastFM API Response for '{self.tag}': {self.get_track_count()} tracks"
