"""Simple web server for SoundCloud import functionality."""

import os
import json
import logging
import requests
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
from dotenv import load_dotenv

from entities import Playlist, Track
from adapter import SoundCloudAdapter

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Setup logging with better formatting
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@app.route("/api/soundcloud/oembed", methods=["POST"])
def soundcloud_oembed():
    """Proxy SoundCloud oEmbed requests to avoid CORS issues."""
    logger.info("Received SoundCloud oEmbed request")

    try:
        data = request.get_json()
        if not data or not data.get("url"):
            return jsonify({"success": False, "error_message": "URL required"}), 400

        soundcloud_url = data.get("url")
        maxwidth = data.get("maxwidth", "100%")
        maxheight = data.get("maxheight", 166)
        auto_play = data.get("auto_play", False)
        show_comments = data.get("show_comments", False)

        # Build oEmbed URL
        oembed_url = f"https://soundcloud.com/oembed"
        params = {
            "url": soundcloud_url,
            "format": "json",
            "maxwidth": maxwidth,
            "maxheight": maxheight,
            "auto_play": str(auto_play).lower(),
            "show_comments": str(show_comments).lower(),
            "visual": "false",
        }

        logger.debug(f"Calling SoundCloud oEmbed: {oembed_url}")
        response = requests.get(oembed_url, params=params, timeout=10)

        if response.status_code == 200:
            oembed_data = response.json()
            return jsonify(
                {
                    "success": True,
                    "html": oembed_data.get("html", ""),
                    "title": oembed_data.get("title", ""),
                    "author_name": oembed_data.get("author_name", ""),
                    "thumbnail_url": oembed_data.get("thumbnail_url", ""),
                }
            )
        else:
            logger.error(f"SoundCloud oEmbed error: {response.status_code}")
            return jsonify(
                {
                    "success": False,
                    "error_message": f"oEmbed failed: {response.status_code}",
                }
            ), response.status_code

    except Exception as e:
        logger.error(f"Error in SoundCloud oEmbed proxy: {e}")
        return jsonify({"success": False, "error_message": str(e)}), 500


@app.route("/api/soundcloud/search", methods=["POST"])
def search_soundcloud():
    """Handle SoundCloud track search requests."""
    logger.info("Received SoundCloud search request")

    try:
        # Get search data from request
        data = request.get_json()
        logger.debug(f"Search request data: {data}")

        if not data:
            logger.warning("No search data provided in request")
            return jsonify(
                {"success": False, "error_message": "No search data provided"}
            ), 400

        artist = data.get("artist", "")
        name = data.get("name", "")
        query = data.get("query", f"{artist} {name}")

        logger.info(f"Searching for track: {query}")

        # Check if SoundCloud OAuth token is configured
        load_dotenv()  # Reload environment variables
        oauth_token = os.getenv("SOUNDCLOUD_OAUTH_TOKEN")

        if not oauth_token:
            logger.warning("SoundCloud OAuth token not configured")
            return jsonify(
                {
                    "success": False,
                    "error_message": "SoundCloud OAuth token not configured. Please set SOUNDCLOUD_OAUTH_TOKEN in your .env file.",
                }
            ), 400

        # Search SoundCloud for the track using OAuth
        try:
            import requests

            search_url = f"https://api-v2.soundcloud.com/search/tracks"
            headers = {
                "Authorization": f"OAuth {oauth_token}",
                "Accept": "application/json; charset=utf-8",
            }
            params = {"q": query, "limit": 1, "linked_partitioning": 1}

            logger.debug(f"Calling SoundCloud API: {search_url} with OAuth token")
            response = requests.get(
                search_url, params=params, headers=headers, timeout=10
            )

            if response.status_code == 200:
                search_results = response.json()

                # API v2 returns results in 'collection' array
                collection = search_results.get("collection", [])
                logger.debug(
                    f"SoundCloud search results: {len(collection)} tracks found"
                )

                if collection and len(collection) > 0:
                    track = collection[0]
                    soundcloud_url = track.get("permalink_url")

                    if soundcloud_url:
                        logger.info(f"Found SoundCloud track: {soundcloud_url}")
                        return jsonify(
                            {
                                "success": True,
                                "soundcloud_url": soundcloud_url,
                                "track_title": track.get("title", ""),
                                "track_artist": track.get("user", {}).get(
                                    "username", ""
                                ),
                                "duration": track.get("duration", 0),
                            }
                        )
                    else:
                        logger.warning("Track found but no permalink_url")
                        return jsonify(
                            {
                                "success": False,
                                "error_message": "Track found but no URL available",
                            }
                        )
                else:
                    logger.info("No tracks found on SoundCloud")
                    return jsonify(
                        {
                            "success": False,
                            "error_message": "No tracks found on SoundCloud",
                        }
                    )
            else:
                logger.error(
                    f"SoundCloud API error: {response.status_code} - {response.text}"
                )
                return jsonify(
                    {
                        "success": False,
                        "error_message": f"SoundCloud API error: {response.status_code}",
                    }
                )

        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling SoundCloud API: {e}")
            return jsonify(
                {"success": False, "error_message": f"Network error: {str(e)}"}
            )

    except Exception as e:
        logger.error(f"Error in SoundCloud search: {e}", exc_info=True)
        return jsonify({"success": False, "error_message": str(e)}), 500


