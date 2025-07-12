#!/usr/bin/env python3
"""
Test runner for new_songs_enjoyer tests
"""

import sys
import os
from pathlib import Path

# Add parent directory to path so we can import the tests
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_all_tests():
    """Run all available tests."""
    print("🧪 Running new_songs_enjoyer Tests")
    print("=" * 40)

    # Import test modules
    try:
        from tests.test_soundcloud_import import test_soundcloud_import
        from tests.mock_soundcloud_test import test_with_mock_credentials

        # Run SoundCloud import test
        print("\n1. Testing SoundCloud Import Endpoint")
        print("-" * 35)
        test_soundcloud_import()

        print("\n2. Testing with Mock Credentials")
        print("-" * 35)
        test_with_mock_credentials()

        print("\n✅ All tests completed!")

    except ImportError as e:
        print(f"❌ Error importing tests: {e}")
    except Exception as e:
        print(f"❌ Error running tests: {e}")


if __name__ == "__main__":
    run_all_tests()
