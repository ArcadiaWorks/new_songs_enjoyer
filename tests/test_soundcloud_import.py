#!/usr/bin/env python3
"""
Test script to simulate SoundCloud import request and see server logs
"""

import requests
import json

# Test playlist data (simulating what the frontend would send)
test_playlist_data = {
    "metadata": {
        "generated_at": "2025-07-12_13-19-09",
        "date": "2025-07-12",
        "tags_used": ["chill", "ambient", "lofi"],
        "tracks_requested": 3,
        "tracks_found": 3,
        "total_available_tracks": 300,
        "api_limit_per_tag": 100,
        "language": "fr",
    },
    "tracks": [
        {
            "name": "Streets",
            "artist": "Doja Cat",
            "url": "https://www.last.fm/music/Doja+Cat/_/Streets",
            "position": 1,
        },
        {
            "name": "Roygbiv",
            "artist": "Boards of Canada",
            "url": "https://www.last.fm/music/Boards+of+Canada/_/Roygbiv",
            "position": 2,
        },
        {
            "name": "Glimpse of Us",
            "artist": "Joji",
            "url": "https://www.last.fm/music/Joji/_/Glimpse+of+Us",
            "position": 3,
        },
    ],
}


def test_soundcloud_import():
    """Test the SoundCloud import endpoint."""
    url = "http://localhost:5000/api/soundcloud/import"

    print("🧪 Testing SoundCloud import endpoint...")
    print(f"📡 Sending POST request to: {url}")
    print(f"📦 Playlist data: {len(test_playlist_data['tracks'])} tracks")

    try:
        response = requests.post(
            url,
            json=test_playlist_data,
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

    except requests.exceptions.ConnectError:
        print(
            "❌ Could not connect to server. Make sure the server is running at http://localhost:5000"
        )
    except requests.exceptions.Timeout:
        print("⏰ Request timed out")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_soundcloud_import()