@app.route("/api/soundcloud/import", methods=["POST"])
def import_to_soundcloud():
    """Handle SoundCloud playlist import requests."""
    logger.info("Received SoundCloud import request")

    try:
        # Get playlist data from request
        data = request.get_json()
        logger.debug(f"Request data keys: {list(data.keys()) if data else 'None'}")

        if not data:
            logger.warning("No playlist data provided in request")
            return jsonify(
                {"success": False, "error_message": "No playlist data provided"}
            ), 400

        # Check if SoundCloud OAuth token is configured (reload env vars)
        load_dotenv()  # Reload environment variables
        oauth_token = os.getenv("SOUNDCLOUD_OAUTH_TOKEN")

        logger.info(
            f"SoundCloud OAuth token check: {'configured' if oauth_token else 'missing'}"
        )

        if not oauth_token:
            logger.error("SoundCloud OAuth token not configured")
            return jsonify(
                {
                    "success": False,
                    "error_message": "SoundCloud OAuth token not configured. Please set SOUNDCLOUD_OAUTH_TOKEN in your .env file.",
                }
            ), 400

        # Reconstruct playlist from data
        metadata_dict = data.get("metadata", {})
        tracks_data = data.get("tracks", [])

        logger.info(f"Reconstructing playlist with {len(tracks_data)} tracks")
        logger.debug(f"Metadata: {metadata_dict}")

        # Create Track objects
        tracks = []
        for i, track_data in enumerate(tracks_data):
            track = Track(
                name=track_data.get("name", ""),
                artist=track_data.get("artist", ""),
                url=track_data.get("url"),
                position=track_data.get("position"),
            )
            tracks.append(track)
            logger.debug(f"Track {i + 1}: {track.name} - {track.artist}")

        # Create playlist (simplified reconstruction)
        playlist = Playlist.create(
            tracks=tracks,
            timestamp=metadata_dict.get("generated_at", ""),
            tags=metadata_dict.get("tags_used", []),
            tracks_requested=metadata_dict.get("tracks_requested", len(tracks)),
            total_available_tracks=metadata_dict.get("total_available_tracks", 0),
            api_limit_per_tag=metadata_dict.get("api_limit_per_tag", 100),
            language=metadata_dict.get("language", "en"),
        )

        logger.info(f"Created playlist with {len(playlist.tracks)} tracks")

        # Import to SoundCloud
        logger.info("Starting SoundCloud import process")
        adapter = SoundCloudAdapter.from_env()
        result = adapter.import_playlist(playlist)

        logger.info(
            f"SoundCloud import result: Success={result.success}, Tracks added={result.tracks_added}, Not found={result.tracks_not_found}"
        )
        if result.error_message:
            logger.error(f"SoundCloud import error: {result.error_message}")

        # Return result
        return jsonify(
            {
                "success": result.success,
                "playlist_id": result.playlist_id,
                "playlist_url": result.playlist_url,
                "tracks_added": result.tracks_added,
                "tracks_not_found": result.tracks_not_found,
                "error_message": result.error_message,
                "not_found_tracks": result.not_found_tracks,
            }
        )

    except Exception as e:
        logger.error(f"Error in SoundCloud import: {e}", exc_info=True)
        return jsonify({"success": False, "error_message": str(e)}), 500


