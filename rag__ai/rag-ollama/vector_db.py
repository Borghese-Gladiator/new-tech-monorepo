# vector_db.py
import faiss
import json
import numpy as np
import re
import ast
from typing import Any, List, Optional

from ollama import embed  # keep your existing import
# If you named the model differently, update EMBED_MODEL
EMBED_MODEL = "mxbai-embed-large"
INDEX_PATH = "index.faiss"
META_PATH = "index_meta.json"


def extract_embeddings_from_text(text: str) -> Optional[List[List[float]]]:
    """
    Find a substring like 'embeddings=[ [..], [..] ]' and parse it with ast.literal_eval.
    Returns list-of-lists or None.
    """
    key = "embeddings"
    idx = text.find(key + "=")
    if idx == -1:
        return None

    i = idx + len(key) + 1
    while i < len(text) and text[i].isspace():
        i += 1

    if i >= len(text) or text[i] != "[":
        return None

    depth = 0
    start = i
    end = None
    while i < len(text):
        ch = text[i]
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
        i += 1

    if end is None:
        return None

    candidate = text[start:end]
    try:
        parsed = ast.literal_eval(candidate)
        return parsed
    except Exception:
        return None


def coerce_embed_response(resp: Any) -> List[List[float]]:
    """
    Convert different possible shapes of a response from ollama.embed into a list-of-vectors.
    Raises ValueError with a helpful message if it can't.
    """
    # 1) If it's already a list/tuple
    if isinstance(resp, (list, tuple)):
        if len(resp) == 0:
            raise ValueError("Embedding response is an empty list.")
        first = resp[0]
        if isinstance(first, (int, float)):
            # single vector supplied as one flat list -> wrap
            return [list(map(float, resp))]
        # assume it's list-of-vectors
        return [list(map(float, v)) for v in resp]

    # 2) If it's a dict with common keys
    if isinstance(resp, dict):
        for key in ("embeddings", "data", "vectors", "results"):
            if key in resp:
                candidate = resp[key]
                # nested data: { "data": {"embeddings": [...] }}
                if isinstance(candidate, dict) and "embeddings" in candidate:
                    candidate = candidate["embeddings"]
                # dict-of-index -> convert to list if possible
                if isinstance(candidate, dict):
                    try:
                        candidate = [candidate[k] for k in sorted(candidate.keys(), key=lambda x: int(x))]
                    except Exception:
                        pass
                if isinstance(candidate, (list, tuple)):
                    return [list(map(float, v)) for v in candidate]
        if "error" in resp:
            raise ValueError(f"Embedding failed: {resp['error']}")
        raise ValueError(f"Dict response from embed() did not contain embeddings. Keys: {list(resp.keys())}")

    # 3) If the object has .embeddings or .data attributes
    if hasattr(resp, "embeddings"):
        cand = getattr(resp, "embeddings")
        if isinstance(cand, (list, tuple)):
            return [list(map(float, v)) for v in cand]
    if hasattr(resp, "data"):
        cand = getattr(resp, "data")
        if isinstance(cand, dict) and "embeddings" in cand:
            cand = cand["embeddings"]
        if isinstance(cand, (list, tuple)):
            return [list(map(float, v)) for v in cand]

    # 4) As a last resort parse text repr for 'embeddings=[...]'
    try:
        text = str(resp)
    except Exception:
        text = None

    if text:
        parsed = extract_embeddings_from_text(text)
        if parsed is not None:
            return [list(map(float, v)) for v in parsed]

    preview = (text[:800] if text else "<unprintable response>")
    raise ValueError(
        "Unable to coerce embed() response into list-of-vectors.\n"
        f"Preview: {preview}\n"
        "Make sure the Ollama daemon is running, the model name is correct, and the model supports embeddings."
    )


class VectorDB:
    def __init__(self):
        # load FAISS index and metadata
        try:
            self.index = faiss.read_index(INDEX_PATH)
        except Exception as e:
            raise RuntimeError(
                f"Failed to load FAISS index at '{INDEX_PATH}'. Make sure you created it first.\n"
                f"Original error: {e}"
            )
        try:
            with open(META_PATH, "r", encoding="utf-8") as f:
                self.meta = json.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load metadata at '{META_PATH}': {e}")

    def query(self, query_text: str, k: int = 4):
        """
        Embed the query text robustly, then run a FAISS search and return list of {'score', 'meta'}.
        """
        try:
            raw = embed(model=EMBED_MODEL, input=[query_text])
        except Exception as e:
            raise RuntimeError(
                f"embed() call failed. Ensure Ollama is running and model '{EMBED_MODEL}' is pulled.\n"
                f"Underlying error: {e}"
            )

        # coerce to list-of-vectors
        vectors = coerce_embed_response(raw)

        if len(vectors) == 0:
            raise RuntimeError("embed() returned no vectors.")
        # For a single input we expect a single vector; take first
        vec = np.array(vectors[0], dtype=np.float32).reshape(1, -1)

        # normalize (if index was built with normalized embeddings)
        faiss.normalize_L2(vec)

        # search
        D, I = self.index.search(vec, k)
        results = []
        for score, idx in zip(D[0], I[0]):
            try:
                meta = self.meta[idx]
            except Exception:
                meta = {"id": f"idx:{idx}"}
            results.append({"score": float(score), "meta": meta})
        return results
