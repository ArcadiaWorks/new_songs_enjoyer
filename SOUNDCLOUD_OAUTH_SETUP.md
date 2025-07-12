# SoundCloud OAuth Token Setup

Since SoundCloud no longer issues new API keys, you can use your OAuth token from browser storage to authenticate with the SoundCloud API.

## How to Get Your SoundCloud OAuth Token

### Method 1: From Browser Storage (Recommended)

1. **Open SoundCloud in your browser** and log in to your account
2. **Open Developer Tools** (F12 or right-click → Inspect)
3. **Go to the Application/Storage tab**
4. **Find Local Storage** or **Session Storage**
5. **Look for SoundCloud domain** (soundcloud.com)
6. **Find the OAuth token** - it will be labeled something like:
   - `oauth_token`
   - `access_token`
   - `authToken`
   - Or similar key containing a long alphanumeric string

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
   console.log(localStorage.getItem('oauth_token'));
   console.log(localStorage.getItem('access_token'));

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