@app.route("/playlist/<filename>")
def serve_playlist(filename):
    """Serve playlist HTML files."""
    output_dir = Path("output")
    return send_from_directory(output_dir, filename)


@app.route("/generate")
def generate_form():
    """Show playlist generation form."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>new_songs_enjoyer - Generate Playlist</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: 'Inter', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }

            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }

            .header {
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: white;
                padding: 40px;
                text-align: center;
            }

            .header h1 {
                font-size: 2.5rem;
                font-weight: 700;
                margin-bottom: 10px;
            }

            .form-section {
                padding: 40px;
            }

            .form-group {
                margin-bottom: 25px;
            }

            .form-group label {
                display: block;
                font-weight: 600;
                color: #1e293b;
                margin-bottom: 8px;
                font-size: 1rem;
            }

            .form-group input, .form-group select, .form-group textarea {
                width: 100%;
                padding: 12px 16px;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                font-size: 1rem;
                transition: border-color 0.2s ease;
            }

            .form-group input:focus, .form-group select:focus, .form-group textarea:focus {
                outline: none;
                border-color: #3b82f6;
            }

            .form-group small {
                display: block;
                color: #64748b;
                margin-top: 5px;
                font-size: 0.875rem;
            }

            .tags-input {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                margin-bottom: 10px;
            }

            .tag-input {
                flex: 1;
                min-width: 120px;
            }

            .quick-tags {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                margin-top: 10px;
            }

            .quick-tag {
                background: #e2e8f0;
                color: #475569;
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 0.875rem;
                cursor: pointer;
                transition: all 0.2s ease;
                border: none;
            }

            .quick-tag:hover, .quick-tag.selected {
                background: #3b82f6;
                color: white;
            }

            .generate-btn {
                background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 50px;
                font-size: 1.1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                width: 100%;
                box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
            }

            .generate-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
            }

            .generate-btn:disabled {
                background: #94a3b8;
                cursor: not-allowed;
                transform: none;
                box-shadow: none;
            }

            .status {
                margin-top: 20px;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
                display: none;
            }

            .status.loading {
                background: #dbeafe;
                color: #1d4ed8;
                border: 1px solid #bfdbfe;
            }

            .status.success {
                background: #dcfce7;
                color: #166534;
                border: 1px solid #bbf7d0;
            }

            .status.error {
                background: #fef2f2;
                color: #dc2626;
                border: 1px solid #fecaca;
            }

            .back-link {
                display: inline-block;
                margin-bottom: 20px;
                color: #3b82f6;
                text-decoration: none;
                font-weight: 500;
            }

            .back-link:hover {
                text-decoration: underline;
            }

            @media (max-width: 768px) {
                .container {
                    margin: 10px;
                    border-radius: 15px;
                }

                .header, .form-section {
                    padding: 20px;
                }

                .header h1 {
                    font-size: 2rem;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎵 Generate Playlist</h1>
                <p>Create a new music playlist with custom parameters</p>
            </div>

            <div class="form-section">
                <a href="/" class="back-link">← Back to Playlists</a>

                <form id="generate-form">
                    <div class="form-group">
                        <label for="tags">Music Tags</label>
                        <div class="tags-input">
                            <input type="text" id="tags" name="tags" class="tag-input" placeholder="Enter tags separated by commas">
                        </div>
                        <div class="quick-tags">
                            <button type="button" class="quick-tag" data-tag="rock">Rock</button>
                            <button type="button" class="quick-tag" data-tag="pop">Pop</button>
                            <button type="button" class="quick-tag" data-tag="electronic">Electronic</button>
                            <button type="button" class="quick-tag" data-tag="jazz">Jazz</button>
                            <button type="button" class="quick-tag" data-tag="classical">Classical</button>
                            <button type="button" class="quick-tag" data-tag="indie">Indie</button>
                            <button type="button" class="quick-tag" data-tag="alternative">Alternative</button>
                            <button type="button" class="quick-tag" data-tag="metal">Metal</button>
                            <button type="button" class="quick-tag" data-tag="hip-hop">Hip-Hop</button>
                            <button type="button" class="quick-tag" data-tag="ambient">Ambient</button>
                        </div>
                        <small>Click quick tags or enter custom tags separated by commas</small>
                    </div>

                    <div class="form-group">
                        <label for="tracks">Number of Tracks</label>
                        <input type="number" id="tracks" name="tracks" value="8" min="1" max="50">
                        <small>Number of tracks to include in the playlist (1-50)</small>
                    </div>

                    <div class="form-group">
                        <label for="limit">API Limit per Tag</label>
                        <input type="number" id="limit" name="limit" value="100" min="10" max="1000">
                        <small>Maximum tracks to fetch per tag from Last.fm (10-1000)</small>
                    </div>

                    <div class="form-group">
                        <label for="language">Language</label>
                        <select id="language" name="language">
                            <option value="en">English</option>
                            <option value="fr">Français</option>
                        </select>
                        <small>Language for the generated playlist interface</small>
                    </div>

                    <div class="form-group">
                        <label for="soundcloud-token">SoundCloud OAuth Token (Optional)</label>
                        <textarea id="soundcloud-token" name="soundcloud_token" rows="3" placeholder="Enter your SoundCloud OAuth token to filter out tracks you've already liked"></textarea>
                        <small>
                            <strong>🔑 How to extract your SoundCloud OAuth token from browser cookies:</strong><br>
                            <strong>Step 1:</strong> Open <a href="https://soundcloud.com" target="_blank" style="color: #3b82f6;">SoundCloud</a> in your browser and make sure you're logged in<br>
                            <strong>Step 2:</strong> Open Developer Tools:<br>
                            &nbsp;&nbsp;• <strong>Chrome/Edge:</strong> Press F12 or right-click → "Inspect"<br>
                            &nbsp;&nbsp;• <strong>Firefox:</strong> Press F12 or right-click → "Inspect Element"<br>
                            &nbsp;&nbsp;• <strong>Safari:</strong> Enable Developer menu first, then press Cmd+Option+I<br>
                            <strong>Step 3:</strong> Navigate to the cookies:<br>
                            &nbsp;&nbsp;• <strong>Chrome/Edge:</strong> Application tab → Storage → Cookies → https://soundcloud.com<br>
                            &nbsp;&nbsp;• <strong>Firefox:</strong> Storage tab → Cookies → https://soundcloud.com<br>
                            &nbsp;&nbsp;• <strong>Safari:</strong> Storage tab → Cookies → soundcloud.com<br>
                            <strong>Step 4:</strong> Find the cookie named <code style="background: #e2e8f0; padding: 2px 4px; border-radius: 3px;">oauth_token</code><br>
                            <strong>Step 5:</strong> Copy the entire value (it should start with numbers and contain letters/numbers)<br>
                            <strong>Step 6:</strong> Paste the token in the field above<br><br>
                            <strong>⚡ What this does:</strong> Filters out tracks you've already liked on SoundCloud from your recommendations, ensuring fresh discoveries!<br>
                            <strong>🔒 Privacy:</strong> Your token is only used during playlist generation and is not stored permanently.
                        </small>
                    </div>

                    <button type="submit" class="generate-btn">
                        🎵 Generate Playlist
                    </button>

                    <div id="status" class="status"></div>
                </form>
            </div>
        </div>

        <script>
            // Quick tag functionality
            document.querySelectorAll('.quick-tag').forEach(tag => {
                tag.addEventListener('click', () => {
                    tag.classList.toggle('selected');
                    updateTagsInput();
                });
            });

            function updateTagsInput() {
                const selectedTags = Array.from(document.querySelectorAll('.quick-tag.selected'))
                    .map(tag => tag.dataset.tag);
                const tagsInput = document.getElementById('tags');

                // Merge with existing input
                const existingTags = tagsInput.value.split(',')
                    .map(tag => tag.trim())
                    .filter(tag => tag.length > 0);

                const allTags = [...new Set([...existingTags, ...selectedTags])];
                tagsInput.value = allTags.join(', ');
            }

            // Form submission
            document.getElementById('generate-form').addEventListener('submit', async (e) => {
                e.preventDefault();

                const formData = new FormData(e.target);
                const params = {
                    tags: formData.get('tags').split(',').map(tag => tag.trim()).filter(tag => tag.length > 0),
                    tracks: parseInt(formData.get('tracks')),
                    limit: parseInt(formData.get('limit')),
                    language: formData.get('language'),
                    soundcloud_token: formData.get('soundcloud_token') || null
                };

                const status = document.getElementById('status');
                const submitBtn = document.querySelector('.generate-btn');

                // Show loading
                status.className = 'status loading';
                status.style.display = 'block';
                status.textContent = 'Generating playlist...';
                submitBtn.disabled = true;

                try {
                    const response = await fetch('/api/generate', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(params)
                    });

                    const result = await response.json();

                    if (result.success) {
                        status.className = 'status success';
                        let successMessage = `
                            Playlist generated successfully!<br>
                            <a href="${result.playlist_url}" target="_blank" style="color: inherit; text-decoration: underline;">
                                View Playlist →
                            </a>
                        `;

                        // Add filtering statistics if available
                        if (result.filtering_stats) {
                            const stats = result.filtering_stats;
                            successMessage += `<br><br><strong>🎯 Platform Filtering Results:</strong><br>`;

                            if (stats.removed_count > 0) {
                                successMessage += `<div style="background: #fef3c7; padding: 10px; border-radius: 6px; margin: 8px 0; border-left: 4px solid #f59e0b;">`;
                                successMessage += `<strong>✨ Filtered for Fresh Discoveries!</strong><br>`;
                                successMessage += `• <strong>${stats.removed_count}</strong> duplicate tracks removed (${stats.removal_percentage}%)<br>`;
                                successMessage += `• <strong>${stats.filtered_count}</strong> fresh tracks in your playlist<br>`;

                                if (stats.soundcloud_matches > 0) {
                                    successMessage += `• <strong>${stats.soundcloud_matches}</strong> SoundCloud matches found<br>`;
                                }
                                if (stats.spotify_matches > 0) {
                                    successMessage += `• <strong>${stats.spotify_matches}</strong> Spotify matches found<br>`;
                                }

                                if (stats.has_errors) {
                                    successMessage += `• ⚠️ <strong>${stats.error_count}</strong> filtering errors occurred<br>`;
                                }
                                successMessage += `</div>`;
                            } else if (params.soundcloud_token && params.soundcloud_token.trim()) {
                                successMessage += `<div style="background: #dcfce7; padding: 10px; border-radius: 6px; margin: 8px 0; border-left: 4px solid #10b981;">`;
                                successMessage += `<strong>🎉 All Fresh Tracks!</strong><br>`;
                                successMessage += `• No duplicate tracks found in your SoundCloud library<br>`;
                                successMessage += `• All <strong>${stats.filtered_count}</strong> tracks are new discoveries<br>`;
                                successMessage += `</div>`;
                            }

                            if (stats.has_errors && stats.error_count > 0) {
                                successMessage += `<div style="background: #fef2f2; padding: 10px; border-radius: 6px; margin: 8px 0; border-left: 4px solid #ef4444;">`;
                                successMessage += `<strong>⚠️ Filtering Warnings:</strong><br>`;
                                successMessage += `• Some filtering operations encountered issues<br>`;
                                successMessage += `• Playlist may contain some tracks from your library<br>`;
                                successMessage += `</div>`;
                            }
                        } else if (params.soundcloud_token && params.soundcloud_token.trim()) {
                            successMessage += `<br><br><strong>🎯 Platform Filtering:</strong><br>`;
                            successMessage += `<div style="background: #dbeafe; padding: 10px; border-radius: 6px; margin: 8px 0; border-left: 4px solid #3b82f6;">`;
                            successMessage += `• SoundCloud token provided but no filtering stats available<br>`;
                            successMessage += `• Check server logs for filtering details<br>`;
                            successMessage += `</div>`;
                        }

                        status.innerHTML = successMessage;
                    } else {
                        status.className = 'status error';
                        status.textContent = `Error: ${result.error}`;
                    }
                } catch (error) {
                    status.className = 'status error';
                    status.textContent = `Error: ${error.message}`;
                } finally {
                    submitBtn.disabled = false;
                }
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(html_content)


@app.route("/api/generate", methods=["POST"])
def generate_playlist():
    """Generate a new playlist with the given parameters."""
    logger.info("Received playlist generation request")

    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        tags = data.get("tags", [])
        tracks = data.get("tracks", 8)
        limit = data.get("limit", 100)
        language = data.get("language", "en")
        soundcloud_token = data.get("soundcloud_token")

        if not tags:
            return jsonify(
                {"success": False, "error": "At least one tag is required"}
            ), 400

        logger.info(
            f"Generating playlist with tags: {tags}, tracks: {tracks}, limit: {limit}, language: {language}, "
            f"soundcloud_token: {'provided' if soundcloud_token else 'not provided'}"
        )

        # Import required modules for playlist generation
        from config import get_default_config, substitute_env_variables
        from main import create_playlist
        from platform_filter import PlatformFilter
        from adapter.soundcloud_adapter import SoundCloudAdapter
        import os

        # Set up temporary environment for SoundCloud token if provided
        original_token = os.environ.get("SOUNDCLOUD_OAUTH_TOKEN")
        if soundcloud_token and soundcloud_token.strip():
            os.environ["SOUNDCLOUD_OAUTH_TOKEN"] = soundcloud_token.strip()

        try:
            # Create config with the provided parameters
            config = get_default_config()
            config.update(
                {
                    "default_tags": tags,
                    "num_tracks": tracks,
                    "api": {
                        "limit_per_tag": limit,
                        "base_url": "https://ws.audioscrobbler.com/2.0/",
                    },
                    "output": {
                        "directory": "output",
                        "history_filename": "music_history.json",
                        "daily_playlist_format": "playlist_{date}.json",
                    },
                    "display": {"show_fetching_progress": True, "language": language},
                    "logging": {
                        "level": "INFO",
                        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    },
                    "platform_filtering": {
                        "enabled": bool(soundcloud_token and soundcloud_token.strip()),
                        "soundcloud": {
                            "enabled": bool(
                                soundcloud_token and soundcloud_token.strip()
                            ),
                            "oauth_token": soundcloud_token.strip()
                            if soundcloud_token and soundcloud_token.strip()
                            else None,
                        },
                    },
                }
            )

            # Substitute environment variables
            config = substitute_env_variables(config)

            # Create SoundCloud adapter if token is provided
            soundcloud_adapter = None
            if soundcloud_token and soundcloud_token.strip():
                try:
                    soundcloud_adapter = SoundCloudAdapter.from_env()
                    logger.info("SoundCloud adapter created for filtering")
                except Exception as e:
                    logger.warning(f"Could not create SoundCloud adapter: {e}")

                # Create platform filter
                platform_filter = (
                    PlatformFilter(soundcloud_adapter=soundcloud_adapter)
                    if soundcloud_adapter
                    else None
                )

                # Generate playlist using main.py function
                from main import ensure_output_directory, save_playlist_files
                from pathlib import Path

                output_dir = ensure_output_directory(config["output"]["directory"])
                playlist = create_playlist(tags, config, Path(output_dir))

                if playlist:
                    # Check if playlist has tracks
                    if len(playlist.tracks) == 0:
                        # Handle empty playlist case
                        error_message = "No new tracks found for the selected tags. "

                        # Check if filtering stats are available to provide more context
                        if playlist.has_filtering_stats():
                            stats = playlist.get_filtering_stats()
                            if stats.get("has_errors", False):
                                error_message += (
                                    "There were also issues with platform filtering. "
                                )

                            # Check if the tag itself returned no tracks vs. all tracks were already seen
                            if stats.get("original_count", 0) == 0:
                                error_message = f"The tag '{', '.join(tags)}' returned no tracks from Last.fm. "
                                error_message += (
                                    "This tag might not exist or have very few tracks. "
                                )
                            else:
                                error_message += "All tracks for these tags have already been recommended. "

                            error_message += (
                                "Try different tags or clear your music history."
                            )
                        else:
                            error_message += "All tracks for these tags may have already been recommended. Try different tags or clear your history."

                        return jsonify(
                            {
                                "success": False,
                                "error": error_message,
                                "suggestion": "Try popular tags like 'indie', 'electronic', 'jazz', 'rock', 'pop', or 'alternative'",
                                "empty_playlist": True,
                            }
                        ), 400

                    # Save playlist files
                    files = save_playlist_files(playlist, output_dir)

                    if files and files.get("html"):
                        html_file = files["html"]
                        playlist_url = f"/playlist/{html_file.name}"

                        # Prepare response with filtering statistics
                        response_data = {
                            "success": True,
                            "playlist_url": playlist_url,
                            "filename": html_file.name,
                        }

                        # Add filtering statistics if available
                        if playlist.has_filtering_stats():
                            response_data["filtering_stats"] = (
                                playlist.get_filtering_stats()
                            )

                        return jsonify(response_data)
                    else:
                        return jsonify(
                            {"success": False, "error": "Failed to save playlist files"}
                        ), 500
                else:
                    return jsonify(
                        {"success": False, "error": "Failed to create playlist"}
                    ), 500
                platform_filter = None

                if soundcloud_adapter:
                    try:
                        from platform_filter import PlatformFilter

                        platform_filter = PlatformFilter(
                            soundcloud_adapter=soundcloud_adapter
                        )
                        logger.info("Platform filtering enabled with SoundCloud")

                        # Test the platform filter with a quick validation
                        try:
                            # Validate that we can fetch favorites (this will cache them)
                            favorites_count = len(
                                platform_filter.get_soundcloud_favorites()
                            )
                            logger.info(
                                f"Platform filter validated - found {favorites_count} SoundCloud favorites"
                            )
                        except Exception as validation_error:
                            logger.warning(
                                f"Platform filter validation failed: {validation_error}"
                            )
                            if "401" in str(validation_error) or "403" in str(
                                validation_error
                            ):
                                logger.error(
                                    "SoundCloud OAuth token is invalid or expired"
                                )
                                return jsonify(
                                    {
                                        "success": False,
                                        "error": "Invalid SoundCloud OAuth token. Please check your token and try again.",
                                    }
                                ), 400
                            elif "timeout" in str(validation_error).lower():
                                logger.warning(
                                    "SoundCloud validation timed out, but continuing with filtering"
                                )
                            else:
                                logger.warning(
                                    "Platform filter validation had issues, but continuing"
                                )

                    except ImportError as e:
                        logger.error(f"Could not import PlatformFilter: {e}")
                        return jsonify(
                            {
                                "success": False,
                                "error": "Platform filtering is not available due to missing dependencies.",
                            }
                        ), 500
                    except Exception as e:
                        logger.error(f"Could not create platform filter: {e}")
                        error_message = "Could not initialize platform filtering."
                        if "token" in str(e).lower():
                            error_message += (
                                " Please check your SoundCloud OAuth token."
                            )
                        return jsonify({"success": False, "error": error_message}), 500
                else:
                    logger.debug(
                        "No SoundCloud adapter available for platform filtering"
                    )

            # No cleanup needed since we're not using temporary files

        finally:
            # Restore original environment
            if original_token is not None:
                os.environ["SOUNDCLOUD_OAUTH_TOKEN"] = original_token
            elif "SOUNDCLOUD_OAUTH_TOKEN" in os.environ:
                del os.environ["SOUNDCLOUD_OAUTH_TOKEN"]

    except Exception as e:
        logger.error(f"Error generating playlist: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/")
def index():
    """Show available playlists."""
    output_dir = Path("output")
    html_files = list(output_dir.glob("*.html"))

    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>new_songs_enjoyer - Playlists</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: 'Inter', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }

            .container {
                max-width: 900px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }

            .header {
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: white;
                padding: 40px;
                text-align: center;
            }

            .header h1 {
                font-size: 2.5rem;
                font-weight: 700;
                margin-bottom: 10px;
            }

            .content {
                padding: 40px;
            }

            .generate-section {
                text-align: center;
                margin-bottom: 40px;
                padding: 30px;
                background: #f8fafc;
                border-radius: 12px;
                border: 2px dashed #cbd5e1;
            }

            .generate-btn {
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                color: white;
                border: none;
                padding: 15px 30px;
                border-radius: 50px;
                font-size: 1.1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                text-decoration: none;
                display: inline-block;
                box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
            }

            .generate-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
            }

            .playlist-item {
                margin: 20px 0;
                padding: 25px;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                background: white;
                transition: all 0.3s ease;
            }

            .playlist-item:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(0,0,0,0.1);
                border-color: #3b82f6;
            }

            .playlist-item h3 {
                margin: 0 0 10px 0;
                color: #1e293b;
                font-size: 1.3rem;
                font-weight: 600;
            }

            .playlist-item a {
                color: #3b82f6;
                text-decoration: none;
                font-weight: 500;
                font-size: 1rem;
            }

            .playlist-item a:hover {
                text-decoration: underline;
            }

            .no-playlists {
                color: #64748b;
                font-style: italic;
                text-align: center;
                padding: 40px;
                background: #f8fafc;
                border-radius: 12px;
            }

            .instructions {
                margin-top: 40px;
                padding: 30px;
                background: #f1f5f9;
                border-radius: 12px;
                border-left: 4px solid #3b82f6;
            }

            .instructions h3 {
                color: #1e293b;
                margin-bottom: 15px;
                font-size: 1.2rem;
            }

            .instructions ol {
                color: #475569;
                padding-left: 20px;
            }

            .instructions li {
                margin-bottom: 8px;
                line-height: 1.5;
            }

            .instructions code {
                background: #e2e8f0;
                padding: 2px 6px;
                border-radius: 4px;
                font-family: 'Monaco', 'Consolas', monospace;
                font-size: 0.9rem;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎵 new_songs_enjoyer</h1>
                <p>Music playlist generator with SoundCloud integration</p>
            </div>

            <div class="content">
                <div class="generate-section">
                    <h2 style="margin-bottom: 15px; color: #1e293b;">✨ Create New Playlist</h2>
                    <p style="margin-bottom: 20px; color: #64748b;">Generate a custom playlist with your favorite music tags</p>
                    <a href="/generate" class="generate-btn">
                        🎵 Generate New Playlist
                    </a>
                </div>

                <h2 style="margin-bottom: 20px; color: #1e293b;">📋 Available Playlists</h2>

                {% if playlists %}
                    {% for playlist in playlists %}
                        <div class="playlist-item">
                            <h3>{{ playlist.name }}</h3>
                            <a href="/playlist/{{ playlist.filename }}">View Playlist →</a>
                        </div>
                    {% endfor %}
                {% else %}
                    <div class="no-playlists">
                        <p>No playlists found. Generate your first playlist to get started!</p>
                    </div>
                {% endif %}

                <div class="instructions">
                    <h3>🚀 How to use</h3>
                    <ol>
                        <li>Click "Generate New Playlist" to create a custom playlist</li>
                        <li>Choose your music tags and preferences</li>
                        <li>View the generated playlist with embedded SoundCloud players</li>
                        <li>Import tracks directly to your SoundCloud account</li>
                    </ol>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    playlists = []
    for html_file in html_files:
        playlists.append(
            {
                "filename": html_file.name,
                "name": html_file.stem.replace("playlist_", "").replace("_", " "),
            }
        )

    return render_template_string(html_content, playlists=playlists)


if __name__ == "__main__":
    print("🎵 new_songs_enjoyer Web Server")
    print("=" * 40)
    print("Starting web server for SoundCloud integration...")
    print("Access your playlists at: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    print("=" * 40)

    app.run(debug=True, host="0.0.0.0", port=5000)
