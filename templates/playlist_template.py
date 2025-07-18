"""Playlist HTML template rendering functionality."""

from jinja2 import Template
from pathlib import Path
from typing import Dict, Any
from entities import Playlist


def render_playlist_html(playlist: Playlist, language: str = "en") -> str:
    """Render playlist to HTML using Jinja2 template.

    Args:
        playlist: Playlist object to render
        language: Language for the template ('en' or 'fr')

    Returns:
        Rendered HTML string
    """
    # Load the HTML template
    template_path = Path(__file__).parent / "playlist_template.html"

    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()

    # Create Jinja2 template
    template = Template(template_content)

    # Prepare template context
    context = {
        "language": language,
        "metadata": playlist.metadata.to_dict(),
        "tracks": [track.to_dict() for track in playlist.tracks],
    }

    # Render template
    return template.render(**context)


def render_playlist_html_with_filtering(
    playlist: Playlist, filter_result, language: str = "en"
) -> str:
    """Render playlist to HTML with filtering statistics.

    Args:
        playlist: Playlist object to render
        filter_result: FilterResult object with filtering statistics
        language: Language for the template ('en' or 'fr')

    Returns:
        Rendered HTML string
    """
    # Load the HTML template
    template_path = Path(__file__).parent / "playlist_template.html"

    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()

    # Create Jinja2 template
    template = Template(template_content)

    # Prepare metadata with filtering stats
    metadata_dict = playlist.metadata.to_dict()
    if filter_result:
        metadata_dict["filtering_stats"] = filter_result.get_statistics_summary()

    # Prepare template context
    context = {
        "language": language,
        "metadata": metadata_dict,
        "tracks": [track.to_dict() for track in playlist.tracks],
    }

    # Render template
    return template.render(**context)
