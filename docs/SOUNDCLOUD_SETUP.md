# SoundCloud Integration Setup

This guide explains how to set up and use the SoundCloud integration feature for importing playlists directly to your SoundCloud account.

## Prerequisites

1. **SoundCloud Developer Account**: You need a SoundCloud account and developer app
2. **API Credentials**: Client ID and Access Token from SoundCloud

## Step 1: Get SoundCloud API Credentials

1. **Create a SoundCloud App**:
   - Go to [SoundCloud Developers](https://developers.soundcloud.com/)
   - Sign in with your SoundCloud account
   - Click "Register a new app"
   - Fill in the app details (name, description, website)
   - Note down your **Client ID**

2. **Get Access Token**:
   - You'll need to implement OAuth flow or use SoundCloud's API explorer
   - For testing, you can use SoundCloud's API explorer to get a temporary token
   - The access token allows the app to manage your playlists

## Step 2: Configure Environment Variables

1. **Copy the example environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` file** and add your credentials:
   ```env
   # Last.fm API Key (required)
   LASTFM_API_KEY=your_lastfm_api_key_here

   # SoundCloud API Configuration (for playlist import)
   SOUNDCLOUD_CLIENT_ID=your_soundcloud_client_id_here
   SOUNDCLOUD_ACCESS_TOKEN=your_soundcloud_access_token_here
   ```

## Step 3: Install Dependencies

Make sure you have all required dependencies:

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

## Step 4: Generate Playlists

First, generate some playlists using the main application:

```bash
# Generate a playlist with specific tags
uv run python main.py --tags electronic indie --num-tracks 5

# Or use default configuration
uv run python main.py
```

This will create both JSON and HTML files in the `output/` directory.

## Step 5: Start the Web Server

Launch the web server for SoundCloud integration:

```bash
# Start the Flask web server
uv run python web_server.py
```

You should see:
```
🎵 new_songs_enjoyer Web Server
========================================
Starting web server for SoundCloud integration...
Access your playlists at: http://localhost:5000
Press Ctrl+C to stop the server
========================================
```

## Step 6: Use the Web Interface

1. **Open your browser** and navigate to: `http://localhost:5000`

2. **View available playlists**: You'll see a list of all generated playlists

3. **Click on any playlist** to view the beautiful playlist interface

4. **Import to SoundCloud**:
   - Scroll down to the "Import to SoundCloud" section
   - Click the orange "Import to SoundCloud" button
   - Wait for the import process to complete
   - Get a direct link to your new SoundCloud playlist

## Features

### ✅ What Works
- **Track Search**: Automatically searches for tracks on SoundCloud
- **Playlist Creation**: Creates "new_songs_enjoyer - Discovery" playlist
- **Duplicate Prevention**: Won't add the same track twice
- **Error Handling**: Clear feedback on missing tracks or API issues
- **Beautiful Interface**: Professional playlist display with SoundCloud integration

### ⚠️ Limitations
- **Track Matching**: Some tracks might not be found on SoundCloud
- **API Rate Limits**: SoundCloud has rate limits for API requests
- **Access Token**: Tokens may expire and need to be refreshed

## Troubleshooting

### "SoundCloud API credentials not configured"
- Make sure your `.env` file has valid `SOUNDCLOUD_CLIENT_ID` and `SOUNDCLOUD_ACCESS_TOKEN`
- Double-check that the `.env` file is in the root directory

### "No tracks found on SoundCloud"
- This happens when none of the tracks in your playlist are available on SoundCloud
- Try generating playlists with more popular music tags

### "NetworkError when attempting to fetch resource"
- Make sure the web server is running (`python web_server.py`)
- Access playlists through `http://localhost:5000` instead of opening HTML files directly

### CORS Errors
- Always use the web server interface (`http://localhost:5000`)
- Don't open HTML files directly in the browser for SoundCloud import

## Advanced Usage

### Custom Playlist Names
Edit `adapter/soundcloud_adapter.py` and modify the `PLAYLIST_NAME` constant:

```python
PLAYLIST_NAME = "My Custom Playlist Name"
```

### Different Server Port
Run the web server on a different port:

```python
# Edit web_server.py, change the last line:
app.run(debug=True, host="0.0.0.0", port=8080)
```

### Production Deployment
For production use:
- Set `debug=False` in `web_server.py`
- Use a proper WSGI server like Gunicorn
- Set up proper environment variable management
- Consider using OAuth2 for token management

## API Endpoints

The web server provides these endpoints:

- `GET /` - List all available playlists
- `GET /playlist/<filename>` - Serve specific playlist HTML
- `POST /api/soundcloud/import` - Import playlist to SoundCloud

## Security Notes

- **Never commit your `.env` file** to version control
- **Keep your access tokens secure** and rotate them regularly
- **Use environment variables** for production deployments
- **Consider OAuth2 flow** for user-facing applications
