const songList = Array.from(document.getElementsByTagName('ytmusic-playlist-shelf-renderer')[0].querySelectorAll(`ytmusic-responsive-list-item-renderer`)).map((el) => el.innerText.split('\n').slice(0, 2))
const songStringList = songList.map((song) => [...song].reverse().join(' - '))
songStringList.sort((a, b) => a.localeCompare(b, undefined, { sensitivity: 'base' }));
console.log(songStringList.join('\n'))