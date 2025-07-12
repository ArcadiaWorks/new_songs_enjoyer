#!/usr/bin/env python3
"""
Test script to validate OAuth workflow
"""

import os
import requests
import json


def test_oauth_configuration():
    """Test OAuth configuration and workflow."""
    print("🔐 Testing SoundCloud OAuth Workflow...")
    print("=" * 50)

    # Test 1: Check if OAuth token is configured
    oauth_token = os.getenv("SOUNDCLOUD_OAUTH_TOKEN")
    if oauth_token:
        print("✅ OAuth token found in environment")
        print(
            f"📋 Token format: {oauth_token[:10]}...{oauth_token[-10:] if len(oauth_token) > 20 else oauth_token}"
        )
    else:
        print("❌ OAuth token not configured")
        print("📖 Please follow SOUNDCLOUD_OAUTH_SETUP.md to get your token")
        return False

    # Test 2: Test search endpoint with OAuth
    search_url = "http://localhost:5000/api/soundcloud/search"
    search_data = {
        "artist": "Nirvana",
        "name": "Come as You Are",
        "query": "Nirvana Come as You Are",
    }

    print(f"\n🔍 Testing search endpoint: {search_url}")
    try:
        response = requests.post(
            search_url,
            json=search_data,
            headers={"Content-Type": "application/json"},
            timeout=15,
        )

        print(f"📊 Response status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ Search successful!")
                print(f"🎵 Found track: {result.get('track_title', 'Unknown')}")
                print(f"👤 Artist: {result.get('track_artist', 'Unknown')}")
                print(f"🔗 URL: {result.get('soundcloud_url', 'No URL')}")
            else:
                print("⚠️  Search completed but no tracks found")
                print(f"📄 Message: {result.get('error_message', 'Unknown error')}")
        elif response.status_code == 400:
            result = response.json()
            if "OAuth token not configured" in result.get("error_message", ""):
                print("❌ OAuth token not configured in server")
                print("📖 Make sure SOUNDCLOUD_OAUTH_TOKEN is in your .env file")
            else:
                print(f"❌ Bad request: {result.get('error_message', 'Unknown error')}")
        else:
            print(f"❌ Unexpected response: {response.status_code}")

    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server")
        print("🚀 Make sure to run: python run.py server")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    # Test 3: Test import endpoint
    print(f"\n📥 Testing import endpoint...")
    import_url = "http://localhost:5000/api/soundcloud/import"
    test_playlist = {
        "metadata": {
            "generated_at": "2025-07-12_15-17-00",
            "date": "2025-07-12",
            "tags_used": ["test"],
            "tracks_requested": 1,
            "tracks_found": 1,
            "total_available_tracks": 1,
            "api_limit_per_tag": 100,
            "language": "en",
        },
        "tracks": [
            {
                "name": "Come as You Are",
                "artist": "Nirvana",
                "url": "https://www.last.fm/music/Nirvana/_/Come+as+You+Are",
                "position": 1,
            }
        ],
    }

    try:
        response = requests.post(
            import_url,
            json=test_playlist,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        print(f"📊 Import response status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ Import workflow successful!")
            else:
                print("⚠️  Import completed with issues")
                print(f"📄 Message: {result.get('error_message', 'Unknown error')}")
        elif response.status_code == 400:
            result = response.json()
            print(
                f"⚠️  Expected OAuth validation: {result.get('error_message', 'Unknown error')}"
            )
        else:
            print(f"❌ Unexpected import response: {response.status_code}")

    except Exception as e:
        print(f"❌ Import test error: {e}")

    print("\n" + "=" * 50)
    print("🎯 OAuth Workflow Test Complete!")
    print("📖 If you need to configure OAuth, see: SOUNDCLOUD_OAUTH_SETUP.md")

    return True


if __name__ == "__main__":
    test_oauth_configuration()
