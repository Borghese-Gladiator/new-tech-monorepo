## YouTube Music setup
Browser Headers
1. Open YouTube Music in Chrome:
    - https://music.youtube.com
    - (Make sure you're logged in)
2. Open DevTools:
    - Press F12 or Cmd+Option+I (Mac)
    - Click the Network tab
3. Filter requests:
    - Type browse in the filter box
    - Refresh the page if needed
    - Click on any browse request
4. Copy the request:
    - Right-click on the request
    - Select: Copy → Copy as cURL (bash)
5. Generate browser.json:
    - `cd /Users/timothy.shee/GitHub/new-tech-monorepo/music-analysis`
    - `poetry run ytmusicapi browser`
      - Paste the cURL command when prompted
      - Press Enter
6. Verify `browser.json` is created
    - ls -la browser.json


## Spotify setup