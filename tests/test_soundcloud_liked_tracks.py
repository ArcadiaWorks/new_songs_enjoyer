#!/usr/bin/env python3
"""
Unit tests for SoundCloud liked tracks functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from adapter.soundcloud_adapter import SoundCloudAdapter, SoundCloudTrack
from entities.track import Track


class TestSoundCloudLikedTracks(unittest.TestCase):
    """Test cases for SoundCloud liked tracks functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.oauth_token = "test_oauth_token_12345"
        self.adapter = SoundCloudAdapter(self.oauth_token)

    def test_get_user_profile_success(self):
        """Test successful user profile retrieval."""
        mock_profile = {
            "id": 12345,
            "username": "testuser",
            "full_name": "Test User",
            "followers_count": 100,
            "followings_count": 50
        }

        with patch.object(self.adapter.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = mock_profile
            mock_get.return_value = mock_response

            result = self.adapter.get_user_profile()

            self.assertIsNotNone(result)
            self.assertEqual(result["username"], "testuser")
            self.assertEqual(result["id"], 12345)
            mock_get.assert_called_once_with(f"{self.adapter.BASE_URL}/me")

    def test_get_user_profile_failure(self):
        """Test user profile retrieval failure."""
        with patch.object(self.adapter.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = Exception("API Error")
            mock_get.return_value = mock_response

            result = self.adapter.get_user_profile()

            self.assertIsNone(result)
            mock_get.assert_called_once_with(f"{self.adapter.BASE_URL}/me")

    def test_get_user_liked_tracks_success(self):
        """Test successful liked tracks retrieval."""
        mock_liked_response = {
            "collection": [
                {
                    "kind": "track",
                    "id": 123456,
                    "title": "Test Track 1",
                    "user": {"username": "artist1"},
                    "permalink_url": "https://soundcloud.com/artist1/test-track-1",
                    "duration": 180000,
                    "genre": "Electronic"
                },
                {
                    "track": {
                        "kind": "track",
                        "id": 789012,
                        "title": "Test Track 2",
                        "user": {"username": "artist2"},
                        "permalink_url": "https://soundcloud.com/artist2/test-track-2",
                        "duration": 240000,
                        "genre": "Ambient"
                    }
                },
                {
                    "kind": "playlist",  # Should be ignored
                    "id": 999999,
                    "title": "Test Playlist"
                }
            ],
            "next_href": None
        }

        with patch.object(self.adapter.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = mock_liked_response
            mock_get.return_value = mock_response

            result = self.adapter.get_user_liked_tracks(limit=10)

            self.assertEqual(len(result), 2)  # Only tracks, not playlists
            
            # Check first track
            self.assertIsInstance(result[0], SoundCloudTrack)
            self.assertEqual(result[0].id, 123456)
            self.assertEqual(result[0].title, "Test Track 1")
            self.assertEqual(result[0].user, "artist1")
            self.assertEqual(result[0].genre, "Electronic")
            
            # Check second track
            self.assertEqual(result[1].id, 789012)
            self.assertEqual(result[1].title, "Test Track 2")
            self.assertEqual(result[1].user, "artist2")
            self.assertEqual(result[1].genre, "Ambient")

            mock_get.assert_called_once()
            args, kwargs = mock_get.call_args
            self.assertEqual(args[0], f"{self.adapter.BASE_URL}/me/likes")
            self.assertEqual(kwargs["params"]["limit"], 10)

    def test_get_user_liked_tracks_pagination(self):
        """Test liked tracks retrieval with pagination."""
        # First page response
        first_page = {
            "collection": [
                {
                    "kind": "track",
                    "id": 111,
                    "title": "Track 1",
                    "user": {"username": "artist1"},
                    "permalink_url": "https://soundcloud.com/artist1/track-1",
                    "duration": 180000,
                    "genre": "Electronic"
                }
            ],
            "next_href": "https://api-v2.soundcloud.com/me/likes?offset=50"
        }

        # Second page response
        second_page = {
            "collection": [
                {
                    "kind": "track",
                    "id": 222,
                    "title": "Track 2",
                    "user": {"username": "artist2"},
                    "permalink_url": "https://soundcloud.com/artist2/track-2",
                    "duration": 240000,
                    "genre": "Ambient"
                }
            ],
            "next_href": None
        }

        with patch.object(self.adapter.session, 'get') as mock_get:
            mock_responses = [Mock(), Mock()]
            mock_responses[0].raise_for_status.return_value = None
            mock_responses[0].json.return_value = first_page
            mock_responses[1].raise_for_status.return_value = None
            mock_responses[1].json.return_value = second_page
            mock_get.side_effect = mock_responses

            result = self.adapter.get_user_liked_tracks(limit=100)

            self.assertEqual(len(result), 2)
            self.assertEqual(result[0].id, 111)
            self.assertEqual(result[1].id, 222)
            self.assertEqual(mock_get.call_count, 2)

    def test_get_user_liked_tracks_empty_response(self):
        """Test liked tracks retrieval with empty response."""
        mock_empty_response = {
            "collection": [],
            "next_href": None
        }

        with patch.object(self.adapter.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = mock_empty_response
            mock_get.return_value = mock_response

            result = self.adapter.get_user_liked_tracks()

            self.assertEqual(len(result), 0)
            mock_get.assert_called_once()

    def test_get_user_liked_tracks_api_error(self):
        """Test liked tracks retrieval with API error."""
        with patch.object(self.adapter.session, 'get') as mock_get:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = Exception("API Error")
            mock_get.return_value = mock_response

            result = self.adapter.get_user_liked_tracks()

            self.assertEqual(len(result), 0)
            mock_get.assert_called_once()

    def test_normalize_track_for_matching(self):
        """Test track normalization for matching."""
        sc_track = SoundCloudTrack(
            id=12345,
            title="Test Song (Remix) [2023]",
            user="Test Artist feat. Another Artist",
            permalink_url="https://soundcloud.com/test/song",
            duration=180000,
            genre="Electronic"
        )

        result = self.adapter._normalize_track_for_matching(sc_track)

        self.assertIsInstance(result, Track)
        self.assertEqual(result.name, "Test Song")  # Should remove (Remix) [2023]
        self.assertEqual(result.artist, "Test Artist feat. Another Artist")
        self.assertEqual(result.url, "https://soundcloud.com/test/song")

    def test_normalize_track_complex_title(self):
        """Test track normalization with complex title patterns."""
        sc_track = SoundCloudTrack(
            id=12345,
            title="Amazing Song - Remaster 2023 (feat. Guest Artist)",
            user="Main Artist",
            permalink_url="https://soundcloud.com/test/song",
            duration=180000,
            genre="Pop"
        )

        result = self.adapter._normalize_track_for_matching(sc_track)

        # Should clean up the title
        self.assertNotIn("Remaster", result.name)
        self.assertNotIn("2023", result.name)
        self.assertNotIn("feat.", result.name)
        self.assertEqual(result.artist, "Main Artist")

    def test_normalize_track_minimal_data(self):
        """Test track normalization with minimal data."""
        sc_track = SoundCloudTrack(
            id=12345,
            title="Simple Song",
            user="Simple Artist",
            permalink_url="https://soundcloud.com/simple/song",
            duration=180000
        )

        result = self.adapter._normalize_track_for_matching(sc_track)

        self.assertEqual(result.name, "Simple Song")
        self.assertEqual(result.artist, "Simple Artist")
        self.assertEqual(result.url, "https://soundcloud.com/simple/song")


if __name__ == '__main__':
    unittest.main()