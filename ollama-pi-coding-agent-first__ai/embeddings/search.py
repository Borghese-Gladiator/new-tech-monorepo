#!/usr/bin/env python3
"""
Semantic search over the local LanceDB index built by index.py.

Usage:
    python3 embeddings/search.py "where do we configure ollama"
    python3 embeddings/search.py --k 10 "auth flow"
    python3 embeddings/search.py --json "embedding indexer"

Designed to be wired as a tool for aider / any agent — the --json
mode prints {results: [{path, symbol, start_line, score, snippet}]}.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests

try:
    import lancedb
except ImportError:
    sys.stderr.write("Missing deps. pip install lancedb requests\n")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).resolve().parent
DB_DIR = SCRIPT_DIR / ".lancedb"
TABLE_NAME = "code_chunks"

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "embeddinggemma:latest")


def embed(text: str) -> list[float]:
    r = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["embedding"]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("query")
    p.add_argument("--k", type=int, default=5)
    p.add_argument("--json", action="store_true", dest="as_json")
    args = p.parse_args()

    if not DB_DIR.exists():
        sys.stderr.write("no index — run: python3 embeddings/index.py\n")
        sys.exit(2)

    db = lancedb.connect(str(DB_DIR))
    if TABLE_NAME not in db.table_names():
        sys.stderr.write("index table missing — run: python3 embeddings/index.py\n")
        sys.exit(2)
    table = db.open_table(TABLE_NAME)

    qvec = embed(args.query)
    hits = table.search(qvec).limit(args.k).to_list()

    results = []
    for h in hits:
        snippet = (h.get("code") or "")[:400]
        results.append({
            "path": h["path"],
            "symbol": h["symbol"],
            "start_line": h["start_line"],
            "score": float(h.get("_distance", 0.0)),
            "snippet": snippet,
        })

    if args.as_json:
        print(json.dumps({"query": args.query, "results": results}, indent=2))
        return

    for r in results:
        print(f"{r['path']}:{r['start_line']}  [{r['symbol']}]  d={r['score']:.3f}")
        print("  " + r["snippet"].replace("\n", "\n  "))
        print()


if __name__ == "__main__":
    main()
