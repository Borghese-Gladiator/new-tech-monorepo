// Function to get text content of elements matching the selector
const getTextContentFromSelector = (selector) => 
  Array.from(document.querySelectorAll(selector)).map((el) => el.textContent.trim());

// Get video titles and authors
const videoTitles = getTextContentFromSelector(".ytd-playlist-video-list-renderer #video-title");
const videoAuthors = getTextContentFromSelector(".ytd-playlist-video-list-renderer #tooltip");
videoAuthors.shift(); // Remove the first element which is null

// Combine titles and authors into an array of objects
const videos = videoTitles.map((title, idx) => ({ title, author: videoAuthors[idx] }));

// Sort videos by author name
videos.sort((a, b) => a.author.toLowerCase().localeCompare(b.author.toLowerCase()));

// Log the sorted videos
console.log(videos.map((video) => `${video.author} - ${video.title}`).join('\n'));