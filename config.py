"""Configuration management for new_songs_enjoyer."""

import argparse
import yaml
import logging
import os

logger = logging.getLogger(__name__)


def get_default_config():
    """Return default configuration."""
    return {
        "default_tags": ["chill", "ambient", "lofi"],
        "num_tracks": 20,
        "api": {"limit_per_tag": 100, "base_url": "https://ws.audioscrobbler.com/2.0/"},
        "output": {
            "directory": "output",
            "history_filename": "music_history.json",
            "daily_playlist_format": "playlist_{date}.json",
        },
        "display": {"show_fetching_progress": True, "language": "fr"},
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "platform_filtering": {
            "enabled": False,
            "soundcloud": {
                "enabled": False,
                "oauth_token": None,
            },
            "spotify": {
                "enabled": False,
                "client_id": None,
                "client_secret": None,
                "access_token": None,
            },
        },
    }


def substitute_env_variables(config):
    """Substitute environment variables in configuration values."""

    def _substitute_recursive(obj):
        if isinstance(obj, dict):
            return {key: _substitute_recursive(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [_substitute_recursive(item) for item in obj]
        elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
            env_var = obj[2:-1]  # Remove ${ and }
            return os.getenv(env_var)
        else:
            return obj

    return _substitute_recursive(config)


def load_config(config_path="config.yaml"):
    """Load configuration from YAML file."""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {config_path}")

            # Substitute environment variables
            config = substitute_env_variables(config)

            # Merge with defaults to ensure all keys exist
            default_config = get_default_config()
            merged_config = _deep_merge(default_config, config)

            return merged_config
    except FileNotFoundError:
        logger.warning(f"Config file {config_path} not found. Using default settings.")
        return get_default_config()
    except yaml.YAMLError as e:
        logger.error(f"Error parsing config file {config_path}: {e}")
        return get_default_config()


def _deep_merge(default, override):
    """Deep merge two dictionaries, with override taking precedence."""
    result = default.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate daily music recommendations from Last.fm"
    )
    parser.add_argument(
        "--tags",
        nargs="+",
        help="Music tags to search for (e.g., --tags chill ambient lofi)",
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)",
    )
    parser.add_argument(
        "--output-dir", help="Output directory for files (overrides config)"
    )
    parser.add_argument(
        "--num-tracks",
        type=int,
        help="Number of tracks to recommend (overrides config)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set logging level (overrides config)",
    )

    # Platform filtering arguments
    parser.add_argument(
        "--soundcloud-token",
        help="SoundCloud OAuth token for filtering liked tracks (overrides config and env)",
    )
    parser.add_argument(
        "--spotify-token",
        help="Spotify access token for filtering liked tracks (overrides config and env)",
    )
    parser.add_argument(
        "--disable-filtering",
        action="store_true",
        help="Disable platform filtering even if configured",
    )

    return parser.parse_args()


def merge_config_with_args(config, args):
    """Merge configuration with command line arguments."""
    # Override config with command line arguments
    if args.tags:
        config["default_tags"] = args.tags
        logger.info(f"Using tags from command line: {args.tags}")

    if args.output_dir:
        config["output"]["directory"] = args.output_dir
        logger.info(f"Using output directory from command line: {args.output_dir}")

    if args.num_tracks:
        config["num_tracks"] = args.num_tracks
        logger.info(f"Using track count from command line: {args.num_tracks}")

    if args.log_level:
        config["logging"]["level"] = args.log_level
        logger.info(f"Using log level from command line: {args.log_level}")

    # Platform filtering arguments
    if args.disable_filtering:
        config["platform_filtering"]["enabled"] = False
        logger.info("Platform filtering disabled via command line")

    if args.soundcloud_token:
        config["platform_filtering"]["soundcloud"]["oauth_token"] = (
            args.soundcloud_token
        )
        config["platform_filtering"]["soundcloud"]["enabled"] = True
        config["platform_filtering"]["enabled"] = True
        logger.info("Using SoundCloud token from command line")

    if args.spotify_token:
        config["platform_filtering"]["spotify"]["access_token"] = args.spotify_token
        config["platform_filtering"]["spotify"]["enabled"] = True
        config["platform_filtering"]["enabled"] = True
        logger.info("Using Spotify token from command line")

    return config


def validate_platform_filtering_config(config):
    """Validate platform filtering configuration."""
    platform_config = config.get("platform_filtering", {})

    if not platform_config.get("enabled", False):
        logger.debug("Platform filtering is disabled")
        return True

    errors = []

    # Check SoundCloud configuration
    soundcloud_config = platform_config.get("soundcloud", {})
    if soundcloud_config.get("enabled", False):
        if not soundcloud_config.get("oauth_token"):
            errors.append("SoundCloud filtering is enabled but oauth_token is missing")

    # Check Spotify configuration
    spotify_config = platform_config.get("spotify", {})
    if spotify_config.get("enabled", False):
        missing_spotify_fields = []
        if not spotify_config.get("client_id"):
            missing_spotify_fields.append("client_id")
        if not spotify_config.get("client_secret"):
            missing_spotify_fields.append("client_secret")
        if not spotify_config.get("access_token"):
            missing_spotify_fields.append("access_token")

        if missing_spotify_fields:
            errors.append(
                f"Spotify filtering is enabled but missing: {', '.join(missing_spotify_fields)}"
            )

    # Check if filtering is enabled but no platforms are configured
    if platform_config.get("enabled", False):
        if not soundcloud_config.get("enabled", False) and not spotify_config.get(
            "enabled", False
        ):
            errors.append(
                "Platform filtering is enabled but no platforms are configured"
            )

    if errors:
        for error in errors:
            logger.error(f"Configuration error: {error}")
        return False

    logger.info("Platform filtering configuration is valid")
    return True


def setup_logging(config):
    """Setup logging configuration."""
    log_level = getattr(logging, config.get("logging", {}).get("level", "INFO"))
    log_format = config.get("logging", {}).get(
        "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logging.basicConfig(
        level=log_level, format=log_format, handlers=[logging.StreamHandler()]
    )

    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
