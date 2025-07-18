# Troubleshooting Guide

This guide covers common issues you might encounter when using new_songs_enjoyer, with a focus on platform filtering problems.

## Table of Contents

- [Basic Setup Issues](#basic-setup-issues)
- [SoundCloud Integration Issues](#soundcloud-integration-issues)
- [Spotify Integration Issues](#spotify-integration-issues)
- [Platform Filtering Issues](#platform-filtering-issues)
- [Performance Issues](#performance-issues)
- [Network and API Issues](#network-and-api-issues)
- [Configuration Issues](#configuration-issues)
- [Getting Help](#getting-help)

## Basic Setup Issues

### Python/uv Installation Problems

**Problem**: `uv` command not found

```bash
uv: command not found
```

**Solutions**:

1. Install uv using the official installer:

   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. Restart your terminal after installation
3. Check if uv is in your PATH: `echo $PATH`

**Problem**: Python version compatibility

```bash
Python 3.7 is not supported
```

**Solution**: Upgrade to Python 3.8 or higher:

```bash
# Check your Python version
python --version

# Install Python 3.8+ using your system package manager
# macOS: brew install python@3.11
# Ubuntu: sudo apt install python3.11
# Windows: Download from python.org
```

### Last.fm API Key Issues

**Problem**: Invalid API key error

```bash
ERROR - Invalid API key
```

**Solutions**:

1. Check your `.env` file contains the correct API key:
   ```bash
   LASTFM_API_KEY=your_actual_api_key_here
   ```
2. Get a new API key from [Last.fm API](https://www.last.fm/api)
3. Ensure no extra spaces or quotes around the key
4. Verify the `.env` file is in the project root directory

## SoundCloud Integration Issues

### OAuth Token Extraction Problems

**Problem**: Can't find OAuth token in browser storage

```bash
No oauth_token found in localStorage
```

**Solutions**:

1. **Make sure you're logged in** to SoundCloud in your browser
2. **Try different storage locations**:
   - Local Storage → soundcloud.com
   - Session Storage → soundcloud.com
   - Cookies → soundcloud.com
3. **Look for different key names**:
   - `oauth_token` (most common)
   - `access_token`
   - `authToken`
   - `sc_oauth_token`
4. **Try the Network method** (see SOUNDCLOUD_OAUTH_SETUP.md)

**Problem**: Token format looks wrong

```bash
Token should start with numbers like: 2-294731-123456789-abcdef
```

**Solutions**:

1. Don't include the "OAuth " prefix in your .env file
2. Copy only the alphanumeric token value
3. Ensure you copied the complete token (they're quite long)

### SoundCloud API Authentication Issues

**Problem**: 401 Unauthorized error

```bash
ERROR - SoundCloud API returned 401: Unauthorized
```

**Solutions**:

1. **Token expired**: Get a fresh token from your browser
2. **Wrong token**: Double-check you copied the correct token
3. **Token format**: Ensure no extra characters or spaces
4. **Account issues**: Try with a different SoundCloud account

**Problem**: 403 Forbidden error

```bash
ERROR - SoundCloud API returned 403: Forbidden
```

**Solutions**:

1. Your account may not have API access
2. The token may have limited permissions
3. Try extracting a fresh token after logging out and back in
4. Some corporate/school networks block SoundCloud API

### SoundCloud Rate Limiting

**Problem**: Too many requests error

```bash
ERROR - SoundCloud API rate limit exceeded
```

**Solutions**:

1. Wait 5-10 minutes before trying again
2. Reduce the number of tracks you're requesting
3. The application automatically handles rate limiting with backoff

## Spotify Integration Issues

### Spotify App Setup Problems

**Problem**: Invalid client credentials

```bash
ERROR - Spotify authentication failed: Invalid client
```

**Solutions**:

1. **Double-check credentials** in your `.env` file:
   ```bash
   SPOTIFY_CLIENT_ID=your_client_id_here
   SPOTIFY_CLIENT_SECRET=your_client_secret_here
   ```
2. **Verify app settings** in Spotify Developer Dashboard:
   - App name and description are filled
   - Redirect URI is set (even if not used)
3. **Check app status**: Ensure your app is not in "Development Mode" restrictions

### Spotify Access Token Issues

**Problem**: Access token expired

```bash
ERROR - Spotify API returned 401: The access token expired
```

**Solutions**:

1. **Get a fresh token** from Spotify Web API Console
2. **Implement refresh token flow** for long-term use
3. **Check token format**: Should start with `BQA` or similar

**Problem**: Insufficient scope permissions

```bash
ERROR - Insufficient scope: user-library-read
```

**Solutions**:

1. **Re-authorize with correct scope**:
   - Go to Spotify Web API Console
   - Check `user-library-read` scope
   - Generate new token
2. **Verify scope in authorization URL** if using custom flow

### Spotify API Rate Limiting

**Problem**: Rate limit exceeded

```bash
ERROR - Spotify API rate limit exceeded
```

**Solutions**:

1. Wait for the rate limit to reset (usually 1 minute)
2. The application automatically handles rate limiting
3. Consider reducing the frequency of requests

## Platform Filtering Issues

### No Filtering Applied

**Problem**: Filtering seems to be disabled

```bash
INFO - Platform filtering is disabled
```

**Solutions**:

1. **Check config.yaml**:
   ```yaml
   platform_filtering:
     enabled: true # Must be true
   ```
2. **Verify platform-specific settings**:
   ```yaml
   soundcloud:
     enabled: true # Enable SoundCloud filtering
   spotify:
     enabled: true # Enable Spotify filtering
   ```
3. **Check credentials** are properly set in `.env`

### Partial Filtering Only

**Problem**: Only one platform is filtering

```bash
WARNING - Spotify filtering failed, continuing with SoundCloud only
```

**Solutions**:

1. **Check logs** for specific error messages
2. **Verify credentials** for the failing platform
3. **Test each platform individually**:
   ```bash
   # Test SoundCloud only
   uv run python main.py --tags electronic --num-tracks 5
   ```
4. **Partial filtering is normal** - the app continues with available platforms

### No Matches Found

**Problem**: Filtering reports 0 matches but you have liked songs

```bash
INFO - Platform filtering: 0 tracks filtered (0 SoundCloud, 0 Spotify)
```

**Possible causes**:

1. **Different music taste**: Your liked songs don't overlap with Last.fm recommendations
2. **Matching algorithm**: Slight differences in artist/track names
3. **Limited liked songs**: Small library on the platforms
4. **Tag mismatch**: Your liked songs don't match the search tags

**This is often normal behavior** - it means you're getting truly fresh recommendations!

### Matching Algorithm Issues

**Problem**: Songs that should match aren't being filtered

```bash
Expected "Artist - Song" to be filtered but it wasn't
```

**Solutions**:

1. **Check exact spelling** in both platforms
2. **Artist name variations**: "The Beatles" vs "Beatles"
3. **Track title differences**: "Song (Remix)" vs "Song"
4. **Case sensitivity**: The algorithm is case-insensitive but check for typos

## Performance Issues

### Slow Filtering Process

**Problem**: Platform filtering takes a long time

```bash
INFO - Fetching liked songs... (this may take a while)
```

**Causes and solutions**:

1. **Large music library**: 1000+ liked songs take time to process
2. **Network latency**: Slow internet connection
3. **API rate limits**: Automatic backoff slows down requests

**Normal behavior**: First run is slower, subsequent runs use caching

### Memory Usage Issues

**Problem**: High memory usage with large libraries

```bash
MemoryError: Unable to allocate memory
```

**Solutions**:

1. **Reduce batch size** in the code (advanced users)
2. **Close other applications** to free memory
3. **Use streaming processing** (requires code modification)

## Network and API Issues

### Connection Problems

**Problem**: Network timeouts

```bash
ERROR - Connection timeout to api.spotify.com
```

**Solutions**:

1. **Check internet connection**
2. **Try different network** (mobile hotspot, different WiFi)
3. **Check firewall settings**
4. **Corporate networks**: May block music API access

### DNS Resolution Issues

**Problem**: Can't resolve API hostnames

```bash
ERROR - Failed to resolve api.spotify.com
```

**Solutions**:

1. **Check DNS settings**: Try 8.8.8.8 or 1.1.1.1
2. **Flush DNS cache**:

   ```bash
   # Windows
   ipconfig /flushdns

   # macOS
   sudo dscacheutil -flushcache

   # Linux
   sudo systemctl restart systemd-resolved
   ```

## Configuration Issues

### YAML Syntax Errors

**Problem**: Configuration file parsing errors

```bash
ERROR - Invalid YAML syntax in config.yaml
```

**Solutions**:

1. **Check indentation**: YAML is sensitive to spaces
2. **Validate YAML**: Use online YAML validator
3. **Check quotes**: Strings with special characters need quotes
4. **Reset to default**: Copy from the example in README.md

### Environment Variable Issues

**Problem**: Environment variables not loading

```bash
ERROR - SOUNDCLOUD_OAUTH_TOKEN not found
```

**Solutions**:

1. **Check .env file location**: Must be in project root
2. **Check .env syntax**: No spaces around `=`

   ```bash
   # Correct
   SOUNDCLOUD_OAUTH_TOKEN=your_token_here

   # Incorrect
   SOUNDCLOUD_OAUTH_TOKEN = your_token_here
   ```

3. **Check file permissions**: Ensure .env is readable
4. **Restart application**: Changes require restart

## Getting Help

### Enable Debug Logging

Add debug logging to get more information:

```yaml
# In config.yaml
logging:
  level: "DEBUG" # Change from INFO to DEBUG
```

This will show detailed API requests and responses.

### Collect Diagnostic Information

When reporting issues, include:

1. **Operating system and version**
2. **Python version**: `python --version`
3. **uv version**: `uv --version`
4. **Error messages** (full stack trace)
5. **Configuration** (remove sensitive tokens)
6. **Steps to reproduce** the issue

### Test Individual Components

Test each component separately:

```bash
# Test Last.fm API
uv run python -c "import config; print('Last.fm API key:', config.get_config().lastfm_api_key[:10] + '...')"

# Test SoundCloud token
uv run python -c "from adapter.soundcloud_adapter import SoundCloudAdapter; adapter = SoundCloudAdapter.from_env(); print('SoundCloud OK' if adapter else 'SoundCloud failed')"

# Test basic functionality without filtering
uv run python main.py --tags electronic --num-tracks 3
```

### Common Log Messages Explained

**INFO messages** (normal operation):

- `Platform filtering enabled` - Filtering is working
- `Fetching liked songs from SoundCloud` - Getting your library
- `Platform filtering: X tracks filtered` - Filtering results

**WARNING messages** (partial failures):

- `SoundCloud authentication failed, skipping` - SoundCloud unavailable but continuing
- `Rate limit hit, backing off` - Temporary slowdown

**ERROR messages** (serious problems):

- `Invalid API credentials` - Check your .env file
- `Network connection failed` - Check internet/firewall
- `Configuration error` - Check config.yaml syntax

### Still Need Help?

If you're still having issues:

1. **Check existing issues** in the project repository
2. **Create a new issue** with diagnostic information
3. **Include logs** with sensitive information removed
4. **Describe expected vs actual behavior**

Remember: Platform filtering is an advanced feature that depends on external APIs. Basic playlist generation should work even if filtering fails.
