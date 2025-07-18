"""Integration tests for complete filtering workflow."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json
from pathlib import Path
from datetime import datetime

from main import create_playlist, create_platform_filter, display_playlist
from entities import Track, Playlist, LastFmApiResponse, FilterResult
from adapter.soundcloud_adapter import SoundCloudAdapter, SoundCloudTrack
from platform_filter import PlatformFilter


class TestFilteringIntegration(unittest.TestCase):
    """Test complete filtering workflow integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.temp_dir)

        # Sample tracks for testing
        self.sample_tracks = [
            Track(name="Chill Song 1", artist="Artist A", url="http://example.com/1"),
            Track(name="Ambient Track", artist="Artist B", url="http://example.com/2"),
            Track(name="Lofi Beat", artist="Artist C", url="http://example.com/3"),
            Track(name="Relaxing Tune", artist="Artist D", url="http://example.com/4"),
            Track(name="Peaceful Sound", artist="Artist E", url="http://example.com/5"),
        ]

        # Sample SoundCloud tracks (some matching, some not)
        self.soundcloud_tracks = [
            SoundCloudTrack(
                id=1,
                title="Chill Song 1",  # Exact match
                user="Artist A",
                permalink_url="http://soundcloud.com/1",
                duration=180000,
            ),
            SoundCloudTrack(
                id=2,
                title="Different Song",  # No match
                user="Different Artist",
                permalink_url="http://soundcloud.com/2",
                duration=200000,
            ),
            SoundCloudTrack(
                id=3,
                title="Lofi Beat (Remix)",  # Fuzzy match
                user="Artist C",
                permalink_url="http://soundcloud.com/3",
                duration=220000,
            ),
        ]

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_platform_filter_enabled(self):
        """Test creating PlatformFilter when filtering is enabled."""
        config = {
            "platform_filtering": {
                "enabled": True,
                "soundcloud": {"enabled": True, "oauth_token": "test_token"},
            }
        }

        with patch("main.SoundCloudAdapter") as mock_adapter_class:
            mock_adapter = Mock()
            mock_adapter_class.return_value = mock_adapter

            platform_filter = create_platform_filter(config)

            self.assertIsNotNone(platform_filter)
            self.assertIsInstance(platform_filter, PlatformFilter)
            mock_adapter_class.assert_called_once_with(oauth_token="test_token")

    def test_create_platform_filter_disabled(self):
        """Test creating PlatformFilter when filtering is disabled."""
        config = {"platform_filtering": {"enabled": False}}

        platform_filter = create_platform_filter(config)
        self.assertIsNone(platform_filter)

    def test_create_platform_filter_no_credentials(self):
        """Test creating PlatformFilter when no credentials are provided."""
        config = {
            "platform_filtering": {
                "enabled": True,
                "soundcloud": {"enabled": True, "oauth_token": None},
            }
        }

        platform_filter = create_platform_filter(config)
        self.assertIsNone(platform_filter)

    def test_create_platform_filter_invalid_config(self):
        """Test creating PlatformFilter with invalid configuration."""
        config = {
            "platform_filtering": {
                "enabled": True,
                # No platforms configured
            }
        }

        platform_filter = create_platform_filter(config)
        self.assertIsNone(platform_filter)

    @patch("main.fetch_tracks_for_tag")
    @patch("main.load_history")
    @patch("main.save_history")
    def test_create_playlist_with_filtering(
        self, mock_save_history, mock_load_history, mock_fetch_tracks
    ):
        """Test complete playlist creation with platform filtering."""
        # Setup mocks
        mock_load_history.return_value = {}

        # Mock API response
        mock_api_response = Mock(spec=LastFmApiResponse)
        mock_api_response.has_error.return_value = False
        mock_api_response.total_tracks = 5
        mock_api_response.filter_seen_tracks.return_value = mock_api_response
        mock_api_response.tracks = self.sample_tracks
        mock_api_response.get_track_count.return_value = 5
        mock_fetch_tracks.return_value = mock_api_response

        # Configuration with filtering enabled
        config = {
            "default_tags": ["chill"],
            "num_tracks": 3,
            "api": {
                "limit_per_tag": 100,
                "base_url": "https://ws.audioscrobbler.com/2.0/",
            },
            "output": {"history_filename": "test_history.json"},
            "display": {"show_fetching_progress": False, "language": "en"},
            "platform_filtering": {
                "enabled": True,
                "soundcloud": {"enabled": True, "oauth_token": "test_token"},
            },
        }

        # Mock SoundCloud adapter and filtering
        with patch("main.SoundCloudAdapter") as mock_adapter_class:
            mock_adapter = Mock()
            mock_adapter_class.return_value = mock_adapter
            mock_adapter.get_user_liked_tracks.return_value = self.soundcloud_tracks
            mock_adapter._normalize_track_for_matching.side_effect = [
                Track(name="Chill Song 1", artist="Artist A", url=""),
                Track(name="Different Song", artist="Different Artist", url=""),
                Track(name="Lofi Beat", artist="Artist C", url=""),
            ]

            # Create playlist
            playlist = create_playlist(["chill"], config, self.output_dir)

            # Verify playlist was created
            self.assertIsInstance(playlist, Playlist)
            self.assertLessEqual(len(playlist.tracks), 3)  # Should be filtered

            # Verify filtering statistics are attached
            self.assertTrue(hasattr(playlist.metadata, "filtering_stats"))
            stats = playlist.metadata.filtering_stats
            self.assertIsInstance(stats, dict)
            self.assertIn("removed_count", stats)
            self.assertIn("soundcloud_matches", stats)

    @patch("main.fetch_tracks_for_tag")
    @patch("main.load_history")
    @patch("main.save_history")
    def test_create_playlist_without_filtering(
        self, mock_save_history, mock_load_history, mock_fetch_tracks
    ):
        """Test playlist creation without platform filtering."""
        # Setup mocks
        mock_load_history.return_value = {}

        # Mock API response
        mock_api_response = Mock(spec=LastFmApiResponse)
        mock_api_response.has_error.return_value = False
        mock_api_response.total_tracks = 5
        mock_api_response.filter_seen_tracks.return_value = mock_api_response
        mock_api_response.tracks = self.sample_tracks
        mock_api_response.get_track_count.return_value = 5
        mock_fetch_tracks.return_value = mock_api_response

        # Configuration with filtering disabled
        config = {
            "default_tags": ["chill"],
            "num_tracks": 3,
            "api": {
                "limit_per_tag": 100,
                "base_url": "https://ws.audioscrobbler.com/2.0/",
            },
            "output": {"history_filename": "test_history.json"},
            "display": {"show_fetching_progress": False, "language": "en"},
            "platform_filtering": {"enabled": False},
        }

        # Create playlist
        playlist = create_playlist(["chill"], config, self.output_dir)

        # Verify playlist was created without filtering
        self.assertIsInstance(playlist, Playlist)
        self.assertEqual(len(playlist.tracks), 3)

        # Verify no filtering statistics are attached
        self.assertFalse(
            hasattr(playlist.metadata, "filtering_stats")
            and playlist.metadata.filtering_stats
        )

    @patch("main.fetch_tracks_for_tag")
    @patch("main.load_history")
    @patch("main.save_history")
    def test_create_playlist_filtering_graceful_fallback(
        self, mock_save_history, mock_load_history, mock_fetch_tracks
    ):
        """Test graceful fallback when platform filtering fails."""
        # Setup mocks
        mock_load_history.return_value = {}

        # Mock API response
        mock_api_response = Mock(spec=LastFmApiResponse)
        mock_api_response.has_error.return_value = False
        mock_api_response.total_tracks = 5
        mock_api_response.filter_seen_tracks.return_value = mock_api_response
        mock_api_response.tracks = self.sample_tracks
        mock_api_response.get_track_count.return_value = 5
        mock_fetch_tracks.return_value = mock_api_response

        # Configuration with filtering enabled
        config = {
            "default_tags": ["chill"],
            "num_tracks": 3,
            "api": {
                "limit_per_tag": 100,
                "base_url": "https://ws.audioscrobbler.com/2.0/",
            },
            "output": {"history_filename": "test_history.json"},
            "display": {"show_fetching_progress": False, "language": "en"},
            "platform_filtering": {
                "enabled": True,
                "soundcloud": {"enabled": True, "oauth_token": "test_token"},
            },
        }

        # Mock SoundCloud adapter to fail
        with patch("main.SoundCloudAdapter") as mock_adapter_class:
            mock_adapter_class.side_effect = Exception("SoundCloud API error")

            # Create playlist - should fallback gracefully
            playlist = create_playlist(["chill"], config, self.output_dir)

            # Verify playlist was still created
            self.assertIsInstance(playlist, Playlist)
            self.assertEqual(len(playlist.tracks), 3)  # All tracks should be included

    def test_display_playlist_with_filtering_stats(self):
        """Test displaying playlist with filtering statistics."""
        # Create a playlist with filtering stats
        tracks = self.sample_tracks[:2]
        playlist = Playlist.create(
            tracks=tracks,
            timestamp="2024-01-01_12-00-00",
            tags=["chill"],
            tracks_requested=3,
            total_available_tracks=5,
            api_limit_per_tag=100,
            language="en",
        )

        # Add filtering statistics
        playlist.metadata.filtering_stats = {
            "removed_count": 2,
            "removal_percentage": 40.0,
            "soundcloud_matches": 2,
            "spotify_matches": 0,
        }

        # Capture output
        import io
        import sys

        captured_output = io.StringIO()
        sys.stdout = captured_output

        try:
            display_playlist(playlist)
            output = captured_output.getvalue()

            # Verify filtering stats are displayed
            self.assertIn("Platform filtering:", output)
            self.assertIn("2 tracks filtered (40.0%)", output)
            self.assertIn("2 SoundCloud matches", output)

        finally:
            sys.stdout = sys.__stdout__

    def test_display_playlist_without_filtering_stats(self):
        """Test displaying playlist without filtering statistics."""
        # Create a playlist without filtering stats
        tracks = self.sample_tracks[:2]
        playlist = Playlist.create(
            tracks=tracks,
            timestamp="2024-01-01_12-00-00",
            tags=["chill"],
            tracks_requested=2,
            total_available_tracks=5,
            api_limit_per_tag=100,
            language="en",
        )

        # Capture output
        import io
        import sys

        captured_output = io.StringIO()
        sys.stdout = captured_output

        try:
            display_playlist(playlist)
            output = captured_output.getvalue()

            # Verify no filtering stats are displayed
            self.assertNotIn("Platform filtering:", output)
            self.assertNotIn("tracks filtered", output)

        finally:
            sys.stdout = sys.__stdout__

    @patch("main.fetch_tracks_for_tag")
    @patch("main.load_history")
    @patch("main.save_history")
    def test_end_to_end_filtering_workflow(
        self, mock_save_history, mock_load_history, mock_fetch_tracks
    ):
        """Test complete end-to-end filtering workflow."""
        # Setup mocks
        mock_load_history.return_value = {}

        # Mock API response with more tracks than requested
        mock_api_response = Mock(spec=LastFmApiResponse)
        mock_api_response.has_error.return_value = False
        mock_api_response.total_tracks = 5
        mock_api_response.filter_seen_tracks.return_value = mock_api_response
        mock_api_response.tracks = self.sample_tracks
        mock_api_response.get_track_count.return_value = 5
        mock_fetch_tracks.return_value = mock_api_response

        # Configuration with filtering enabled
        config = {
            "default_tags": ["chill"],
            "num_tracks": 3,
            "api": {
                "limit_per_tag": 100,
                "base_url": "https://ws.audioscrobbler.com/2.0/",
            },
            "output": {"history_filename": "test_history.json"},
            "display": {"show_fetching_progress": False, "language": "en"},
            "platform_filtering": {
                "enabled": True,
                "soundcloud": {"enabled": True, "oauth_token": "test_token"},
            },
        }

        # Mock SoundCloud adapter with realistic filtering
        with patch("main.SoundCloudAdapter") as mock_adapter_class:
            mock_adapter = Mock()
            mock_adapter_class.return_value = mock_adapter
            mock_adapter.get_user_liked_tracks.return_value = self.soundcloud_tracks

            # Mock normalization to return tracks that will match 2 out of 5 input tracks
            def mock_normalize(sc_track):
                if sc_track.title == "Chill Song 1":
                    return Track(name="Chill Song 1", artist="Artist A", url="")
                elif sc_track.title == "Lofi Beat (Remix)":
                    return Track(name="Lofi Beat", artist="Artist C", url="")
                else:
                    return Track(name=sc_track.title, artist=sc_track.user, url="")

            mock_adapter._normalize_track_for_matching.side_effect = mock_normalize

            # Create playlist with filtering
            playlist = create_playlist(["chill"], config, self.output_dir)

            # Verify end-to-end results
            self.assertIsInstance(playlist, Playlist)
            self.assertLessEqual(
                len(playlist.tracks), 3
            )  # Should have filtered some tracks

            # Verify filtering was applied
            self.assertTrue(hasattr(playlist.metadata, "filtering_stats"))
            stats = playlist.metadata.filtering_stats
            self.assertGreater(
                stats["removed_count"], 0
            )  # Some tracks should be removed
            self.assertGreater(
                stats["soundcloud_matches"], 0
            )  # Should have SoundCloud matches

            # Verify history was saved
            mock_save_history.assert_called_once()


if __name__ == "__main__":
    unittest.main()
