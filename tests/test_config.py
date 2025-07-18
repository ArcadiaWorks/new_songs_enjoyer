"""Unit tests for configuration management."""

import unittest
import tempfile
import os
import yaml
from unittest.mock import patch, MagicMock
from config import (
    get_default_config,
    load_config,
    substitute_env_variables,
    parse_arguments,
    merge_config_with_args,
    validate_platform_filtering_config,
    _deep_merge,
)


class TestConfigurationManagement(unittest.TestCase):
    """Test cases for configuration management."""

    def setUp(self):
        """Set up test data."""
        self.sample_config = {
            "default_tags": ["test", "music"],
            "num_tracks": 10,
            "platform_filtering": {
                "enabled": True,
                "soundcloud": {
                    "enabled": True,
                    "oauth_token": "test_token",
                },
                "spotify": {
                    "enabled": False,
                    "client_id": None,
                    "client_secret": None,
                    "access_token": None,
                },
            },
        }

    def test_get_default_config(self):
        """Test getting default configuration."""
        config = get_default_config()

        # Check basic structure
        self.assertIn("default_tags", config)
        self.assertIn("num_tracks", config)
        self.assertIn("platform_filtering", config)

        # Check platform filtering defaults
        pf_config = config["platform_filtering"]
        self.assertFalse(pf_config["enabled"])
        self.assertFalse(pf_config["soundcloud"]["enabled"])
        self.assertFalse(pf_config["spotify"]["enabled"])
        self.assertIsNone(pf_config["soundcloud"]["oauth_token"])
        self.assertIsNone(pf_config["spotify"]["client_id"])

    def test_substitute_env_variables_simple(self):
        """Test environment variable substitution."""
        config = {
            "test_var": "${TEST_ENV_VAR}",
            "normal_var": "normal_value",
        }

        with patch.dict(os.environ, {"TEST_ENV_VAR": "substituted_value"}):
            result = substitute_env_variables(config)

        self.assertEqual(result["test_var"], "substituted_value")
        self.assertEqual(result["normal_var"], "normal_value")

    def test_substitute_env_variables_nested(self):
        """Test environment variable substitution in nested structures."""
        config = {
            "platform_filtering": {
                "soundcloud": {
                    "oauth_token": "${SOUNDCLOUD_OAUTH_TOKEN}",
                },
                "spotify": {
                    "client_id": "${SPOTIFY_CLIENT_ID}",
                    "client_secret": "${SPOTIFY_CLIENT_SECRET}",
                },
            },
        }

        env_vars = {
            "SOUNDCLOUD_OAUTH_TOKEN": "sc_token_123",
            "SPOTIFY_CLIENT_ID": "spotify_id_456",
            "SPOTIFY_CLIENT_SECRET": "spotify_secret_789",
        }

        with patch.dict(os.environ, env_vars):
            result = substitute_env_variables(config)

        self.assertEqual(
            result["platform_filtering"]["soundcloud"]["oauth_token"], "sc_token_123"
        )
        self.assertEqual(
            result["platform_filtering"]["spotify"]["client_id"], "spotify_id_456"
        )
        self.assertEqual(
            result["platform_filtering"]["spotify"]["client_secret"],
            "spotify_secret_789",
        )

    def test_substitute_env_variables_missing_env(self):
        """Test environment variable substitution with missing variables."""
        config = {
            "test_var": "${MISSING_ENV_VAR}",
        }

        result = substitute_env_variables(config)
        self.assertIsNone(result["test_var"])

    def test_substitute_env_variables_list(self):
        """Test environment variable substitution in lists."""
        config = {
            "test_list": ["${TEST_VAR}", "normal_value", "${ANOTHER_VAR}"],
        }

        with patch.dict(os.environ, {"TEST_VAR": "sub1", "ANOTHER_VAR": "sub2"}):
            result = substitute_env_variables(config)

        self.assertEqual(result["test_list"], ["sub1", "normal_value", "sub2"])

    def test_deep_merge(self):
        """Test deep merging of dictionaries."""
        default = {
            "a": 1,
            "b": {"c": 2, "d": 3},
            "e": [1, 2, 3],
        }

        override = {
            "b": {"c": 20},  # Should override c but keep d
            "f": 4,  # Should add new key
        }

        result = _deep_merge(default, override)

        self.assertEqual(result["a"], 1)
        self.assertEqual(result["b"]["c"], 20)  # Overridden
        self.assertEqual(result["b"]["d"], 3)  # Preserved
        self.assertEqual(result["e"], [1, 2, 3])  # Preserved
        self.assertEqual(result["f"], 4)  # Added

    def test_load_config_file_not_found(self):
        """Test loading config when file doesn't exist."""
        with patch("config.logger"):
            config = load_config("nonexistent.yaml")

        # Should return default config
        default_config = get_default_config()
        self.assertEqual(config, default_config)

    def test_load_config_valid_file(self):
        """Test loading config from valid YAML file."""
        test_config = {
            "num_tracks": 15,
            "platform_filtering": {
                "enabled": True,
                "soundcloud": {
                    "enabled": True,
                    "oauth_token": "${SOUNDCLOUD_OAUTH_TOKEN}",
                },
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(test_config, f)
            temp_path = f.name

        try:
            with patch.dict(os.environ, {"SOUNDCLOUD_OAUTH_TOKEN": "test_token"}):
                with patch("config.logger"):
                    config = load_config(temp_path)

            # Should merge with defaults and substitute env vars
            self.assertEqual(config["num_tracks"], 15)
            self.assertTrue(config["platform_filtering"]["enabled"])
            self.assertEqual(
                config["platform_filtering"]["soundcloud"]["oauth_token"], "test_token"
            )
            # Should have default values for missing keys
            self.assertIn("default_tags", config)

        finally:
            os.unlink(temp_path)

    def test_load_config_invalid_yaml(self):
        """Test loading config with invalid YAML."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = f.name

        try:
            with patch("config.logger"):
                config = load_config(temp_path)

            # Should return default config
            default_config = get_default_config()
            self.assertEqual(config, default_config)

        finally:
            os.unlink(temp_path)

    @patch("argparse.ArgumentParser.parse_args")
    def test_parse_arguments_basic(self, mock_parse_args):
        """Test basic argument parsing."""
        mock_args = MagicMock()
        mock_args.tags = ["chill", "ambient"]
        mock_args.config = "test.yaml"
        mock_args.output_dir = "test_output"
        mock_args.num_tracks = 25
        mock_args.log_level = "DEBUG"
        mock_args.soundcloud_token = "sc_token"
        mock_args.spotify_token = "spotify_token"
        mock_args.disable_filtering = False
        mock_parse_args.return_value = mock_args

        args = parse_arguments()

        self.assertEqual(args.tags, ["chill", "ambient"])
        self.assertEqual(args.config, "test.yaml")
        self.assertEqual(args.output_dir, "test_output")
        self.assertEqual(args.num_tracks, 25)
        self.assertEqual(args.log_level, "DEBUG")
        self.assertEqual(args.soundcloud_token, "sc_token")
        self.assertEqual(args.spotify_token, "spotify_token")
        self.assertFalse(args.disable_filtering)

    def test_merge_config_with_args_basic(self):
        """Test merging config with basic arguments."""
        config = get_default_config()

        mock_args = MagicMock()
        mock_args.tags = ["test", "music"]
        mock_args.output_dir = "test_output"
        mock_args.num_tracks = 30
        mock_args.log_level = "WARNING"
        mock_args.soundcloud_token = None
        mock_args.spotify_token = None
        mock_args.disable_filtering = False

        with patch("config.logger"):
            result = merge_config_with_args(config, mock_args)

        self.assertEqual(result["default_tags"], ["test", "music"])
        self.assertEqual(result["output"]["directory"], "test_output")
        self.assertEqual(result["num_tracks"], 30)
        self.assertEqual(result["logging"]["level"], "WARNING")

    def test_merge_config_with_args_platform_filtering(self):
        """Test merging config with platform filtering arguments."""
        config = get_default_config()

        mock_args = MagicMock()
        mock_args.tags = None
        mock_args.output_dir = None
        mock_args.num_tracks = None
        mock_args.log_level = None
        mock_args.soundcloud_token = "sc_token_123"
        mock_args.spotify_token = "spotify_token_456"
        mock_args.disable_filtering = False

        with patch("config.logger"):
            result = merge_config_with_args(config, mock_args)

        # Should enable platform filtering and set tokens
        self.assertTrue(result["platform_filtering"]["enabled"])
        self.assertTrue(result["platform_filtering"]["soundcloud"]["enabled"])
        self.assertTrue(result["platform_filtering"]["spotify"]["enabled"])
        self.assertEqual(
            result["platform_filtering"]["soundcloud"]["oauth_token"], "sc_token_123"
        )
        self.assertEqual(
            result["platform_filtering"]["spotify"]["access_token"], "spotify_token_456"
        )

    def test_merge_config_with_args_disable_filtering(self):
        """Test disabling filtering via command line."""
        config = get_default_config()
        config["platform_filtering"]["enabled"] = True  # Start with enabled

        mock_args = MagicMock()
        mock_args.tags = None
        mock_args.output_dir = None
        mock_args.num_tracks = None
        mock_args.log_level = None
        mock_args.soundcloud_token = None
        mock_args.spotify_token = None
        mock_args.disable_filtering = True

        with patch("config.logger"):
            result = merge_config_with_args(config, mock_args)

        # Should disable platform filtering
        self.assertFalse(result["platform_filtering"]["enabled"])

    def test_validate_platform_filtering_config_disabled(self):
        """Test validation when platform filtering is disabled."""
        config = {"platform_filtering": {"enabled": False}}

        with patch("config.logger"):
            result = validate_platform_filtering_config(config)

        self.assertTrue(result)

    def test_validate_platform_filtering_config_valid_soundcloud(self):
        """Test validation with valid SoundCloud configuration."""
        config = {
            "platform_filtering": {
                "enabled": True,
                "soundcloud": {
                    "enabled": True,
                    "oauth_token": "valid_token",
                },
                "spotify": {
                    "enabled": False,
                },
            }
        }

        with patch("config.logger"):
            result = validate_platform_filtering_config(config)

        self.assertTrue(result)

    def test_validate_platform_filtering_config_valid_spotify(self):
        """Test validation with valid Spotify configuration."""
        config = {
            "platform_filtering": {
                "enabled": True,
                "soundcloud": {
                    "enabled": False,
                },
                "spotify": {
                    "enabled": True,
                    "client_id": "client_id",
                    "client_secret": "client_secret",
                    "access_token": "access_token",
                },
            }
        }

        with patch("config.logger"):
            result = validate_platform_filtering_config(config)

        self.assertTrue(result)

    def test_validate_platform_filtering_config_missing_soundcloud_token(self):
        """Test validation fails with missing SoundCloud token."""
        config = {
            "platform_filtering": {
                "enabled": True,
                "soundcloud": {
                    "enabled": True,
                    "oauth_token": None,
                },
                "spotify": {
                    "enabled": False,
                },
            }
        }

        with patch("config.logger"):
            result = validate_platform_filtering_config(config)

        self.assertFalse(result)

    def test_validate_platform_filtering_config_missing_spotify_credentials(self):
        """Test validation fails with missing Spotify credentials."""
        config = {
            "platform_filtering": {
                "enabled": True,
                "soundcloud": {
                    "enabled": False,
                },
                "spotify": {
                    "enabled": True,
                    "client_id": None,
                    "client_secret": "secret",
                    "access_token": "token",
                },
            }
        }

        with patch("config.logger"):
            result = validate_platform_filtering_config(config)

        self.assertFalse(result)

    def test_validate_platform_filtering_config_no_platforms_enabled(self):
        """Test validation fails when filtering is enabled but no platforms are configured."""
        config = {
            "platform_filtering": {
                "enabled": True,
                "soundcloud": {
                    "enabled": False,
                },
                "spotify": {
                    "enabled": False,
                },
            }
        }

        with patch("config.logger"):
            result = validate_platform_filtering_config(config)

        self.assertFalse(result)

    def test_validate_platform_filtering_config_both_platforms(self):
        """Test validation with both platforms enabled and valid."""
        config = {
            "platform_filtering": {
                "enabled": True,
                "soundcloud": {
                    "enabled": True,
                    "oauth_token": "sc_token",
                },
                "spotify": {
                    "enabled": True,
                    "client_id": "client_id",
                    "client_secret": "client_secret",
                    "access_token": "access_token",
                },
            }
        }

        with patch("config.logger"):
            result = validate_platform_filtering_config(config)

        self.assertTrue(result)

    def test_validate_platform_filtering_config_missing_config_section(self):
        """Test validation with missing platform_filtering section."""
        config = {}

        with patch("config.logger"):
            result = validate_platform_filtering_config(config)

        self.assertTrue(
            result
        )  # Should pass when section is missing (disabled by default)


if __name__ == "__main__":
    unittest.main()
