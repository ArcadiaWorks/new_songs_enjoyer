"""Unit tests for FilterResult entity."""

import unittest
from entities.filter_result import FilterResult
from entities.track import Track


class TestFilterResult(unittest.TestCase):
    """Test cases for FilterResult entity."""

    def setUp(self):
        """Set up test data."""
        self.sample_tracks = [
            Track(name="Song 1", artist="Artist 1"),
            Track(name="Song 2", artist="Artist 2"),
            Track(name="Song 3", artist="Artist 3"),
            Track(name="Song 4", artist="Artist 4"),
            Track(name="Song 5", artist="Artist 5"),
        ]

    def test_filter_result_creation_valid(self):
        """Test creating a valid FilterResult."""
        filtered_tracks = self.sample_tracks[:3]
        removed_tracks = self.sample_tracks[3:]

        result = FilterResult(
            original_count=5,
            filtered_tracks=filtered_tracks,
            removed_tracks=removed_tracks,
            soundcloud_matches=1,
            spotify_matches=1,
            errors=[],
        )

        self.assertEqual(result.original_count, 5)
        self.assertEqual(len(result.filtered_tracks), 3)
        self.assertEqual(len(result.removed_tracks), 2)
        self.assertEqual(result.soundcloud_matches, 1)
        self.assertEqual(result.spotify_matches, 1)
        self.assertEqual(result.errors, [])

    def test_filter_result_validation_negative_original_count(self):
        """Test validation fails with negative original count."""
        with self.assertRaises(ValueError) as context:
            FilterResult(
                original_count=-1,
                filtered_tracks=[],
                removed_tracks=[],
                soundcloud_matches=0,
                spotify_matches=0,
                errors=[],
            )
        self.assertIn("Original count cannot be negative", str(context.exception))

    def test_filter_result_validation_negative_soundcloud_matches(self):
        """Test validation fails with negative SoundCloud matches."""
        with self.assertRaises(ValueError) as context:
            FilterResult(
                original_count=5,
                filtered_tracks=self.sample_tracks,
                removed_tracks=[],
                soundcloud_matches=-1,
                spotify_matches=0,
                errors=[],
            )
        self.assertIn("SoundCloud matches cannot be negative", str(context.exception))

    def test_filter_result_validation_negative_spotify_matches(self):
        """Test validation fails with negative Spotify matches."""
        with self.assertRaises(ValueError) as context:
            FilterResult(
                original_count=5,
                filtered_tracks=self.sample_tracks,
                removed_tracks=[],
                soundcloud_matches=0,
                spotify_matches=-1,
                errors=[],
            )
        self.assertIn("Spotify matches cannot be negative", str(context.exception))

    def test_filter_result_validation_inconsistent_counts(self):
        """Test validation fails with inconsistent track counts."""
        with self.assertRaises(ValueError) as context:
            FilterResult(
                original_count=5,
                filtered_tracks=self.sample_tracks[:2],  # 2 tracks
                removed_tracks=self.sample_tracks[
                    3:
                ],  # 2 tracks (should be 3 filtered)
                soundcloud_matches=0,
                spotify_matches=0,
                errors=[],
            )
        self.assertIn("Inconsistent track counts", str(context.exception))

    def test_filter_result_validation_invalid_types(self):
        """Test validation fails with invalid types."""
        with self.assertRaises(ValueError) as context:
            FilterResult(
                original_count=5,
                filtered_tracks="not a list",
                removed_tracks=[],
                soundcloud_matches=0,
                spotify_matches=0,
                errors=[],
            )
        self.assertIn("Filtered tracks must be a list", str(context.exception))

        with self.assertRaises(ValueError) as context:
            FilterResult(
                original_count=5,
                filtered_tracks=[],
                removed_tracks="not a list",
                soundcloud_matches=0,
                spotify_matches=0,
                errors=[],
            )
        self.assertIn("Removed tracks must be a list", str(context.exception))

        with self.assertRaises(ValueError) as context:
            FilterResult(
                original_count=0,
                filtered_tracks=[],
                removed_tracks=[],
                soundcloud_matches=0,
                spotify_matches=0,
                errors="not a list",
            )
        self.assertIn("Errors must be a list", str(context.exception))

    def test_create_empty(self):
        """Test creating an empty FilterResult with no filtering."""
        result = FilterResult.create_empty(self.sample_tracks)

        self.assertEqual(result.original_count, 5)
        self.assertEqual(len(result.filtered_tracks), 5)
        self.assertEqual(len(result.removed_tracks), 0)
        self.assertEqual(result.soundcloud_matches, 0)
        self.assertEqual(result.spotify_matches, 0)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.filtered_tracks, self.sample_tracks)

    def test_create_with_filtering(self):
        """Test creating FilterResult with filtering applied."""
        removed_tracks = self.sample_tracks[2:4]  # Remove tracks 3 and 4

        result = FilterResult.create_with_filtering(
            original_tracks=self.sample_tracks,
            removed_tracks=removed_tracks,
            soundcloud_matches=1,
            spotify_matches=1,
            errors=["Test error"],
        )

        self.assertEqual(result.original_count, 5)
        self.assertEqual(len(result.filtered_tracks), 3)
        self.assertEqual(len(result.removed_tracks), 2)
        self.assertEqual(result.soundcloud_matches, 1)
        self.assertEqual(result.spotify_matches, 1)
        self.assertEqual(result.errors, ["Test error"])

        # Check that the correct tracks were filtered out
        expected_filtered = [
            self.sample_tracks[0],
            self.sample_tracks[1],
            self.sample_tracks[4],
        ]
        self.assertEqual(result.filtered_tracks, expected_filtered)

    def test_create_with_filtering_default_errors(self):
        """Test creating FilterResult with default empty errors."""
        result = FilterResult.create_with_filtering(
            original_tracks=self.sample_tracks, removed_tracks=[]
        )

        self.assertEqual(result.errors, [])

    def test_to_dict(self):
        """Test JSON serialization via to_dict method."""
        filtered_tracks = self.sample_tracks[:3]
        removed_tracks = self.sample_tracks[3:]

        result = FilterResult(
            original_count=5,
            filtered_tracks=filtered_tracks,
            removed_tracks=removed_tracks,
            soundcloud_matches=1,
            spotify_matches=1,
            errors=["Test error"],
        )

        data = result.to_dict()

        self.assertEqual(data["original_count"], 5)
        self.assertEqual(data["filtered_count"], 3)
        self.assertEqual(data["removed_count"], 2)
        self.assertEqual(data["soundcloud_matches"], 1)
        self.assertEqual(data["spotify_matches"], 1)
        self.assertEqual(data["total_matches"], 2)
        self.assertTrue(data["has_errors"])
        self.assertEqual(data["error_count"], 1)
        self.assertEqual(data["errors"], ["Test error"])
        self.assertEqual(len(data["filtered_tracks"]), 3)
        self.assertEqual(len(data["removed_tracks"]), 2)

        # Check that tracks are properly serialized
        self.assertEqual(data["filtered_tracks"][0]["name"], "Song 1")
        self.assertEqual(data["removed_tracks"][0]["name"], "Song 4")

    def test_to_dict_no_errors(self):
        """Test to_dict with no errors."""
        result = FilterResult.create_empty(self.sample_tracks)
        data = result.to_dict()

        self.assertFalse(data["has_errors"])
        self.assertEqual(data["error_count"], 0)
        self.assertEqual(data["errors"], [])

    def test_get_removal_percentage(self):
        """Test removal percentage calculation."""
        # Test with 40% removal (2 out of 5)
        result = FilterResult.create_with_filtering(
            original_tracks=self.sample_tracks, removed_tracks=self.sample_tracks[:2]
        )
        self.assertEqual(result.get_removal_percentage(), 40.0)

        # Test with no removal
        result_no_removal = FilterResult.create_empty(self.sample_tracks)
        self.assertEqual(result_no_removal.get_removal_percentage(), 0.0)

        # Test with empty original list
        result_empty = FilterResult.create_empty([])
        self.assertEqual(result_empty.get_removal_percentage(), 0.0)

    def test_get_statistics_summary(self):
        """Test statistics summary without track details."""
        result = FilterResult.create_with_filtering(
            original_tracks=self.sample_tracks,
            removed_tracks=self.sample_tracks[:2],
            soundcloud_matches=1,
            spotify_matches=1,
            errors=["Test error"],
        )

        summary = result.get_statistics_summary()

        self.assertEqual(summary["original_count"], 5)
        self.assertEqual(summary["filtered_count"], 3)
        self.assertEqual(summary["removed_count"], 2)
        self.assertEqual(summary["removal_percentage"], 40.0)
        self.assertEqual(summary["soundcloud_matches"], 1)
        self.assertEqual(summary["spotify_matches"], 1)
        self.assertEqual(summary["total_matches"], 2)
        self.assertTrue(summary["has_errors"])
        self.assertEqual(summary["error_count"], 1)

        # Should not contain track details
        self.assertNotIn("filtered_tracks", summary)
        self.assertNotIn("removed_tracks", summary)
        self.assertNotIn("errors", summary)

    def test_add_error(self):
        """Test adding errors to the result."""
        result = FilterResult.create_empty(self.sample_tracks)

        result.add_error("First error")
        self.assertEqual(result.errors, ["First error"])

        result.add_error("Second error")
        self.assertEqual(result.errors, ["First error", "Second error"])

        # Test duplicate error is not added
        result.add_error("First error")
        self.assertEqual(result.errors, ["First error", "Second error"])

        # Test empty error is not added
        result.add_error("")
        self.assertEqual(result.errors, ["First error", "Second error"])

    def test_has_filtering_applied(self):
        """Test checking if filtering was applied."""
        # No filtering
        result_no_filter = FilterResult.create_empty(self.sample_tracks)
        self.assertFalse(result_no_filter.has_filtering_applied())

        # With filtering
        result_with_filter = FilterResult.create_with_filtering(
            original_tracks=self.sample_tracks, removed_tracks=self.sample_tracks[:1]
        )
        self.assertTrue(result_with_filter.has_filtering_applied())

    def test_is_successful(self):
        """Test checking if filtering completed without errors."""
        # No errors
        result_success = FilterResult.create_empty(self.sample_tracks)
        self.assertTrue(result_success.is_successful())

        # With errors
        result_with_errors = FilterResult.create_with_filtering(
            original_tracks=self.sample_tracks, removed_tracks=[], errors=["Test error"]
        )
        self.assertFalse(result_with_errors.is_successful())

    def test_str_representation(self):
        """Test string representation."""
        result = FilterResult.create_with_filtering(
            original_tracks=self.sample_tracks,
            removed_tracks=self.sample_tracks[:2],
            soundcloud_matches=1,
            spotify_matches=1,
        )

        str_repr = str(result)
        self.assertIn("3/5 tracks", str_repr)
        self.assertIn("2 removed", str_repr)
        self.assertIn("1 SoundCloud", str_repr)
        self.assertIn("1 Spotify", str_repr)

    def test_len_method(self):
        """Test len() method returns filtered track count."""
        result = FilterResult.create_with_filtering(
            original_tracks=self.sample_tracks, removed_tracks=self.sample_tracks[:2]
        )

        self.assertEqual(len(result), 3)
        self.assertEqual(len(result), len(result.filtered_tracks))

    def test_edge_case_all_tracks_removed(self):
        """Test edge case where all tracks are removed."""
        result = FilterResult.create_with_filtering(
            original_tracks=self.sample_tracks,
            removed_tracks=self.sample_tracks,
            soundcloud_matches=5,
        )

        self.assertEqual(result.original_count, 5)
        self.assertEqual(len(result.filtered_tracks), 0)
        self.assertEqual(len(result.removed_tracks), 5)
        self.assertEqual(result.get_removal_percentage(), 100.0)

    def test_edge_case_empty_original_tracks(self):
        """Test edge case with empty original tracks list."""
        result = FilterResult.create_empty([])

        self.assertEqual(result.original_count, 0)
        self.assertEqual(len(result.filtered_tracks), 0)
        self.assertEqual(len(result.removed_tracks), 0)
        self.assertEqual(result.get_removal_percentage(), 0.0)


if __name__ == "__main__":
    unittest.main()
