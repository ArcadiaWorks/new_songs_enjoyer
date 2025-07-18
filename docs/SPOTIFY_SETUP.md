# Spotify Integration Setup

The Spotify integration allows the platform filtering feature to access your Spotify liked songs and prevent duplicate recommendations. This is an optional feature that works alongside or instead of SoundCloud filtering.

## What This Enables

- **Platform Filtering**: Automatically exclude tracks you've already liked on Spotify from new recommendations
- **Multi-Platform Filtering**: Combine with SoundCloud filtering for comprehensive duplicate prevention
- **Spotify Library Access**: Access your Spotify saved tracks for filtering purposes

## Prerequisites

- A Spotify account (free or premium)
- A Spotify Developer account (free)
- Basic understanding of API credentials

## Step 1: Create a Spotify App

1. **Go to Spotify Developer Dashboard**

   - Visit [developer.spotify.com](https://developer.spotify.com/)
   - Click "Log in" and use your Spotify account credentials

2. **Create a New App**

   - Click "Create app" button
   - Fill in the required information:
     - **App name**: `new_songs_enjoyer` (or any name you prefer)
     - **App description**: `Music discovery tool for filtering liked songs`
     - **Website**: Leave blank or add your personal website
     - **Redirect URI**: `http://localhost:8080/callback` (for local development)
   - Check the boxes for Terms of Service and Branding Guidelines
   - Click "Save"

3. **Get Your App Credentials**
   - In your new app's dashboard, click "Settings"
   - Copy your **Client ID** and **Client Secret**
   - Keep these secure - you'll need them for configuration

## Step 2: Get User Access Token

Since the application needs to access your personal liked songs, you need a user access token with the `user-library-read` scope.

### Method 1: Using Spotify's Web API Console (Recommended)

1. **Go to Spotify Web API Console**

   - Visit [developer.spotify.com/console/get-current-user-saved-tracks/](https://developer.spotify.com/console/get-current-user-saved-tracks/)

2. **Authorize the Request**

   - Click "Get Token" button
   - Check the `user-library-read` scope
   - Click "Request Token"
   - Log in with your Spotify account if prompted
   - Authorize the application

3. **Copy the Access Token**
   - The console will show an access token
   - Copy this token - it starts with `BQA` or similar
   - This token is valid for 1 hour

### Method 2: Using Authorization Code Flow (Advanced)

If you need a longer-lasting solution, you can implement the full OAuth flow:

1. **Authorization URL**

   ```
   https://accounts.spotify.com/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=http://localhost:8080/callback&scope=user-library-read
   ```

2. **Exchange Code for Token**
   - Use the authorization code from the callback to get an access token
   - This requires implementing token refresh logic

## Step 3: Configure Environment Variables

Add your Spotify credentials to your `.env` file:

```bash
# Spotify API Configuration (optional)
SPOTIFY_CLIENT_ID=your_spotify_client_id_here
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here
SPOTIFY_ACCESS_TOKEN=your_spotify_access_token_here
```

## Step 4: Enable Spotify Filtering

Update your `config.yaml` to enable Spotify filtering:

```yaml
platform_filtering:
  enabled: true
  spotify:
    enabled: true # Set to true to enable Spotify filtering
    client_id: "${SPOTIFY_CLIENT_ID}"
    client_secret: "${SPOTIFY_CLIENT_SECRET}"
    access_token: "${SPOTIFY_ACCESS_TOKEN}"
```

## Testing Your Setup

1. **Test the configuration**:

   ```bash
   uv run python -c "from adapter.spotify_adapter import SpotifyAdapter; adapter = SpotifyAdapter.from_env(); print('Spotify setup successful!' if adapter else 'Setup failed')"
   ```

2. **Run a filtering test**:

   ```bash
   uv run python main.py --tags electronic --num-tracks 10
   ```

3. **Check the logs** for Spotify filtering activity

## Token Management

### Access Token Expiration

- Spotify access tokens expire after 1 hour
- You'll need to refresh them regularly for continuous use
- Consider implementing refresh token logic for production use

### Getting Fresh Tokens

When your token expires:

1. **Quick Method**: Use the Web API Console again to get a new token
2. **Automated Method**: Implement refresh token flow in your application
3. **Manual Method**: Re-run the authorization flow

## Troubleshooting

### Invalid Client Credentials

- Double-check your Client ID and Client Secret
- Ensure they're correctly set in your `.env` file
- Verify your Spotify app is properly configured

### Access Token Issues

- **401 Unauthorized**: Token expired or invalid - get a fresh token
- **403 Forbidden**: Missing required scopes - ensure `user-library-read` is included
- **429 Rate Limited**: Too many requests - implement rate limiting

### Scope Permissions

The application requires the `user-library-read` scope to access your liked songs:

- This scope allows reading your saved tracks
- It does NOT allow modifying your library
- It's a read-only permission for filtering purposes

### Network Issues

- Ensure you have internet connectivity
- Check if Spotify API is accessible from your network
- Some corporate networks may block Spotify API calls

## Security Best Practices

### Protect Your Credentials

- Never commit API credentials to version control
- Use environment variables for all sensitive data
- Keep your Client Secret private
- Regularly rotate access tokens

### Minimal Permissions

- Only request the `user-library-read` scope
- Don't request additional permissions unless needed
- Review app permissions periodically

## Advanced Configuration

### Rate Limiting

Spotify has rate limits for API calls:

- **Web API**: 100 requests per minute per user
- **Client Credentials**: Higher limits for app-only requests
- The application automatically handles rate limiting with exponential backoff

### Batch Processing

- Spotify allows fetching up to 50 tracks per request
- The application automatically batches requests for efficiency
- Large libraries (1000+ tracks) may take a few seconds to process

### Caching

- Liked songs are cached during the session
- Cache is cleared when the application restarts
- Consider implementing persistent caching for better performance

## Integration with SoundCloud

You can use both Spotify and SoundCloud filtering simultaneously:

```yaml
platform_filtering:
  enabled: true
  soundcloud:
    enabled: true
    oauth_token: "${SOUNDCLOUD_OAUTH_TOKEN}"
  spotify:
    enabled: true
    client_id: "${SPOTIFY_CLIENT_ID}"
    client_secret: "${SPOTIFY_CLIENT_SECRET}"
    access_token: "${SPOTIFY_ACCESS_TOKEN}"
```

This will filter against both platforms, providing comprehensive duplicate prevention.
