"""
Extracts unique lines from music.md files in two git repositories,
grouping them by the earliest year they appeared and by language.

Keeps the OLDEST timestamp for duplicates across both repos.
Each year's lines are sorted alphabetically with proper Unicode collation,
grouped by detected language (English, Chinese, Japanese, Korean, etc.).
"""
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Tuple
import unicodedata
import locale
import re
from collections import defaultdict

# ---------- Config ----------
REPO1_PATH = Path("path_a")
FILE1_HINT = "entertainment/music/music.md"

REPO2_PATH = Path("path_b")
FILE2_HINT = "Personal/Entertainment/music/music.md"
# -----------------------------------------------

#------------ Patch for sorting unicode ------------
# --- Collation key (ICU -> Unidecode -> locale) ---
try:
    import icu  # pip install PyICU
    _icu_collator = icu.Collator.createInstance(icu.Locale("en_US"))
    _icu_collator.setStrength(icu.Collator.SECONDARY)  # ignore case/accents
    def _collate_key(s: str) -> bytes:
        t = unicodedata.normalize("NFKC", s)
        return _icu_collator.getSortKey(t)  # bytes
except Exception:
    try:
        from unidecode import unidecode  # pip install Unidecode
        locale.setlocale(locale.LC_COLLATE, "")  # use system locale
        def _collate_key(s: str) -> str:
            # Normalize and transliterate (CJK -> romaji/pinyin-like), then locale collation
            t = unicodedata.normalize("NFKC", s)
            t = unidecode(t)
            return locale.strxfrm(t.casefold())
    except Exception:
        # Last resort: locale collation on normalized text
        locale.setlocale(locale.LC_COLLATE, "")
        def _collate_key(s: str) -> str:
            t = unicodedata.normalize("NFKC", s)
            return locale.strxfrm(t.casefold())

# Optional: soften punctuation/hyphens for sort without changing output text
_LEADING_NOISE = re.compile(r"^[\s\-\*\.\d\)\(・、，。・【】\[\]]+")
def _normalize_for_sort(s: str) -> str:
    t = _LEADING_NOISE.sub("", s)              # drop leading bullets / noise
    t = t.replace("—", "-").replace("–", "-")  # normalize dashes
    return t
#----------------------------------------------------


def detect_language(text: str) -> str:
    """
    Detect the language of a text line based on character analysis.

    Returns: 'English', 'Chinese', 'Japanese', 'Korean', 'German', 'French',
             'Spanish', 'Russian', 'Instrumental', or 'Other'
    """
    # Remove common punctuation and whitespace for analysis
    clean_text = text.strip()

    # Count character types
    char_counts = {
        'chinese': 0,
        'hiragana': 0,
        'katakana': 0,
        'korean': 0,
        'cyrillic': 0,
        'latin': 0,
        'digits': 0,
    }

    for char in clean_text:
        code = ord(char)
        # Chinese (CJK Unified Ideographs)
        if 0x4E00 <= code <= 0x9FFF:
            char_counts['chinese'] += 1
        # Japanese Hiragana
        elif 0x3040 <= code <= 0x309F:
            char_counts['hiragana'] += 1
        # Japanese Katakana
        elif 0x30A0 <= code <= 0x30FF:
            char_counts['katakana'] += 1
        # Korean Hangul
        elif 0xAC00 <= code <= 0xD7AF:
            char_counts['korean'] += 1
        # Cyrillic (Russian, Ukrainian, etc.)
        elif 0x0400 <= code <= 0x04FF:
            char_counts['cyrillic'] += 1
        # Latin alphabet
        elif char.isalpha() and char.isascii():
            char_counts['latin'] += 1
        elif char.isdigit():
            char_counts['digits'] += 1

    total_chars = sum(char_counts.values())

    # If mostly numbers/punctuation, check for instrumental indicators
    if total_chars < 3:
        lower = clean_text.lower()
        if 'ost' in lower or 'instrumental' in lower or 'bgm' in lower:
            return 'Instrumental'
        return 'Other'

    # Determine language by character composition
    # Japanese: has hiragana/katakana (even if mixed with Chinese characters)
    if char_counts['hiragana'] > 0 or char_counts['katakana'] > 0:
        return 'Japanese'

    # Chinese: has Chinese characters but no hiragana/katakana
    if char_counts['chinese'] > 0:
        return 'Chinese'

    # Korean
    if char_counts['korean'] > 0:
        return 'Korean'

    # Russian/Cyrillic
    if char_counts['cyrillic'] > 0:
        return 'Russian'

    # European languages (Latin-based)
    if char_counts['latin'] > 0:
        lower = clean_text.lower()

        # German indicators
        if any(word in lower for word in ['über', 'für', 'von', 'und', 'der', 'die', 'das', 'ä', 'ö', 'ü', 'ß']):
            return 'German'

        # French indicators
        if any(word in lower for word in ['le ', 'la ', 'les ', 'de ', 'des ', 'du ', 'à ', 'ç', 'é', 'è', 'ê']):
            return 'French'

        # Spanish indicators
        if any(word in lower for word in ['el ', 'la ', 'los ', 'las ', 'de ', 'del ', 'y ', 'ñ', 'á', 'í', 'ó', 'ú']):
            return 'Spanish'

        # Default to English for Latin scripts
        return 'English'

    return 'Other'


