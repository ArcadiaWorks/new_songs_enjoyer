"""Main module for new_songs_enjoyer music recommendation system."""

import requests
import random
import json
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
from jinja2 import Template

from config import (
    parse_arguments,
    load_config,
    merge_config_with_args,
    setup_logging,
    validate_platform_filtering_config,
)
from entities import Track, Playlist, LastFmApiResponse, FilterResult
from adapter import SoundCloudAdapter
from platform_filter import PlatformFilter

# Load environment variables
load_dotenv()
logger = logging.getLogger(__name__)


def ensure_output_directory(output_dir: str) -> Path:
    """Create output directory if it doesn't exist."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    logger.debug(f"Ensured output directory exists: {output_path}")
    return output_path


def fetch_tracks_for_tag(tag: str, config: dict) -> LastFmApiResponse:
    """Fetch tracks for a given tag from Last.fm API."""
    api_key = os.getenv("LASTFM_API_KEY", "VOTRE_CLE_LASTFM")
    url = config["api"]["base_url"]

    params = {
        "method": "tag.gettoptracks",
        "tag": tag,
        "api_key": api_key,
        "format": "json",
        "limit": config["api"]["limit_per_tag"],
    }

    try:
        logger.debug(f"Fetching tracks for tag: {tag}")
        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        api_response = LastFmApiResponse.from_api_data(tag, data)

        logger.info(f"Fetched {api_response.get_track_count()} tracks for tag '{tag}'")
        return api_response

    except requests.RequestException as e:
        logger.error(f"Error fetching tracks for tag '{tag}': {e}")
        return LastFmApiResponse.error(tag, str(e))
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON response for tag '{tag}': {e}")
        return LastFmApiResponse.error(tag, f"JSON parsing error: {e}")


def load_history(history_file: Path) -> dict:
    """Load music history from file."""
    if not history_file.exists():
        logger.debug(f"History file {history_file} does not exist, starting fresh")
        return {}

    try:
        with open(history_file, "r", encoding="utf-8") as f:
            history = json.load(f)
            logger.debug(f"Loaded history from {history_file}")
            return history
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error loading history from {history_file}: {e}")
        return {}


def save_history(history: dict, history_file: Path) -> None:
    """Save music history to file."""
    try:
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        logger.debug(f"Saved history to {history_file}")
    except IOError as e:
        logger.error(f"Error saving history to {history_file}: {e}")


def get_seen_tracks(history: dict) -> set:
    """Extract seen tracks from history."""
    seen = set()
    for day_tracks in history.values():
        for track_data in day_tracks:
            seen.add((track_data["name"], track_data["artist"]))
    return seen


def generate_html_playlist(playlist: Playlist, output_dir: Path) -> Path:
    """Generate a beautiful HTML version of the playlist."""
    try:
        template_path = Path("templates/playlist_template.html")
        if not template_path.exists():
            logger.warning("HTML template not found, skipping HTML generation")
            return None

        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()

        template = Template(template_content)
        html_content = template.render(
            metadata=playlist.metadata.to_dict(),
            tracks=[track.to_dict() for track in playlist.tracks],
            language=playlist.metadata.language,
        )

        html_filename = f"playlist_{playlist.metadata.generated_at}.html"
        html_file = output_dir / html_filename

        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"Generated beautiful HTML playlist: {html_file}")
        return html_file

    except Exception as e:
        logger.error(f"Error generating HTML playlist: {e}")
        return None


def create_platform_filter(config: dict) -> Optional[PlatformFilter]:
    """Create PlatformFilter instance if filtering is enabled and configured.

    Args:
        config: Application configuration dictionary

    Returns:
        PlatformFilter instance or None if filtering is disabled/unavailable
    """
    try:
        platform_config = config.get("platform_filtering", {})

        if not platform_config.get("enabled", False):
            logger.debug("Platform filtering is disabled in configuration")
            return None

        # Validate configuration
        if not validate_platform_filtering_config(config):
            logger.warning(
                "Platform filtering configuration is invalid, skipping filtering"
            )
            return None

        soundcloud_adapter = None

        # Setup SoundCloud adapter if enabled
        soundcloud_config = platform_config.get("soundcloud", {})
        if soundcloud_config.get("enabled", False):
            oauth_token = soundcloud_config.get("oauth_token")
            if oauth_token and oauth_token.strip():
                try:
                    logger.debug(
                        "Initializing SoundCloud adapter for platform filtering"
                    )
                    soundcloud_adapter = SoundCloudAdapter(
                        oauth_token=oauth_token.strip()
                    )

                    # Test the adapter by validating the token
                    try:
                        profile = soundcloud_adapter.get_user_profile()
                        if profile:
                            username = profile.get("username", "Unknown")
                            logger.info(
                                f"SoundCloud adapter initialized successfully for user: {username}"
                            )
                        else:
                            logger.warning(
                                "SoundCloud adapter created but token validation failed"
                            )
                            soundcloud_adapter = None
                    except Exception as validation_error:
                        logger.error(
                            f"SoundCloud token validation failed: {validation_error}"
                        )
                        if "401" in str(validation_error) or "403" in str(
                            validation_error
                        ):
                            logger.error(
                                "SoundCloud OAuth token is invalid or expired. Please update your token."
                            )
                        elif "timeout" in str(validation_error).lower():
                            logger.warning(
                                "SoundCloud token validation timed out, but will attempt to use adapter"
                            )
                        else:
                            logger.warning(
                                "SoundCloud token validation failed, but will attempt to use adapter"
                            )

                except ValueError as ve:
                    logger.error(f"Invalid SoundCloud configuration: {ve}")
                    return None
                except Exception as e:
                    logger.error(f"Failed to initialize SoundCloud adapter: {e}")
                    if "token" in str(e).lower():
                        logger.error(
                            "Please check your SOUNDCLOUD_OAUTH_TOKEN environment variable"
                        )
                    return None
            else:
                logger.warning(
                    "SoundCloud filtering enabled but no OAuth token provided"
                )
                logger.info(
                    "To enable SoundCloud filtering, set SOUNDCLOUD_OAUTH_TOKEN environment variable"
                )

        # Create PlatformFilter instance
        if soundcloud_adapter:
            try:
                platform_filter = PlatformFilter(soundcloud_adapter=soundcloud_adapter)
                logger.info(
                    "Platform filtering initialized successfully with SoundCloud integration"
                )
                return platform_filter
            except Exception as e:
                logger.error(f"Failed to create PlatformFilter instance: {e}")
                return None
        else:
            logger.info(
                "No platform adapters available for filtering - continuing without filtering"
            )
            return None

    except Exception as e:
        logger.error(f"Unexpected error creating platform filter: {e}", exc_info=True)
        return None


def save_playlist_files(playlist: Playlist, output_dir: Path) -> dict:
    """Save playlist to both JSON and HTML formats."""
    # Save JSON file
    json_filename = f"playlist_{playlist.metadata.generated_at}.json"
    json_file = output_dir / json_filename

    try:
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(playlist.to_dict(), f, indent=2, ensure_ascii=False)
        logger.info(f"Saved JSON playlist to {json_file}")
    except IOError as e:
        logger.error(f"Error saving JSON playlist to {json_file}: {e}")
        return None

    # Generate HTML file
    html_file = generate_html_playlist(playlist, output_dir)

    return {"json": json_file, "html": html_file}


def create_playlist(tags: list, config: dict, output_dir: Path) -> Playlist:
    """Create a new playlist with recommendations."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Load history and get seen tracks
    history_file = output_dir / config["output"]["history_filename"]
    history = load_history(history_file)
    seen_tracks = get_seen_tracks(history)

    logger.info(f"Found {len(seen_tracks)} previously seen tracks")

    # Fetch tracks from all tags
    all_new_tracks = []
    total_fetched = 0

    for tag in tags:
        if config["display"]["show_fetching_progress"]:
            message = (
                f"Récupération du tag: {tag}"
                if config["display"]["language"] == "fr"
                else f"Fetching tag: {tag}"
            )
            logger.info(message)

        api_response = fetch_tracks_for_tag(tag, config)

        if api_response.has_error():
            logger.warning(
                f"Failed to fetch tracks for tag '{tag}': {api_response.error_message}"
            )
            continue

        total_fetched += api_response.total_tracks

        # Filter out seen tracks
        filtered_response = api_response.filter_seen_tracks(seen_tracks)
        all_new_tracks.extend(filtered_response.tracks)

        logger.debug(
            f"Added {filtered_response.get_track_count()} new tracks from tag '{tag}'"
        )

    logger.info(f"Total new tracks found: {len(all_new_tracks)}")

    # Check if we have any tracks to work with
    if len(all_new_tracks) == 0:
        logger.warning("No new tracks available for the selected tags")

        # Create an empty playlist with appropriate metadata
        empty_playlist = Playlist.create(
            tracks=[],
            timestamp=timestamp,
            tags=tags,
            tracks_requested=config["num_tracks"],
            total_available_tracks=total_fetched,
            api_limit_per_tag=config["api"]["limit_per_tag"],
            language=config["display"]["language"],
        )

        # Add empty filter result for consistency
        empty_filter_result = FilterResult.create_empty([])
        empty_filter_result.add_error("No new tracks found for the selected tags")
        empty_playlist.set_filtering_stats(empty_filter_result)

        # Don't save to history since there are no tracks
        return empty_playlist

    # Apply platform filtering before track selection
    filter_result = None
    platform_filter = create_platform_filter(config)

    if platform_filter:
        logger.info("Applying platform filtering to remove already liked tracks")

        try:
            filter_result = platform_filter.filter_tracks(all_new_tracks)

            # Log comprehensive filtering statistics
            stats = filter_result.get_statistics_summary()
            logger.info(f"Platform filtering results: {stats}")

            if filter_result.has_filtering_applied():
                logger.info(
                    f"Removed {len(filter_result.removed_tracks)} tracks already in platform libraries"
                )
                logger.info(f"SoundCloud matches: {filter_result.soundcloud_matches}")
                if filter_result.spotify_matches > 0:
                    logger.info(f"Spotify matches: {filter_result.spotify_matches}")

                # Log some examples of removed tracks for transparency
                if (
                    filter_result.removed_tracks
                    and len(filter_result.removed_tracks) <= 5
                ):
                    logger.debug("Removed tracks:")
                    for track in filter_result.removed_tracks:
                        logger.debug(f"  - {track.name} by {track.artist}")
                elif len(filter_result.removed_tracks) > 5:
                    logger.debug("Sample of removed tracks:")
                    for track in filter_result.removed_tracks[:3]:
                        logger.debug(f"  - {track.name} by {track.artist}")
                    logger.debug(
                        f"  ... and {len(filter_result.removed_tracks) - 3} more"
                    )
            else:
                logger.info("No tracks were filtered - all tracks are new discoveries!")

            # Handle filtering errors with user-friendly messages
            if filter_result.errors:
                logger.warning(
                    f"Platform filtering completed with {len(filter_result.errors)} issues:"
                )
                for error in filter_result.errors:
                    logger.warning(f"  - {error}")

                # Provide helpful guidance based on error types
                error_text = " ".join(filter_result.errors).lower()
                if "oauth" in error_text or "token" in error_text:
                    logger.info(
                        "💡 Tip: Update your SoundCloud OAuth token if filtering isn't working properly"
                    )
                elif "timeout" in error_text:
                    logger.info(
                        "💡 Tip: Try again later if SoundCloud services are slow"
                    )
                elif "rate limit" in error_text:
                    logger.info(
                        "💡 Tip: Wait a few minutes before trying again due to API rate limits"
                    )

            # Use filtered tracks for selection
            tracks_for_selection = filter_result.filtered_tracks

            if not tracks_for_selection:
                logger.warning(
                    "All tracks were filtered out! Using original track list to ensure recommendations are available."
                )
                tracks_for_selection = all_new_tracks
                # Update filter result to reflect fallback
                filter_result = FilterResult.create_empty(all_new_tracks)
                filter_result.add_error(
                    "All tracks filtered - using fallback to original list"
                )

        except Exception as e:
            logger.error(f"Platform filtering failed unexpectedly: {e}", exc_info=True)
            logger.warning("Continuing without platform filtering due to error")

            # Fallback to no filtering
            tracks_for_selection = all_new_tracks
            filter_result = FilterResult.create_empty(all_new_tracks)
            filter_result.add_error(f"Platform filtering failed: {str(e)}")

            # Provide user guidance
            if "soundcloud" in str(e).lower():
                logger.info("💡 Check your SoundCloud OAuth token configuration")
            else:
                logger.info("💡 Platform filtering will be skipped for this session")
    else:
        logger.debug("Platform filtering not available, using all tracks")
        tracks_for_selection = all_new_tracks
        # Create empty filter result for consistency
        filter_result = FilterResult.create_empty(all_new_tracks)

    # Select random tracks from filtered set
    random.shuffle(tracks_for_selection)
    selected_tracks = tracks_for_selection[: config["num_tracks"]]

    # Create playlist
    playlist = Playlist.create(
        tracks=selected_tracks,
        timestamp=timestamp,
        tags=tags,
        tracks_requested=config["num_tracks"],
        total_available_tracks=total_fetched,
        api_limit_per_tag=config["api"]["limit_per_tag"],
        language=config["display"]["language"],
    )

    # Add filtering statistics to playlist metadata
    playlist.set_filtering_stats(filter_result)

    # Save to history (simple format for compatibility)
    today = str(datetime.now().date())
    history[today] = [track.to_dict() for track in selected_tracks]
    save_history(history, history_file)

    return playlist


