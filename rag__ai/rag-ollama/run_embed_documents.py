# run_embed_documents.py (updated, robust extractor)
import os
import json
import ast
import re
import numpy as np
import faiss
from tqdm import tqdm
from typing import List, Any

# Import your Ollama client. Adjust if your import path differs.
from ollama import embed  # if your client differs, update this import

DOC_DIR = "sample_docs"
INDEX_PATH = "index.faiss"
META_PATH = "index_meta.json"
EMBED_MODEL = "mxbai-embed-large"  # change to the model you pulled


def load_docs(doc_dir: str) -> List[dict]:
    docs = []
    for fname in os.listdir(doc_dir):
        path = os.path.join(doc_dir, fname)
        if os.path.isfile(path) and path.endswith((".txt", ".md")):
            with open(path, "r", encoding="utf-8") as f:
                docs.append({"id": fname, "text": f.read()})
    return docs


def normalize_embeddings_array(arr: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return arr / norms


def extract_embeddings_from_text(text: str):
    """
    Find the substring that starts with 'embeddings=' and contains a Python-list literal,
    then parse it with ast.literal_eval.
    This handles stringified SDK objects like:
      "model='mxbai-embed-large' ... embeddings=[[0.03, ...], [...]] ..."
    """
    key = "embeddings"
    idx = text.find(key + "=")
    if idx == -1:
        return None

    # Move to char after 'embeddings='
    i = idx + len(key) + 1

    # Skip whitespace
    while i < len(text) and text[i].isspace():
        i += 1

    # Expect '[' beginning of list
    if i >= len(text) or text[i] != "[":
        return None

    # Find matching closing bracket for the top-level list
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
                end = i + 1  # include closing bracket
                break
        i += 1

    if end is None:
        # couldn't find balanced bracket (maybe truncated preview)
        return None

    candidate = text[start:end]

    # candidate should be a Python list literal; use ast.literal_eval safely
    try:
        parsed = ast.literal_eval(candidate)
        return parsed
    except Exception:
        return None


def coerce_embed_response(resp: Any) -> List[List[float]]:
    """
    Convert the raw response from ollama.embed(...) into a list-of-vectors.
    Handles:
      - native list-of-lists
      - dict with 'embeddings' or 'data'
      - object with attribute .embeddings
      - stringified object containing 'embeddings=[...]'
    """
    # 1) If it's already a list-of-lists
    if isinstance(resp, (list, tuple)):
        if len(resp) == 0:
            raise ValueError("Embedding response is empty list.")
        # If first element is numeric, treat as single vector
        first = resp[0]
        if isinstance(first, (int, float)):
            return [list(map(float, resp))]
        # Otherwise assume list-of-vectors
        return [list(map(float, v)) for v in resp]

    # 2) If it's a dict-like object
    if isinstance(resp, dict):
        # common wrapper keys
        for key in ("embeddings", "data", "vectors", "results"):
            if key in resp:
                candidate = resp[key]
                # sometimes data: {"embeddings": [...]}
                if isinstance(candidate, dict) and "embeddings" in candidate:
                    candidate = candidate["embeddings"]
                # if candidate is dict of index->vector, convert to list
                if isinstance(candidate, dict):
                    try:
                        candidate = [candidate[k] for k in sorted(candidate.keys(), key=lambda x: int(x))]
                    except Exception:
                        pass
                if isinstance(candidate, (list, tuple)):
                    return [list(map(float, v)) for v in candidate]
        # if there's an 'error' field
        if "error" in resp:
            raise ValueError(f"Embedding failed: {resp['error']}")
        # fallback
        raise ValueError(f"Dict response did not contain embeddings. Keys: {list(resp.keys())}")

    # 3) If object has attribute .embeddings or .data
    if hasattr(resp, "embeddings"):
        candidate = getattr(resp, "embeddings")
        if isinstance(candidate, (list, tuple)):
            return [list(map(float, v)) for v in candidate]
    if hasattr(resp, "data"):
        candidate = getattr(resp, "data")
        # maybe data.embeddings
        if isinstance(candidate, dict) and "embeddings" in candidate:
            candidate = candidate["embeddings"]
        if isinstance(candidate, (list, tuple)):
            return [list(map(float, v)) for v in candidate]

    # 4) As a last resort, parse the string representation for 'embeddings=[...]'
    try:
        text = str(resp)
    except Exception:
        text = None

    if text:
        parsed = extract_embeddings_from_text(text)
        if parsed is not None:
            # parsed should be list-of-lists
            return [list(map(float, v)) for v in parsed]

    # If we get here, we couldn't coerce
    preview = str(resp)[:800] if text is None else text[:800]
    raise ValueError(
        "Unable to coerce embedding response into list-of-vectors.\n"
        f"Preview: {preview}\n"
        "If this is an SDK object, ensure it contains an 'embeddings' attribute or try printing the full repr."
    )


def main():
    print("Loading documents...")
    docs = load_docs(DOC_DIR)
    if not docs:
        print("No docs found in", DOC_DIR)
        return

    texts = [d["text"] for d in docs]
    print(f"Found {len(texts)} documents. Generating embeddings...")

    try:
        resp = embed(model=EMBED_MODEL, input=texts)
    except Exception as e:
        raise RuntimeError(
            "Ollama embed call failed. Ensure the Ollama daemon is running and you pulled the model.\n"
            "Example: `ollama pull mxbai-embed-large` and `ollama server`.\n"
            f"Underlying error: {e}"
        )

    # Debug preview
    try:
        preview = str(resp)[:1000]
    except Exception:
        preview = "<unprintable response>"
    print("DEBUG: raw embed response preview:", preview)

    vectors = coerce_embed_response(resp)
    if len(vectors) != len(texts):
        raise ValueError(f"Number of embeddings ({len(vectors)}) != number of documents ({len(texts)}).")

    xb = np.array(vectors, dtype=np.float32)
    print("Embeddings shape:", xb.shape)

    xb = normalize_embeddings_array(xb)

    dim = xb.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(xb)
    faiss.write_index(index, INDEX_PATH)
    print(f"✅ Wrote FAISS index to {INDEX_PATH} with {index.ntotal} vectors")

    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)
    print(f"✅ Wrote metadata to {META_PATH}")


if __name__ == "__main__":
    main()
