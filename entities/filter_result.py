"""FilterResult entity for tracking filtering statistics."""

from dataclasses import dataclass
from typing import List, Dict, Any
from .track import Track


@dataclass
class FilterResult:
    """Result of platform filtering operation with statistics."""

    original_count: int
    filtered_tracks: List[Track]
    removed_tracks: List[Track]
    soundcloud_matches: int
    spotify_matches: int
    errors: List[str]

    def __post_init__(self):
        """Validate filter result data after initialization."""
        if self.original_count < 0:
            raise ValueError("Original count cannot be negative")
        
        if not isinstance(self.filtered_tracks, list):
            raise ValueError("Filtered tracks must be a list")
        
        if not isinstance(self.removed_tracks, list):
            raise ValueError("Removed tracks must be a list")
        
        if not isinstance(self.errors, list):
            raise ValueError("Errors must be a list")
        
        if self.soundcloud_matches < 0:
            raise ValueError("SoundCloud matches cannot be negative")
        
        if self.spotify_matches < 0:
            raise ValueError("Spotify matches cannot be negative")
        
        # Validate that counts are consistent
        expected_filtered_count = self.original_count - len(self.removed_tracks)
        if len(self.filtered_tracks) != expected_filtered_count:
            raise ValueError(
                f"Inconsistent track counts: expected {expected_filtered_count} "
                f"filtered tracks, got {len(self.filtered_tracks)}"
            )

    @classmethod
    def create_empty(cls, original_tracks: List[Track]) -> "FilterResult":
        """Create a FilterResult with no filtering applied."""
        return cls(
            original_count=len(original_tracks),
            filtered_tracks=original_tracks.copy(),
            removed_tracks=[],
            soundcloud_matches=0,
            spotify_matches=0,
            errors=[]
        )

    @classmethod
    def create_with_filtering(
        cls,
        original_tracks: List[Track],
        removed_tracks: List[Track],
        soundcloud_matches: int = 0,
        spotify_matches: int = 0,
        errors: List[str] = None
    ) -> "FilterResult":
        """Create a FilterResult with filtering applied."""
        if errors is None:
            errors = []
        
        # Create filtered tracks by removing the removed tracks
        filtered_tracks = [
            track for track in original_tracks 
            if track not in removed_tracks
        ]
        
        return cls(
            original_count=len(original_tracks),
            filtered_tracks=filtered_tracks,
            removed_tracks=removed_tracks,
            soundcloud_matches=soundcloud_matches,
            spotify_matches=spotify_matches,
            errors=errors
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert filter result to dictionary for JSON serialization."""
        return {
            "original_count": self.original_count,
            "filtered_count": len(self.filtered_tracks),
            "removed_count": len(self.removed_tracks),
            "soundcloud_matches": self.soundcloud_matches,
            "spotify_matches": self.spotify_matches,
            "total_matches": self.soundcloud_matches + self.spotify_matches,
            "has_errors": len(self.errors) > 0,
            "error_count": len(self.errors),
            "errors": self.errors,
            "filtered_tracks": [track.to_dict() for track in self.filtered_tracks],
            "removed_tracks": [track.to_dict() for track in self.removed_tracks]
        }

    def get_removal_percentage(self) -> float:
        """Get the percentage of tracks that were removed."""
        if self.original_count == 0:
            return 0.0
        return (len(self.removed_tracks) / self.original_count) * 100

    def get_statistics_summary(self) -> Dict[str, Any]:
        """Get a summary of filtering statistics without track details."""
        return {
            "original_count": self.original_count,
            "filtered_count": len(self.filtered_tracks),
            "removed_count": len(self.removed_tracks),
            "removal_percentage": round(self.get_removal_percentage(), 1),
            "soundcloud_matches": self.soundcloud_matches,
            "spotify_matches": self.spotify_matches,
            "total_matches": self.soundcloud_matches + self.spotify_matches,
            "has_errors": len(self.errors) > 0,
            "error_count": len(self.errors)
        }

    def add_error(self, error: str) -> None:
        """Add an error message to the result."""
        if error and error not in self.errors:
            self.errors.append(error)

    def has_filtering_applied(self) -> bool:
        """Check if any filtering was actually applied."""
        return len(self.removed_tracks) > 0

    def is_successful(self) -> bool:
        """Check if filtering completed without errors."""
        return len(self.errors) == 0

    def __str__(self) -> str:
        """String representation of the filter result."""
        return (
            f"FilterResult: {len(self.filtered_tracks)}/{self.original_count} tracks "
            f"({len(self.removed_tracks)} removed, "
            f"{self.soundcloud_matches} SoundCloud + {self.spotify_matches} Spotify matches)"
        )

    def __len__(self) -> int:
        """Return the number of filtered tracks."""
        return len(self.filtered_tracks)