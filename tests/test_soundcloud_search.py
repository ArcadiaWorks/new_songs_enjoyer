#!/usr/bin/env python3
"""
Test script for SoundCloud search endpoint
"""

import requests
import json


def test_soundcloud_search():
    """Test the SoundCloud search endpoint."""
    url = "http://localhost:5000/api/soundcloud/search"

    # Test with a popular track
    test_data = {
        "artist": "Nirvana",
        "name": "Come as You Are",
        "query": "Nirvana Come as You Are",
    }

    print("🧪 Testing SoundCloud search endpoint...")
    print(f"📡 Sending POST request to: {url}")
    print(f"📦 Search data: {test_data}")

    try:
        response = requests.post(
            url,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        print(f"📊 Response status: {response.status_code}")
        print(f"📄 Response headers: {dict(response.headers)}")

        if response.headers.get("content-type", "").startswith("application/json"):
            result = response.json()
            print("📋 Response data:")
            print(json.dumps(result, indent=2))
        else:
            print(f"📝 Response text: {response.text}")

    except requests.exceptions.ConnectionError:
        print(
            "❌ Could not connect to server. Make sure the server is running at http://localhost:5000"
        )
    except requests.exceptions.Timeout:
        print("⏰ Request timed out")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_soundcloud_search()
