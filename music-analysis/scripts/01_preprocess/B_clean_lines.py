#!/usr/bin/env python3
"""
Run this AFTER you run `extract_lines.py`

Script to parse and clean playlist.md for easy splitting and Spotify/YT_Music search
"""

import re
from pathlib import Path


def extract_title_from_markdown_link(line):
    """Extract title from markdown link format [title](url)"""
    match = re.search(r'\[([^\]]+)\]', line)
    if match:
        return match.group(1)
    return line


def remove_url_suffix(line):
    """Remove URL suffix like '=> https://...' or '- https://...' or just 'https://...'"""
    # Remove URLs with various prefixes
    line = re.sub(r'\s*[-=]>?\s*https?://\S+', '', line)
    # Also remove standalone URLs
    line = re.sub(r'\s+https?://\S+', '', line)
    return line


def clean_artist_name(artist):
    """Clean up artist name by removing extra info in parentheses and tags"""
    # Remove things like (Gura), (feat. X), (English), etc. but keep the main part
    # Handle patterns like "Hololive (Gura)" -> "Gura"
    # or "Artist (feat. Someone)" -> "Artist"

    # Special handling for Hololive format: "Hololive (ArtistName)"
    hololive_match = re.match(r'Hololive\s*\(([^)]+)\)', artist, re.IGNORECASE)
    if hololive_match:
        return hololive_match.group(1).strip()

    # Remove irrelevant parentheses with artist info like "( - Justin Bieber)"
    artist = re.sub(r'\s*\(\s*-\s*[^)]+\)', '', artist)

    # Remove trailing (feat. ...), (ED), (OP), etc.
    artist = re.sub(r'\s*\([^)]*(?:feat|ED|OP|OST|from)[^)]*\)', '', artist, flags=re.IGNORECASE)

    # Remove any remaining empty parentheses
    artist = re.sub(r'\s*\(\s*\)', '', artist)

    # Remove duplicate names (e.g., "Mosawo もさを" -> "Mosawo")
    # Keep only the first word if there are duplicates with different scripts
    parts = artist.split()
    if len(parts) > 1:
        # Check if we have both Latin and non-Latin characters
        has_latin = any(c.isascii() and c.isalpha() for c in parts[0])
        has_non_latin = any(not c.isascii() for part in parts[1:] for c in part)
        if has_latin and has_non_latin:
            # Keep only the Latin name
            artist = parts[0]

    return artist.strip()


def clean_song_name(song):
    """Clean up song name by removing extra metadata"""
    # Remove URLs
    song = remove_url_suffix(song)

    # Remove extra notes after '=>'
    song = re.sub(r'\s*=>\s*[^-]+$', '', song)

    # Remove ED/OP tags with numbers (e.g., "ED2", "OP1", "ED 2", "OP 1")
    song = re.sub(r'\s*(?:ED|OP)\s*\d+\s*', '', song, flags=re.IGNORECASE)

    # Remove common video-related phrases (with or without parentheses)
    video_patterns = [
        r'\s*\(?Official Music Video\)?',
        r'\s*\(?Official Video\)?',
        r'\s*\(?Official MV\)?',
        r'\s*\(?Official Audio\)?',
        r'\s*\(?Lyric Video\)?',
        r'\s*\(?Music Video\)?',
        r'\s*\(?MV\)?',
        r'\s*\(?Audio\)?',
        r'\s*\(?Lyrics?\)?',
    ]
    for pattern in video_patterns:
        song = re.sub(pattern, '', song, flags=re.IGNORECASE)

    return song.strip()


def normalize_collaborations(artist):
    """Normalize different collaboration separators to &"""
    # Replace X, ・, × with &
    artist = re.sub(r'\s*[Xx×・]\s*', ' & ', artist)
    return artist


def has_clear_artist_song_format(text):
    """Check if the line has a clear Artist - Song format"""
    # After cleaning, check if there's a dash separator
    # and both sides have content
    if ' - ' not in text:
        return False

    parts = text.split(' - ', 1)
    if len(parts) != 2:
        return False

    artist, song = parts
    artist = artist.strip()
    song = song.strip()

    # Check if artist and song have content
    if not artist or not song:
        return False

    # For CJK characters, even single character can be a valid title
    # So be more lenient with length checks
    has_cjk = any(ord(c) > 0x2E80 for c in song)  # CJK character range starts around 0x2E80

    min_artist_len = 1 if has_cjk else 2
    min_song_len = 1 if has_cjk else 2

    if len(artist) < min_artist_len or len(song) < min_song_len:
        return False

    # Artist shouldn't be too long (likely not an artist if > 100 chars)
    if len(artist) > 100:
        return False

    return True


