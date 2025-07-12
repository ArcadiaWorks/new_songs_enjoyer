"""Track entity representing a music track."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Track:
    """Represents a music track with its metadata."""

    name: str
    artist: str
    url: Optional[str] = None
    position: Optional[int] = None
    added_to_playlist: Optional[str] = None

    def __post_init__(self):
        """Validate track data after initialization."""
        if not self.name or not self.name.strip():
            raise ValueError("Track name cannot be empty")
        if not self.artist or not self.artist.strip():
            raise ValueError("Artist name cannot be empty")

    @classmethod
    def from_lastfm_data(cls, data: dict, position: Optional[int] = None) -> "Track":
        """Create a Track from Last.fm API response data."""
        if not isinstance(data, dict):
            raise ValueError("Track data must be a dictionary")

        name = data.get("name", "").strip()
        if not name:
            raise ValueError("Track name is required")

        # Handle artist data (can be dict or string)
        artist_data = data.get("artist", {})
        if isinstance(artist_data, dict):
            artist = artist_data.get("name", "").strip()
        else:
            artist = str(artist_data).strip()

        if not artist:
            raise ValueError("Artist name is required")

        return cls(name=name, artist=artist, url=data.get("url"), position=position)

    def to_dict(self) -> dict:
        """Convert track to dictionary for JSON serialization."""
        result = {
            "name": self.name,
            "artist": self.artist,
        }

        if self.url:
            result["url"] = self.url
            result["last_fm_url"] = self.url

        if self.position is not None:
            result["position"] = self.position

        if self.added_to_playlist:
            result["added_to_playlist"] = self.added_to_playlist

        return result

    def __str__(self) -> str:
        """String representation of the track."""
        return f"{self.name} - {self.artist}"

    def __eq__(self, other) -> bool:
        """Check equality based on name and artist."""
        if not isinstance(other, Track):
            return False
        return (
            self.name.lower() == other.name.lower()
            and self.artist.lower() == other.artist.lower()
        )

    def __hash__(self) -> int:
        """Hash based on name and artist for set operations."""
        return hash((self.name.lower(), self.artist.lower()))
