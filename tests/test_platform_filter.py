"""Unit tests for PlatformFilter class."""

import unittest
from unittest.mock import Mock, patch
import logging

from entities import Track, FilterResult
from adapter.soundcloud_adapter import SoundCloudAdapter, SoundCloudTrack
from platform_filter import PlatformFilter

# Disable logging during tests
logging.disable(logging.CRITICAL)


class TestPlatformFilter(unittest.TestCase):
    """Test cases for PlatformFilter class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_soundcloud_adapter = Mock(spec=SoundCloudAdapter)
        self.platform_filter = PlatformFilter(
            soundcloud_adapter=self.mock_soundcloud_adapter
        )

    def test_init_with_soundcloud_adapter(self):
        """Test PlatformFilter initialization with SoundCloud adapter."""
        filter_instance = PlatformFilter(
            soundcloud_adapter=self.mock_soundcloud_adapter
        )
        self.assertEqual(
            filter_instance.soundcloud_adapter, self.mock_soundcloud_adapter
        )
        self.assertIsNone(filter_instance._soundcloud_favorites_cache)

    def test_init_without_soundcloud_adapter(self):
        """Test PlatformFilter initialization without SoundCloud adapter."""
        filter_instance = PlatformFilter()
        self.assertIsNone(filter_instance.soundcloud_adapter)
        self.assertIsNone(filter_instance._soundcloud_favorites_cache)

    def test_filter_tracks_no_adapter(self):
        """Test filtering tracks when no SoundCloud adapter is available."""
        filter_instance = PlatformFilter()
        tracks = [
            Track(name="Song 1", artist="Artist 1"),
            Track(name="Song 2", artist="Artist 2"),
        ]

        result = filter_instance.filter_tracks(tracks)

        self.assertIsInstance(result, FilterResult)
        self.assertEqual(result.original_count, 2)
        self.assertEqual(len(result.filtered_tracks), 2)
        self.assertEqual(len(result.removed_tracks), 0)
        self.assertEqual(result.soundcloud_matches, 0)
        self.assertEqual(result.spotify_matches, 0)
        self.assertEqual(len(result.errors), 0)

    def test_filter_tracks_with_matches(self):
        """Test filtering tracks with SoundCloud matches."""
        # Mock SoundCloud favorites
        soundcloud_favorites = [
            Track(name="Matched Song", artist="Matched Artist"),
            Track(name="Another Match", artist="Another Artist"),
        ]

        with patch.object(
            self.platform_filter,
            "get_soundcloud_favorites",
            return_value=soundcloud_favorites,
        ):
            tracks = [
                Track(
                    name="Matched Song", artist="Matched Artist"
                ),  # Should be removed
                Track(name="Unique Song", artist="Unique Artist"),  # Should remain
                Track(
                    name="Another Match", artist="Another Artist"
                ),  # Should be removed
            ]

            result = self.platform_filter.filter_tracks(tracks)

            self.assertEqual(result.original_count, 3)
            self.assertEqual(len(result.filtered_tracks), 1)
            self.assertEqual(len(result.removed_tracks), 2)
            self.assertEqual(result.soundcloud_matches, 2)
            self.assertEqual(result.filtered_tracks[0].name, "Unique Song")

    def test_filter_tracks_no_matches(self):
        """Test filtering tracks with no SoundCloud matches."""
        soundcloud_favorites = [
            Track(name="Different Song", artist="Different Artist"),
        ]

        with patch.object(
            self.platform_filter,
            "get_soundcloud_favorites",
            return_value=soundcloud_favorites,
        ):
            tracks = [
                Track(name="Unique Song 1", artist="Unique Artist 1"),
                Track(name="Unique Song 2", artist="Unique Artist 2"),
            ]

            result = self.platform_filter.filter_tracks(tracks)

            self.assertEqual(result.original_count, 2)
            self.assertEqual(len(result.filtered_tracks), 2)
            self.assertEqual(len(result.removed_tracks), 0)
            self.assertEqual(result.soundcloud_matches, 0)

    def test_get_soundcloud_favorites_no_adapter(self):
        """Test getting SoundCloud favorites when no adapter is available."""
        filter_instance = PlatformFilter()
        favorites = filter_instance.get_soundcloud_favorites()
        self.assertEqual(favorites, [])

    def test_get_soundcloud_favorites_success(self):
        """Test successfully getting SoundCloud favorites."""
        # Mock SoundCloud tracks
        mock_sc_tracks = [
            SoundCloudTrack(
                id=1,
                title="Test Song 1",
                user="Test Artist 1",
                permalink_url="https://soundcloud.com/test1",
                duration=180000,
            ),
            SoundCloudTrack(
                id=2,
                title="Test Song 2",
                user="Test Artist 2",
                permalink_url="https://soundcloud.com/test2",
                duration=200000,
            ),
        ]

        # Mock the adapter methods and properties
        self.mock_soundcloud_adapter.oauth_token = "valid_token"
        self.mock_soundcloud_adapter.get_user_profile.return_value = {
            "username": "testuser"
        }
        self.mock_soundcloud_adapter.get_user_liked_tracks.return_value = mock_sc_tracks
        self.mock_soundcloud_adapter._normalize_track_for_matching.side_effect = [
            Track(name="Test Song 1", artist="Test Artist 1"),
            Track(name="Test Song 2", artist="Test Artist 2"),
        ]

        favorites = self.platform_filter.get_soundcloud_favorites()

        self.assertEqual(len(favorites), 2)
        self.assertEqual(favorites[0].name, "Test Song 1")
        self.assertEqual(favorites[0].artist, "Test Artist 1")
        self.assertEqual(favorites[1].name, "Test Song 2")
        self.assertEqual(favorites[1].artist, "Test Artist 2")

        # Test caching - second call should not hit the adapter
        self.mock_soundcloud_adapter.get_user_liked_tracks.reset_mock()
        favorites_cached = self.platform_filter.get_soundcloud_favorites()
        self.assertEqual(favorites_cached, favorites)
        self.mock_soundcloud_adapter.get_user_liked_tracks.assert_not_called()

    def test_get_soundcloud_favorites_error(self):
        """Test handling errors when getting SoundCloud favorites."""
        # Mock the adapter to have a valid token but fail on API call
        self.mock_soundcloud_adapter.oauth_token = "valid_token"
        self.mock_soundcloud_adapter.get_user_profile.return_value = {
            "username": "testuser"
        }
        self.mock_soundcloud_adapter.get_user_liked_tracks.side_effect = Exception(
            "API Error"
        )

        # Should raise SoundCloudAPIError due to the new error handling
        from platform_filter import SoundCloudAPIError

        with self.assertRaises(SoundCloudAPIError):
            self.platform_filter.get_soundcloud_favorites()

        # Should cache empty list after error
        self.assertEqual(self.platform_filter._soundcloud_favorites_cache, [])

    def test_match_tracks_exact_match(self):
        """Test exact track matching (case-insensitive)."""
        lastfm_track = Track(name="Test Song", artist="Test Artist")
        platform_tracks = [
            Track(name="Different Song", artist="Different Artist"),
            Track(
                name="TEST SONG", artist="TEST ARTIST"
            ),  # Should match (case-insensitive)
        ]

        result = self.platform_filter._match_tracks(lastfm_track, platform_tracks)
        self.assertTrue(result)

    def test_match_tracks_fuzzy_match(self):
        """Test fuzzy track matching."""
        lastfm_track = Track(name="Test Song", artist="Test Artist")
        platform_tracks = [
            Track(
                name="Test Song (Remastered)", artist="Test Artist"
            ),  # Should match after normalization
        ]

        result = self.platform_filter._match_tracks(lastfm_track, platform_tracks)
        self.assertTrue(result)

    def test_match_tracks_no_match(self):
        """Test when no tracks match."""
        lastfm_track = Track(name="Test Song", artist="Test Artist")
        platform_tracks = [
            Track(name="Completely Different", artist="Different Artist"),
            Track(name="Another Song", artist="Another Artist"),
        ]

        result = self.platform_filter._match_tracks(lastfm_track, platform_tracks)
        self.assertFalse(result)

    def test_match_tracks_empty_platform_list(self):
        """Test matching against empty platform tracks list."""
        lastfm_track = Track(name="Test Song", artist="Test Artist")
        platform_tracks = []

        result = self.platform_filter._match_tracks(lastfm_track, platform_tracks)
        self.assertFalse(result)

    def test_normalize_track_for_comparison(self):
        """Test track normalization for comparison."""
        track = Track(
            name="Test Song (Remastered 2021) [feat. Another Artist]",
            artist="Test Artist (Official)",
        )

        normalized = self.platform_filter._normalize_track_for_comparison(track)

        # Should remove remastered info, featuring info, and parentheses
        self.assertEqual(normalized.name, "Test Song")
        self.assertEqual(normalized.artist, "Test Artist")

    def test_clean_track_name(self):
        """Test track name cleaning."""
        test_cases = [
            ("Song Name", "Song Name"),
            ("Song Name (Remastered)", "Song Name"),
            ("Song Name [Official Video]", "Song Name"),
            ("Song Name - Remastered 2021", "Song Name"),
            ("Song Name (feat. Artist)", "Song Name"),
            ("Song Name ft. Artist", "Song Name"),
            ("Song Name with Artist", "Song Name"),
            ("Song Name (Remastered) [feat. Artist] - 2021", "Song Name"),
        ]

        for input_name, expected in test_cases:
            with self.subTest(input_name=input_name):
                result = self.platform_filter._clean_track_name(input_name)
                self.assertEqual(result, expected)

    def test_clean_artist_name(self):
        """Test artist name cleaning."""
        test_cases = [
            ("Artist Name", "Artist Name"),
            ("Artist Name (Official)", "Artist Name"),
            ("Artist Name [Records]", "Artist Name"),
            ("Artist Name (Official) [Records]", "Artist Name"),
        ]

        for input_name, expected in test_cases:
            with self.subTest(input_name=input_name):
                result = self.platform_filter._clean_artist_name(input_name)
                self.assertEqual(result, expected)

    def test_calculate_track_similarity(self):
        """Test track similarity calculation."""
        track1 = Track(name="Test Song", artist="Test Artist")

        # Exact match should have high similarity
        track2 = Track(name="Test Song", artist="Test Artist")
        similarity = self.platform_filter._calculate_track_similarity(track1, track2)
        self.assertGreaterEqual(similarity, 0.9)

        # Partial match should have medium similarity
        track3 = Track(name="Test Song Remix", artist="Test Artist")
        similarity = self.platform_filter._calculate_track_similarity(track1, track3)
        self.assertGreater(similarity, 0.7)
        self.assertLess(similarity, 1.0)

        # No match should have low similarity
        track4 = Track(name="Completely Different", artist="Different Artist")
        similarity = self.platform_filter._calculate_track_similarity(track1, track4)
        self.assertLess(similarity, 0.5)

    def test_filter_tracks_with_error_handling(self):
        """Test error handling during filtering."""
        with patch.object(
            self.platform_filter,
            "get_soundcloud_favorites",
            side_effect=Exception("Test Error"),
        ):
            tracks = [Track(name="Test Song", artist="Test Artist")]

            result = self.platform_filter.filter_tracks(tracks)

            # Should return original tracks when filtering fails
            self.assertEqual(len(result.filtered_tracks), 1)
            self.assertEqual(len(result.errors), 1)
            self.assertIn("unexpected error", result.errors[0])

    def test_filter_result_to_dict(self):
        """Test FilterResult serialization to dictionary."""
        tracks = [Track(name="Test Song", artist="Test Artist")]
        removed = [Track(name="Removed Song", artist="Removed Artist")]

        result = FilterResult(
            original_count=2,
            filtered_tracks=tracks,
            removed_tracks=removed,
            soundcloud_matches=1,
            spotify_matches=0,
            errors=["Test error"],
        )

        result_dict = result.to_dict()

        self.assertEqual(result_dict["original_count"], 2)
        self.assertEqual(result_dict["filtered_count"], 1)
        self.assertEqual(result_dict["removed_count"], 1)
        self.assertEqual(result_dict["soundcloud_matches"], 1)
        self.assertEqual(result_dict["spotify_matches"], 0)
        self.assertEqual(result_dict["errors"], ["Test error"])
        self.assertEqual(len(result_dict["filtered_tracks"]), 1)
        self.assertEqual(len(result_dict["removed_tracks"]), 1)


if __name__ == "__main__":
    unittest.main()