def run(cmd, cwd):
    return subprocess.check_output(cmd, cwd=str(cwd), stderr=subprocess.STDOUT).decode("utf-8", errors="replace")

def list_all_commits(repo_root: Path):
    fmt = r"%H%x09%ct"
    out = run(["git", "log", "--all", "--reverse", "--date-order", f"--format={fmt}"], repo_root)
    commits = []
    for line in out.splitlines():
        if not line.strip():
            continue
        sha, ts = line.split("\t", 1)
        commits.append((sha, int(ts)))
    return commits

def file_path_predicate(path: str, hint: str):
    """Only match music.md, skip music_queue/music_history/music_iced"""
    path = path.lower()
    if any(skip in path for skip in ["music_queue", "music_history", "music_iced"]):
        return False
    return "music.md" in path or (hint and hint.lower() in path)

def files_touched_in_commit(repo_root: Path, commit: str):
    out = run(["git", "show", "--format=", "--name-only", "--diff-filter=AMR", "--find-renames", "--find-copies", commit], repo_root)
    return [l.strip() for l in out.splitlines() if l.strip()]

def iter_added_lines_from_patch(patch_text: str):
    current_file = None
    for raw in patch_text.splitlines():
        if raw.startswith("+++ "):
            current_file = raw[6:] if raw.startswith("+++ b/") else raw[4:]
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            line = raw[1:].rstrip("\r\n")
            if line.strip():
                yield current_file, line

def show_filtered_patch(repo_root: Path, commit: str, files: List[str]):
    if not files:
        return ""
    cmd = ["git", "show", "--format=", "--find-renames", "--find-copies", "--diff-filter=AMR", commit, "--", *files]
    return run(cmd, repo_root)

def collect_first_seen_lines(repo_root: Path, hint_path: str) -> Dict[str, int]:
    commits = list_all_commits(repo_root)
    first_seen = {}
    for sha, epoch in commits:
        files = files_touched_in_commit(repo_root, sha)
        relevant = [f for f in files if file_path_predicate(f, hint_path)]
        if not relevant:
            continue
        patch = show_filtered_patch(repo_root, sha, relevant)
        for fpath, added in iter_added_lines_from_patch(patch):
            if not file_path_predicate(fpath, hint_path):
                continue
            if added not in first_seen:
                first_seen[added] = epoch
    return first_seen

def utc_year(epoch):
    return datetime.fromtimestamp(epoch, tz=timezone.utc).year

def main():
    repo1 = collect_first_seen_lines(REPO1_PATH, FILE1_HINT)
    repo2 = collect_first_seen_lines(REPO2_PATH, FILE2_HINT)

    # Deduplicate by text, keep the OLDEST timestamp
    combined = {}
    for m in (repo1, repo2):
        for txt, ts in m.items():
            combined[txt] = ts if txt not in combined else min(combined[txt], ts)

    # Group by year, then by language
    grouped: Dict[int, Dict[str, List[Tuple[int, str]]]] = defaultdict(lambda: defaultdict(list))

    for txt, ts in combined.items():
        year = utc_year(ts)
        language = detect_language(txt)
        grouped[year][language].append((ts, txt))

    # Sort each language's lines alphabetically within each year
    for year in grouped:
        for language in grouped[year]:
            grouped[year][language].sort(
                key=lambda item: (
                    _collate_key(_normalize_for_sort(item[1])),
                    item[1],       # tie-breaker: original text
                    item[0],       # tie-breaker: timestamp
                )
            )

    # Define language order for output
    language_order = [
        'English',
        'Chinese',
        'Japanese',
        'Korean',
        'German',
        'French',
        'Spanish',
        'Russian',
        'Instrumental',
        'Other',
    ]

    # Write Markdown
    md_path = Path("music_by_year.md")
    with md_path.open("w", encoding="utf-8") as f:
        for year in sorted(grouped.keys()):
            f.write(f"# {year}\n")

            # Output languages in defined order
            for language in language_order:
                if language in grouped[year]:
                    f.write(f"{language}\n")
                    for _, line in grouped[year][language]:
                        f.write(f"- {line}\n")
                    f.write("\n")

            # Handle any unexpected languages not in the order list
            for language in sorted(grouped[year].keys()):
                if language not in language_order:
                    f.write(f"{language}\n")
                    for _, line in grouped[year][language]:
                        f.write(f"- {line}\n")
                    f.write("\n")

    print(f"Markdown written to: {md_path.resolve()}")

    # Print statistics
    print("\nStatistics by year and language:")
    for year in sorted(grouped.keys()):
        print(f"\n{year}:")
        for language in language_order:
            if language in grouped[year]:
                count = len(grouped[year][language])
                print(f"  {language}: {count}")

if __name__ == "__main__":
    main()
