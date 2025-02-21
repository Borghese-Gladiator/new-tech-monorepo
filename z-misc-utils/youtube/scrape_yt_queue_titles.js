// Get the queue element
const queueElement = document.getElementsByTagName("ytmusic-player-queue")[0];

// Get the list of song elements within the queue
const songElements = queueElement.getElementsByTagName("ytmusic-player-queue-item");

// Initialize an array to store song strings
const songStringList = [];

// Iterate over each song element
for (const songElement of songElements) {
  // Get the song title and author
  const title = songElement.querySelector('.song-title.style-scope.ytmusic-player-queue-item').innerText;
  const author = songElement.querySelector(".byline.style-scope.ytmusic-player-queue-item").innerText;
  
  // Add the formatted string to the list
  songStringList.push(`${author} - ${title}`);
}

// Remove duplicates by converting to a Set and back to an array
const uniqueSongStringList = Array.from(new Set(songStringList));

// Sort the list alphabetically, case insensitive
uniqueSongStringList.sort((a, b) => a.localeCompare(b, undefined, { sensitivity: 'base' }));

// Log the sorted, unique list of songs
console.log(uniqueSongStringList.join("\n"));