def display_playlist(playlist: Playlist) -> None:
    """Display the playlist in the console."""
    print("\n" + "=" * 50)

    if playlist.metadata.language == "fr":
        print(f"Recommandations du jour ({len(playlist)} titres):")
    else:
        print(f"Daily recommendations ({len(playlist)} tracks):")

    print("=" * 50)

    # Display filtering statistics if available
    if playlist.has_filtering_stats():
        stats = playlist.get_filtering_stats()
        if playlist.metadata.language == "fr":
            print("Filtrage des plateformes:")
            print(
                f"  • {stats['removed_count']} titres filtrés ({stats['removal_percentage']}%)"
            )
            if stats["soundcloud_matches"] > 0:
                print(f"  • {stats['soundcloud_matches']} correspondances SoundCloud")
            if stats["spotify_matches"] > 0:
                print(f"  • {stats['spotify_matches']} correspondances Spotify")
        else:
            print("Platform filtering:")
            print(
                f"  • {stats['removed_count']} tracks filtered ({stats['removal_percentage']}%)"
            )
            if stats["soundcloud_matches"] > 0:
                print(f"  • {stats['soundcloud_matches']} SoundCloud matches")
            if stats["spotify_matches"] > 0:
                print(f"  • {stats['spotify_matches']} Spotify matches")
        print("=" * 50)

    if playlist.is_empty():
        message = (
            "Aucune nouvelle recommandation disponible."
            if playlist.metadata.language == "fr"
            else "No new recommendations available."
        )
        print(message)
        return

    for track in playlist:
        print(f"{track.position:2d}. {track}")
        if track.url:
            print(f"    -> {track.url}")


def main():
    """Main entry point for the application."""
    # Parse arguments and setup
    args = parse_arguments()
    config = load_config(args.config)
    config = merge_config_with_args(config, args)

    setup_logging(config)
    logger.info("Starting new_songs_enjoyer")

    # Get configuration
    tags = config["default_tags"]
    logger.info(f"Using tags: {tags}")
    logger.info(f"Generating {config['num_tracks']} track recommendations")

    try:
        # Setup output directory
        output_dir = ensure_output_directory(config["output"]["directory"])

        # Create playlist
        playlist = create_playlist(tags, config, output_dir)

        # Save files
        files = save_playlist_files(playlist, output_dir)
        if files:
            message = (
                f"Playlist sauvegardée: {files}"
                if config["display"]["language"] == "fr"
                else f"Playlist saved: {files}"
            )
            logger.info(message)

        # Display results
        display_playlist(playlist)
        logger.info("Application completed successfully")

    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
