"""
Extracts unique lines from music.md files in two git repositories,
grouping them by the earliest year they appeared.

Keeps the OLDEST timestamp for duplicates across both repos.
Each year's lines are sorted alphabetically with proper Unicode collation.
"""
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Tuple

# ---------- Config ----------
REPO1_PATH = Path("path_a")
FILE1_HINT = "entertainment/music/music.md"

REPO2_PATH = Path("path_b")
FILE2_HINT = "Personal/Entertainment/music/music.md"
# -----------------------------------------------

#------------ Patch for sorting unicode ------------
# add near the top with other imports
import unicodedata, locale
from typing import Tuple

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
import re
_LEADING_NOISE = re.compile(r"^[\s\-\*\.\d\)\(・、，。・【】\[\]]+")
def _normalize_for_sort(s: str) -> str:
    t = _LEADING_NOISE.sub("", s)              # drop leading bullets / noise
    t = t.replace("—", "-").replace("–", "-")  # normalize dashes
    return t
#----------------------------------------------------


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

    # Group by year
    grouped: Dict[int, List[Tuple[int, str]]] = {}
    for txt, ts in combined.items():
        grouped.setdefault(utc_year(ts), []).append((ts, txt))

    # Sort each year's lines alphabetically (case-insensitive)
    ## for year in grouped:
    ##     grouped[year].sort(key=lambda x: x[1].lower())
    for year in grouped:
        grouped[year].sort(
            key=lambda item: (
                _collate_key(_normalize_for_sort(item[1])),
                item[1],       # tie-breaker: original text
                item[0],       # tie-breaker: timestamp
            )
        )

    # Write Markdown
    md_path = Path("music_by_year.md")
    with md_path.open("w", encoding="utf-8") as f:
        for year in sorted(grouped.keys()):
            f.write(f"# {year}\n")
            for _, line in grouped[year]:
                f.write(f"- {line}\n")
            f.write("\n")

    print(f"Markdown written to: {md_path.resolve()}")

if __name__ == "__main__":
    main()
