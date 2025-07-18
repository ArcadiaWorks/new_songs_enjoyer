# SoundCloud OAuth Token Setup

Since SoundCloud no longer issues new API keys, you can use your OAuth token from browser storage to authenticate with the SoundCloud API. This token is required for the platform filtering feature to access your liked tracks and prevent duplicate recommendations.

## What This Enables

- **Platform Filtering**: Automatically exclude tracks you've already liked on SoundCloud from new recommendations
- **Personalized Playlists**: Get truly fresh music discoveries based on your actual listening history
- **SoundCloud Integration**: Access your SoundCloud profile and liked tracks data

## How to Get Your SoundCloud OAuth Token

### Method 1: From Browser Storage (Recommended)

1. **Open SoundCloud in your browser** and log in to your account

   - Go to [soundcloud.com](https://soundcloud.com) and make sure you're logged in
   - Navigate to any page (your profile, liked tracks, etc.)

2. **Open Developer Tools**

   - Press `F12` on your keyboard, OR
   - Right-click anywhere on the page → "Inspect" or "Inspect Element", OR
   - Use keyboard shortcut: `Ctrl+Shift+I` (Windows/Linux) or `Cmd+Option+I` (Mac)

3. **Navigate to the Storage tab**

   - **Chrome/Edge**: Click "Application" tab → "Local Storage" in the left sidebar
   - **Firefox**: Click "Storage" tab → "Local Storage" in the left sidebar
   - **Safari**: Click "Storage" tab → "Local Storage" in the left sidebar

4. **Find SoundCloud domain**

   - Look for `https://soundcloud.com` in the Local Storage list
   - Click on it to expand and view stored data

5. **Locate the OAuth token**

   - Look through the key-value pairs for entries like:
     - `oauth_token` (most common)
     - `access_token`
     - `authToken`
     - `sc_anonymous_id` (not the right one - skip this)
   - The token value should be a long string starting with numbers and containing hyphens
   - Example format: `2-294731-123456789-abcdef123456789`

6. **Copy the token value**
   - Double-click the token value to select it
   - Copy it to your clipboard (`Ctrl+C` or `Cmd+C`)

### Method 2: From Network Requests

1. **Open SoundCloud** and log in
2. **Open Developer Tools** → **Network tab**
3. **Refresh the page** or navigate around SoundCloud
4. **Look for API requests** to `api-v2.soundcloud.com`
5. **Check the Authorization header** in any request
6. **Copy the token** after "OAuth " (without the "OAuth " prefix)

### Method 3: From Browser Console

1. **Open SoundCloud** and log in
2. **Open Developer Tools** → **Console tab**
3. **Try running these commands** to find stored tokens:

   ```javascript
   // Check localStorage
   console.log(localStorage);

   // Check for specific keys
   console.log(localStorage.getItem("oauth_token"));
   console.log(localStorage.getItem("access_token"));

   // Check sessionStorage
   console.log(sessionStorage);
   ```

## Adding the Token to Your Environment

1. **Copy your OAuth token** (it should be a long string like `2-294731-123456789-abcdef123456`)
2. **Add it to your .env file**:
   ```bash
   SOUNDCLOUD_OAUTH_TOKEN=your_oauth_token_here
   ```

## Testing Your Setup

1. **Start the server**: `python run.py server`
2. **Run the search test**: `python tests/test_soundcloud_search.py`
3. **Check for successful authentication** (no 401 errors)

## Example Valid Token Format

Your OAuth token should look something like:

```
2-294731-123456789-abcdef123456789
```

## Troubleshooting

### Token Expired

- OAuth tokens can expire
- If you get 401 errors, get a fresh token from your browser
- SoundCloud tokens typically last for the session duration

### Wrong Token Format

- Make sure you copied the full token
- Don't include "OAuth " prefix in your .env file
- Token should be the raw alphanumeric string

### 403 Forbidden

- Your account might not have API access
- Try with a different SoundCloud account
- Some tokens have limited permissions

## Security Note

⚠️ **Keep your OAuth token private!**

- Don't commit it to version control
- Don't share it publicly
- Add `.env` to your `.gitignore`

## Using the Integration

Once configured, you can:

1. **Search for tracks**: The "🎧 View on SoundCloud" buttons will work
2. **Import playlists**: Full playlist import to your SoundCloud account
3. **Embed players**: Real SoundCloud oEmbed players in your HTML

The system will automatically use your OAuth token for all SoundCloud API requests.