def parse_and_clean_line(line):
    """
    Parse a line and return (cleaned_line, is_song)
    is_song = True if it's a clear artist - song format
    """
    original = line

    # Remove leading bullet points and numbers
    line = re.sub(r'^\s*[-*•]\s*', '', line)
    line = re.sub(r'^\s*#?\d+\s*', '', line)

    # Extract from markdown links
    if '[' in line and '](' in line:
        line = extract_title_from_markdown_link(line)

    # Remove URLs early
    line = remove_url_suffix(line)

    # Handle Hololive pattern EARLY: "Hololive (Artist) Song" -> "Artist - Song"
    # This handles cases like "Hololive (AZKI) いのち (2024 ver.)" -> "AZKI - いのち (2024 ver.)"
    hololive_match = re.match(r'Hololive\s*\(([^)]+)\)\s+(.*)', line, re.IGNORECASE)
    if hololive_match:
        artist = hololive_match.group(1).strip()
        song = hololive_match.group(2).strip()
        line = f"{artist} - {song}"

    # Remove tags like COVER, KARAOKE (but keep the structure)
    # Replace "COVER -" or "KARAOKE -" with just "-"
    line = re.sub(r'\s*(?:COVER|KARAOKE)\s+', ' ', line, flags=re.IGNORECASE)

    # Remove irrelevant parentheses with artist info like "( - Justin Bieber)" BEFORE splitting
    line = re.sub(r'\s*\(\s*-\s*[^)]+\)', '', line)

    # Remove ED/OP tags with numbers from the beginning/middle of lines
    # This handles cases like "Toradora ED2 | Orange" or "Anime OP1 - Song"
    line = re.sub(r'\s+(?:ED|OP)\s*\d+\s*', ' ', line, flags=re.IGNORECASE)

    # Convert pipe separators to dashes (e.g., "Toradora | Orange" -> "Toradora - Orange")
    line = re.sub(r'\s*\|\s*', ' - ', line)

    # Normalize en dash (–) to regular dash
    line = line.replace('–', '-')

    # Smarter dash normalization: don't normalize dashes in short artist names like "K-On", "A-ha"
    # Only normalize dashes that are clearly separators
    # Pattern 1: "Word- " (dash followed by space but no space before)
    line = re.sub(r'(\w)-\s+', r'\1 - ', line)
    # Pattern 2: " -Word" (space before dash but no space after)
    line = re.sub(r'\s+-(\w)', r' - \1', line)

    # Clean up multiple dashes (e.g., " - - " becomes " - ")
    while ' -  - ' in line or ' - - ' in line:
        line = re.sub(r'\s+-\s+-\s+', ' - ', line)

    # Try to parse as Artist - Song format
    if ' - ' in line:
        parts = line.split(' - ', 1)
        if len(parts) == 2:
            artist, song = parts
            artist = clean_artist_name(artist)
            artist = normalize_collaborations(artist)
            song = clean_song_name(song)
            line = f"{artist} - {song}"

    # Clean up extra whitespace
    line = ' '.join(line.split())
    line = line.strip()

    # Remove any remaining URLs (in case they weren't caught earlier)
    line = remove_url_suffix(line)

    # Check if it's a valid artist - song format
    is_song = has_clear_artist_song_format(line)

    return line, is_song


def process_playlist(input_file, output_songs, output_uncategorized):
    """Process the playlist file and categorize entries"""
    songs = []
    uncategorized = []
    current_year = None
    current_language = None

    # Language headers to preserve
    language_headers = ['English', 'Chinese', 'Japanese', 'Korean', 'German', 'French',
                       'Spanish', 'Russian', 'Instrumental', 'Other']

    with open(input_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Check for year headers like "# 2023"
            year_match = re.match(r'^#\s*(\d{4})\s*$', line)
            if year_match:
                current_year = year_match.group(1)
                # Add year header to both lists
                songs.append(f"\n# {current_year}")
                uncategorized.append(f"\n# {current_year}")
                continue

            # Check for language headers
            if line in language_headers:
                current_language = line
                # Add language header to songs list
                songs.append(f"\n## {current_language}")
                continue

            # Parse and clean the line
            cleaned, is_song = parse_and_clean_line(line)

            if not cleaned:
                continue

            if is_song:
                songs.append(cleaned)
            else:
                # Keep original for uncategorized
                uncategorized.append(line)

    # Write songs to file (markdown format with bullets)
    with open(output_songs, 'w', encoding='utf-8') as f:
        for song in songs:
            # Headers start with # or newline+#, don't add bullets to those
            if song.startswith('#') or song.startswith('\n#'):
                f.write(f"{song}\n")
            else:
                # Add bullet point to song lines
                f.write(f"- {song}\n")

    # Write uncategorized to file (markdown format with bullets)
    with open(output_uncategorized, 'w', encoding='utf-8') as f:
        for item in uncategorized:
            # Headers start with # or newline+#, don't add bullets to those
            if item.startswith('#') or item.startswith('\n#'):
                f.write(f"{item}\n")
            else:
                # Add bullet point to uncategorized lines
                f.write(f"- {item}\n")

    # Count only actual songs/items (not year or language headers)
    num_songs = len([s for s in songs if not s.startswith('\n#') and not s.startswith('#')])
    num_uncategorized = len([u for u in uncategorized if not u.startswith('\n#') and not u.startswith('#')])

    return num_songs, num_uncategorized


def main():
    # Define paths
    base_dir = Path(__file__).parent.parent.parent  # Go up to project root
    input_file = base_dir / "data" / "01_A_extracted_music_by_year.md"
    output_songs = base_dir / "data" / "01_B_cleaned_playlist.md"
    output_uncategorized = base_dir / "data" / "01_B_unrecognized_playlist.md"

    print(f"Processing: {input_file}")
    print(f"Output songs: {output_songs}")
    print(f"Output uncategorized: {output_uncategorized}")
    print()

    num_songs, num_uncategorized = process_playlist(
        input_file, output_songs, output_uncategorized
    )

    print(f"✓ Processed {num_songs + num_uncategorized} total entries")
    print(f"  - {num_songs} songs with clear artist-song format")
    print(f"  - {num_uncategorized} uncategorized entries")
    print()
    print(f"Files created:")
    print(f"  - {output_songs}")
    print(f"  - {output_uncategorized}")


if __name__ == "__main__":
    main()
