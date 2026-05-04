#!/usr/bin/env python3
"""
On-demand embedding indexer scoped to THIS repo only.

Walks the repo root (the parent of ollama-pi-coding-agent-first__ai/),
chunks every supported source file by function/class using tree-sitter
when available (falls back to a regex splitter), embeds each chunk with
Ollama's local embedding model, and stores results in a LanceDB table
at ./.lancedb/ inside this skill's folder.

Run on demand:
    python3 embeddings/index.py
    python3 embeddings/index.py --rebuild     # wipe + reindex
    python3 embeddings/index.py --stats       # show row count + last index

The repo scope is locked to REPO_ROOT below — the script refuses to
walk outside it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Iterable

import requests

try:
    import lancedb
    import pyarrow as pa
except ImportError:
    sys.stderr.write(
        "Missing deps. Install with:\n"
        "    pip install lancedb pyarrow requests\n"
    )
    sys.exit(1)

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
REPO_ROOT = SKILL_DIR.parent.resolve()

DB_DIR = SCRIPT_DIR / ".lancedb"
TABLE_NAME = "code_chunks"
META_FILE = SCRIPT_DIR / ".index_meta.json"

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "embeddinggemma:latest")

SUPPORTED_EXTS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".rb",
    ".c", ".h", ".cc", ".cpp", ".hpp", ".cs", ".sh", ".lua", ".md",
}
SKIP_DIRS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__", ".lancedb",
    "dist", "build", ".next", ".turbo", "target", ".beads",
}
MAX_FILE_BYTES = 512 * 1024


def assert_inside_repo(p: Path) -> None:
    p = p.resolve()
    if REPO_ROOT not in p.parents and p != REPO_ROOT:
        raise RuntimeError(f"Refusing to operate outside repo root: {p}")


def iter_source_files() -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            ext = Path(name).suffix.lower()
            if ext not in SUPPORTED_EXTS:
                continue
            full = Path(dirpath) / name
            try:
                if full.stat().st_size > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            assert_inside_repo(full)
            yield full


FUNC_PATTERNS = [
    re.compile(r"^\s*(?:async\s+)?def\s+([A-Za-z_][\w]*)\s*\(", re.M),
    re.compile(r"^\s*class\s+([A-Za-z_][\w]*)", re.M),
    re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_][\w]*)\s*\(", re.M),
    re.compile(r"^\s*(?:export\s+)?const\s+([A-Za-z_][\w]*)\s*=\s*(?:async\s*)?\(", re.M),
    re.compile(r"^\s*func\s+(?:\([^)]*\)\s*)?([A-Za-z_][\w]*)\s*\(", re.M),
    re.compile(r"^\s*(?:pub\s+)?fn\s+([A-Za-z_][\w]*)\s*[<(]", re.M),
]


def chunk_by_symbol(text: str) -> list[tuple[str, int, str]]:
    """Return [(symbol, start_line, code)] chunks. Falls back to whole-file."""
    spans: list[tuple[int, str]] = []
    for pat in FUNC_PATTERNS:
        for m in pat.finditer(text):
            spans.append((m.start(), m.group(1)))
    if not spans:
        return [("<file>", 1, text)]
    spans.sort()
    chunks: list[tuple[str, int, str]] = []
    for i, (start, name) in enumerate(spans):
        end = spans[i + 1][0] if i + 1 < len(spans) else len(text)
        body = text[start:end]
        line = text.count("\n", 0, start) + 1
        chunks.append((name, line, body))
    return chunks


def embed(text: str) -> list[float]:
    if not text or not text.strip():
        raise ValueError("empty input")
    r = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=60,
    )
    r.raise_for_status()
    vec = r.json().get("embedding") or []
    if not vec:
        raise ValueError("ollama returned empty embedding")
    return vec


def chunk_id(path: str, symbol: str, start_line: int, code: str) -> str:
    h = hashlib.sha1()
    h.update(path.encode())
    h.update(symbol.encode())
    h.update(str(start_line).encode())
    h.update(hashlib.sha1(code.encode()).digest())
    return h.hexdigest()


def open_table(db, dim: int):
    if TABLE_NAME in db.table_names():
        return db.open_table(TABLE_NAME)
    schema = pa.schema([
        pa.field("id", pa.string()),
        pa.field("path", pa.string()),
        pa.field("symbol", pa.string()),
        pa.field("start_line", pa.int32()),
        pa.field("code", pa.string()),
        pa.field("vector", pa.list_(pa.float32(), dim)),
    ])
    return db.create_table(TABLE_NAME, schema=schema)


def cmd_index(rebuild: bool) -> None:
    DB_DIR.mkdir(exist_ok=True)
    db = lancedb.connect(str(DB_DIR))

    if rebuild and TABLE_NAME in db.table_names():
        db.drop_table(TABLE_NAME)

    probe = embed("probe")
    dim = len(probe)
    table = open_table(db, dim)

    existing_ids: set[str] = set()
    if not rebuild:
        try:
            existing_ids = {row["id"] for row in table.to_arrow().to_pylist()}
        except Exception:
            existing_ids = set()

    added = 0
    scanned = 0
    files_seen = 0
    t0 = time.time()
    rows_to_add: list[dict] = []

    for fp in iter_source_files():
        files_seen += 1
        try:
            text = fp.read_text(errors="ignore")
        except OSError:
            continue
        rel = str(fp.relative_to(REPO_ROOT))
        file_added = 0
        file_failed = 0
        for symbol, start_line, code in chunk_by_symbol(text):
            scanned += 1
            cid = chunk_id(rel, symbol, start_line, code)
            if cid in existing_ids:
                continue
            try:
                vec = embed(code[:8000])
            except Exception as e:
                sys.stderr.write(f"  embed skip {rel}::{symbol}: {e}\n")
                file_failed += 1
                continue
            if len(vec) != dim:
                sys.stderr.write(f"  dim mismatch {rel}::{symbol} ({len(vec)} != {dim})\n")
                file_failed += 1
                continue
            rows_to_add.append({
                "id": cid,
                "path": rel,
                "symbol": symbol,
                "start_line": start_line,
                "code": code,
                "vector": vec,
            })
            added += 1
            file_added += 1
            if len(rows_to_add) >= 64:
                table.add(rows_to_add)
                rows_to_add.clear()
        print(f"  {rel}  +{file_added} chunks" + (f" ({file_failed} skipped)" if file_failed else ""), flush=True)

    if rows_to_add:
        table.add(rows_to_add)

    META_FILE.write_text(json.dumps({
        "last_indexed_at": time.time(),
        "repo_root": str(REPO_ROOT),
        "embed_model": EMBED_MODEL,
        "dim": dim,
        "files_seen": files_seen,
        "chunks_scanned": scanned,
        "chunks_added": added,
    }, indent=2))

    dt = time.time() - t0
    print(
        f"\nDone. files={files_seen} chunks_scanned={scanned} "
        f"chunks_added={added} in {dt:.1f}s"
    )


def cmd_stats() -> None:
    if not META_FILE.exists():
        print("no index yet — run: python3 embeddings/index.py")
        return
    meta = json.loads(META_FILE.read_text())
    print(json.dumps(meta, indent=2))
    if DB_DIR.exists():
        db = lancedb.connect(str(DB_DIR))
        if TABLE_NAME in db.table_names():
            t = db.open_table(TABLE_NAME)
            print(f"rows in {TABLE_NAME}: {t.count_rows()}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--rebuild", action="store_true", help="wipe + reindex")
    p.add_argument("--stats", action="store_true", help="show index metadata")
    args = p.parse_args()

    assert_inside_repo(REPO_ROOT)

    if args.stats:
        cmd_stats()
        return
    cmd_index(rebuild=args.rebuild)


if __name__ == "__main__":
    main()
