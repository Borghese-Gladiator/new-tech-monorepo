## YouTube Music setup
[Browser Authentication](https://ytmusicapi.readthedocs.io/en/stable/setup/browser.html)
- `poetry run ytmusicapi browser`
- Verify `browser.json` is created

## Spotify setup
You need to create a .env file at the project root with:
```
# Get Spotify credentials from: https://developer.spotify.com/dashboard
SPOTIFY_CLIENT_ID=your_actual_client_id
SPOTIFY_CLIENT_SECRET=your_actual_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
YTMUSIC_HEADERS_PATH=./browser.json
```

Steps to get Spotify credentials:
1. Go to https://developer.spotify.com/dashboard
2. Log in with your Spotify account
3. Click "Create app"
4. Add redirect URI: http://localhost:8888/callback
5. Copy the Client ID and Client Secret