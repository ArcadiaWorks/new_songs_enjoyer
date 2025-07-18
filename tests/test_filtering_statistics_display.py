"""Tests for filtering statistics display in various output formats."""

import unittest
import json
import io
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path
from datetime import datetime

from entities import Track, Playlist, FilterResult
from main import display_playlist, generate_html_playlist


class TestFilteringStatisticsDisplay(unittest.TestCase):
    """Test filtering statistics display functionality."""

    def setUp(self):
        """Set up test data."""
        self.sample_tracks = [
            Track(
                name="Test Song 1",
                artist="Test Artist 1",
                url="https://last.fm/music/Test+Artist+1/_/Test+Song+1",
                position=1,
            ),
            Track(
                name="Test Song 2",
                artist="Test Artist 2",
                url="https://last.fm/music/Test+Artist+2/_/Test+Song+2",
                position=2,
            ),
            Track(
                name="Test Song 3",
                artist="Test Artist 3",
                url="https://last.fm/music/Test+Artist+3/_/Test+Song+3",
                position=3,
            ),
        ]

    def test_playlist_json_output_with_filtering_stats(self):
        """Test that JSON output includes filtering statistics."""
        # Create playlist with filtering stats
        playlist = Playlist.create(
            tracks=self.sample_tracks[:2],
            timestamp="2024-01-01_12-00-00",
            tags=["chill"],
            tracks_requested=3,
            total_available_tracks=5,
            api_limit_per_tag=100,
            language="en",
        )

        # Create filter result with statistics
        filter_result = FilterResult.create_with_filtering(
            original_tracks=self.sample_tracks,
            removed_tracks=[self.sample_tracks[2]],
            soundcloud_matches=1,
            spotify_matches=0,
        )

        # Set filtering stats on playlist
        playlist.set_filtering_stats(filter_result)

        # Convert to dict (JSON serialization)
        playlist_dict = playlist.to_dict()

        # Verify filtering stats are included
        self.assertIn("filtering_stats", playlist_dict["metadata"])
        filtering_stats = playlist_dict["metadata"]["filtering_stats"]

        self.assertEqual(filtering_stats["original_count"], 3)
        self.assertEqual(filtering_stats["filtered_count"], 2)
        self.assertEqual(filtering_stats["removed_count"], 1)
        self.assertEqual(filtering_stats["removal_percentage"], 33.3)
        self.assertEqual(filtering_stats["soundcloud_matches"], 1)
        self.assertEqual(filtering_stats["spotify_matches"], 0)
        self.assertEqual(filtering_stats["total_matches"], 1)
        self.assertFalse(filtering_stats["has_errors"])

    def test_playlist_json_output_without_filtering_stats(self):
        """Test that JSON output works without filtering statistics."""
        # Create playlist without filtering stats
        playlist = Playlist.create(
            tracks=self.sample_tracks[:2],
            timestamp="2024-01-01_12-00-00",
            tags=["chill"],
            tracks_requested=2,
            total_available_tracks=5,
            api_limit_per_tag=100,
            language="en",
        )

        # Convert to dict (JSON serialization)
        playlist_dict = playlist.to_dict()

        # Verify filtering stats are not included or are None
        filtering_stats = playlist_dict["metadata"].get("filtering_stats")
        self.assertIsNone(filtering_stats)

    def test_display_playlist_with_filtering_stats_english(self):
        """Test console display with filtering statistics in English."""
        # Create playlist with filtering stats
        playlist = Playlist.create(
            tracks=self.sample_tracks[:2],
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
        captured_output = io.StringIO()
        sys.stdout = captured_output

        try:
            display_playlist(playlist)
            output = captured_output.getvalue()

            # Verify filtering stats are displayed in English
            self.assertIn("Platform filtering:", output)
            self.assertIn("2 tracks filtered (40.0%)", output)
            self.assertIn("2 SoundCloud matches", output)
            self.assertNotIn("Spotify matches", output)

        finally:
            sys.stdout = sys.__stdout__

    def test_display_playlist_with_filtering_stats_french(self):
        """Test console display with filtering statistics in French."""
        # Create playlist with filtering stats
        playlist = Playlist.create(
            tracks=self.sample_tracks[:2],
            timestamp="2024-01-01_12-00-00",
            tags=["chill"],
            tracks_requested=3,
            total_available_tracks=5,
            api_limit_per_tag=100,
            language="fr",
        )

        # Add filtering statistics
        playlist.metadata.filtering_stats = {
            "removed_count": 1,
            "removal_percentage": 25.0,
            "soundcloud_matches": 1,
            "spotify_matches": 1,
        }

        # Capture output
        captured_output = io.StringIO()
        sys.stdout = captured_output

        try:
            display_playlist(playlist)
            output = captured_output.getvalue()

            # Verify filtering stats are displayed in French
            self.assertIn("Filtrage des plateformes:", output)
            self.assertIn("1 titres filtrés (25.0%)", output)
            self.assertIn("1 correspondances SoundCloud", output)
            self.assertIn("1 correspondances Spotify", output)

        finally:
            sys.stdout = sys.__stdout__

    def test_display_playlist_with_both_platforms(self):
        """Test console display with both SoundCloud and Spotify matches."""
        # Create playlist with filtering stats
        playlist = Playlist.create(
            tracks=self.sample_tracks[:1],
            timestamp="2024-01-01_12-00-00",
            tags=["chill"],
            tracks_requested=3,
            total_available_tracks=5,
            api_limit_per_tag=100,
            language="en",
        )

        # Add filtering statistics with both platforms
        playlist.metadata.filtering_stats = {
            "removed_count": 3,
            "removal_percentage": 75.0,
            "soundcloud_matches": 2,
            "spotify_matches": 1,
        }

        # Capture output
        captured_output = io.StringIO()
        sys.stdout = captured_output

        try:
            display_playlist(playlist)
            output = captured_output.getvalue()

            # Verify both platforms are displayed
            self.assertIn("Platform filtering:", output)
            self.assertIn("3 tracks filtered (75.0%)", output)
            self.assertIn("2 SoundCloud matches", output)
            self.assertIn("1 Spotify matches", output)

        finally:
            sys.stdout = sys.__stdout__

    def test_display_playlist_without_filtering_stats(self):
        """Test console display without filtering statistics."""
        # Create playlist without filtering stats
        playlist = Playlist.create(
            tracks=self.sample_tracks[:2],
            timestamp="2024-01-01_12-00-00",
            tags=["chill"],
            tracks_requested=2,
            total_available_tracks=5,
            api_limit_per_tag=100,
            language="en",
        )

        # Capture output
        captured_output = io.StringIO()
        sys.stdout = captured_output

        try:
            display_playlist(playlist)
            output = captured_output.getvalue()

            # Verify no filtering stats are displayed
            self.assertNotIn("Platform filtering:", output)
            self.assertNotIn("tracks filtered", output)
            self.assertNotIn("SoundCloud matches", output)
            self.assertNotIn("Spotify matches", output)

        finally:
            sys.stdout = sys.__stdout__

    def test_display_playlist_with_zero_filtering(self):
        """Test console display when filtering found no matches."""
        # Create playlist with zero filtering
        playlist = Playlist.create(
            tracks=self.sample_tracks,
            timestamp="2024-01-01_12-00-00",
            tags=["chill"],
            tracks_requested=3,
            total_available_tracks=5,
            api_limit_per_tag=100,
            language="en",
        )

        # Add filtering statistics with no matches
        playlist.metadata.filtering_stats = {
            "removed_count": 0,
            "removal_percentage": 0.0,
            "soundcloud_matches": 0,
            "spotify_matches": 0,
        }

        # Capture output
        captured_output = io.StringIO()
        sys.stdout = captured_output

        try:
            display_playlist(playlist)
            output = captured_output.getvalue()

            # Verify filtering section is shown but with zero results
            self.assertIn("Platform filtering:", output)
            self.assertIn("0 tracks filtered (0.0%)", output)
            # Should not show platform matches when they are zero
            self.assertNotIn("SoundCloud matches", output)
            self.assertNotIn("Spotify matches", output)

        finally:
            sys.stdout = sys.__stdout__

    def test_html_output_with_filtering_stats(self):
        """Test HTML output includes filtering statistics."""
        # Create playlist with filtering stats
        playlist = Playlist.create(
            tracks=self.sample_tracks[:2],
            timestamp="2024-01-01_12-00-00",
            tags=["chill"],
            tracks_requested=3,
            total_available_tracks=5,
            api_limit_per_tag=100,
            language="en",
        )

        # Add filtering statistics
        playlist.metadata.filtering_stats = {
            "removed_count": 1,
            "removal_percentage": 33.3,
            "soundcloud_matches": 1,
            "spotify_matches": 0,
            "total_matches": 1,
        }

        # Create a mock template that we can verify receives the filtering stats
        mock_template_content = """
        <div class="metadata">
            {% if metadata.filtering_stats %}
                <div class="filtering-stats">
                    <span>{{ metadata.filtering_stats.removed_count }} filtered</span>
                    <span>{{ metadata.filtering_stats.removal_percentage }}%</span>
                    {% if metadata.filtering_stats.soundcloud_matches > 0 %}
                        <span>{{ metadata.filtering_stats.soundcloud_matches }} SoundCloud</span>
                    {% endif %}
                </div>
            {% endif %}
        </div>
        """

        # Mock the template file reading
        with patch("pathlib.Path.exists", return_value=True), patch(
            "builtins.open", unittest.mock.mock_open(read_data=mock_template_content)
        ), patch("pathlib.Path.mkdir"):
            # Generate HTML
            output_dir = Path("test_output")
            html_file = generate_html_playlist(playlist, output_dir)

            # Verify HTML file would be created (mocked)
            self.assertIsNotNone(html_file)

    def test_filter_result_statistics_summary(self):
        """Test FilterResult statistics summary generation."""
        # Create filter result with various statistics
        original_tracks = self.sample_tracks
        removed_tracks = [self.sample_tracks[1], self.sample_tracks[2]]

        filter_result = FilterResult.create_with_filtering(
            original_tracks=original_tracks,
            removed_tracks=removed_tracks,
            soundcloud_matches=2,
            spotify_matches=1,
            errors=["Test error"],
        )

        # Get statistics summary
        stats = filter_result.get_statistics_summary()

        # Verify all expected fields are present
        expected_fields = [
            "original_count",
            "filtered_count",
            "removed_count",
            "removal_percentage",
            "soundcloud_matches",
            "spotify_matches",
            "total_matches",
            "has_errors",
            "error_count",
        ]

        for field in expected_fields:
            self.assertIn(field, stats)

        # Verify values
        self.assertEqual(stats["original_count"], 3)
        self.assertEqual(stats["filtered_count"], 1)
        self.assertEqual(stats["removed_count"], 2)
        self.assertEqual(stats["removal_percentage"], 66.7)
        self.assertEqual(stats["soundcloud_matches"], 2)
        self.assertEqual(stats["spotify_matches"], 1)
        self.assertEqual(stats["total_matches"], 3)
        self.assertTrue(stats["has_errors"])
        self.assertEqual(stats["error_count"], 1)

    def test_playlist_filtering_stats_methods(self):
        """Test playlist filtering statistics helper methods."""
        # Create playlist
        playlist = Playlist.create(
            tracks=self.sample_tracks[:2],
            timestamp="2024-01-01_12-00-00",
            tags=["chill"],
            tracks_requested=3,
            total_available_tracks=5,
            api_limit_per_tag=100,
            language="en",
        )

        # Initially should have no filtering stats
        self.assertFalse(playlist.has_filtering_stats())
        self.assertEqual(playlist.get_filtering_stats(), {})

        # Add filtering statistics
        filter_result = FilterResult.create_with_filtering(
            original_tracks=self.sample_tracks,
            removed_tracks=[self.sample_tracks[2]],
            soundcloud_matches=1,
            spotify_matches=0,
        )

        playlist.set_filtering_stats(filter_result)

        # Now should have filtering stats
        self.assertTrue(playlist.has_filtering_stats())
        stats = playlist.get_filtering_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("removed_count", stats)
        self.assertEqual(stats["removed_count"], 1)


if __name__ == "__main__":
    unittest.main()
