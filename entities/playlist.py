"""Playlist entities for managing music playlists."""

from dataclasses import dataclass
from typing import List, Dict, Any
from datetime import date
from .track import Track


@dataclass
class PlaylistMetadata:
    """Metadata for a music playlist."""

    generated_at: str
    date: str
    tags_used: List[str]
    tracks_requested: int
    tracks_found: int
    total_available_tracks: int
    api_limit_per_tag: int
    language: str
    filtering_stats: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary for JSON serialization."""
        result = {
            "generated_at": self.generated_at,
            "date": self.date,
            "tags_used": self.tags_used,
            "tracks_requested": self.tracks_requested,
            "tracks_found": self.tracks_found,
            "total_available_tracks": self.total_available_tracks,
            "api_limit_per_tag": self.api_limit_per_tag,
            "language": self.language,
        }

        # Include filtering statistics if available
        if self.filtering_stats:
            result["filtering_stats"] = self.filtering_stats

        return result


@dataclass
class Playlist:
    """Represents a complete music playlist with metadata and tracks."""

    metadata: PlaylistMetadata
    tracks: List[Track]

    def __post_init__(self):
        """Validate playlist data after initialization."""
        if not isinstance(self.tracks, list):
            raise ValueError("Tracks must be a list")

        # Ensure all tracks have positions
        for i, track in enumerate(self.tracks, 1):
            if track.position is None:
                track.position = i
            track.added_to_playlist = self.metadata.generated_at

    @classmethod
    def create(
        cls,
        tracks: List[Track],
        timestamp: str,
        tags: List[str],
        tracks_requested: int,
        total_available_tracks: int,
        api_limit_per_tag: int,
        language: str = "fr",
    ) -> "Playlist":
        """Create a playlist with auto-generated metadata."""
        metadata = PlaylistMetadata(
            generated_at=timestamp,
            date=str(date.today()),
            tags_used=tags,
            tracks_requested=tracks_requested,
            tracks_found=len(tracks),
            total_available_tracks=total_available_tracks,
            api_limit_per_tag=api_limit_per_tag,
            language=language,
        )

        return cls(metadata=metadata, tracks=tracks)

    def to_dict(self) -> Dict[str, Any]:
        """Convert playlist to dictionary for JSON serialization."""
        return {
            "metadata": self.metadata.to_dict(),
            "tracks": [track.to_dict() for track in self.tracks],
        }

    def add_track(self, track: Track) -> None:
        """Add a track to the playlist."""
        track.position = len(self.tracks) + 1
        track.added_to_playlist = self.metadata.generated_at
        self.tracks.append(track)

        # Update metadata
        self.metadata.tracks_found = len(self.tracks)

    def remove_track(self, track: Track) -> bool:
        """Remove a track from the playlist. Returns True if removed."""
        if track in self.tracks:
            self.tracks.remove(track)

            # Reposition remaining tracks
            for i, remaining_track in enumerate(self.tracks, 1):
                remaining_track.position = i

            # Update metadata
            self.metadata.tracks_found = len(self.tracks)
            return True
        return False

    def get_track_count(self) -> int:
        """Get the number of tracks in the playlist."""
        return len(self.tracks)

    def is_empty(self) -> bool:
        """Check if the playlist is empty."""
        return len(self.tracks) == 0

    def get_tags_display(self) -> str:
        """Get a formatted string of tags for display."""
        return ", ".join(self.metadata.tags_used)

    def set_filtering_stats(self, filter_result) -> None:
        """Set filtering statistics from FilterResult.

        Args:
            filter_result: FilterResult object containing filtering statistics
        """
        if filter_result and hasattr(filter_result, "get_statistics_summary"):
            self.metadata.filtering_stats = filter_result.get_statistics_summary()

    def has_filtering_stats(self) -> bool:
        """Check if playlist has filtering statistics."""
        return self.metadata.filtering_stats is not None

    def get_filtering_stats(self) -> Dict[str, Any]:
        """Get filtering statistics or empty dict if none available."""
        return self.metadata.filtering_stats or {}

    def __str__(self) -> str:
        """String representation of the playlist."""
        return f"Playlist ({self.get_track_count()} tracks) - {self.get_tags_display()}"

    def __len__(self) -> int:
        """Return the number of tracks in the playlist."""
        return len(self.tracks)

    def __iter__(self):
        """Make playlist iterable over tracks."""
        return iter(self.tracks)
