"""Configuration management for new_songs_enjoyer."""

import argparse
import yaml
import logging
from pathlib import Path

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
    }


def load_config(config_path="config.yaml"):
    """Load configuration from YAML file."""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {config_path}")
            return config
    except FileNotFoundError:
        logger.warning(f"Config file {config_path} not found. Using default settings.")
        return get_default_config()
    except yaml.YAMLError as e:
        logger.error(f"Error parsing config file {config_path}: {e}")
        return get_default_config()


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

    return config


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
