"""Main module for new_songs_enjoyer music recommendation system."""

import requests
import random
import json
import os
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from jinja2 import Template

from config import parse_arguments, load_config, merge_config_with_args, setup_logging
from entities import Track, Playlist, LastFmApiResponse
from adapter import SoundCloudAdapter

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

    # Select random tracks
    random.shuffle(all_new_tracks)
    selected_tracks = all_new_tracks[: config["num_tracks"]]

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
            print(f"    🔗 {track.url}")


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
