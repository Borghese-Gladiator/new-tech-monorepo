"""
Here's a drop-in hybrid retrieval script that fuses sparse (TF-IDF) and dense (FAISS IVF) results.
It supports RRF (reciprocal rank fusion) or weighted score fusion, and then runs the same
Llama-3B-Instruct generation as your other scripts.

USAGE
# Ensure previous artifacts exist
poetry run python scripts/2_data_prep.py
poetry run python scripts/3_build_faiss_ivf.py --nlist 2048 --metric ip

# Run hybrid query (RRF fusion)
poetry run python scripts/4b_hybrid_query.py --query "How does IVF indexing trade recall for latency?" \
  --fusion rrf --top_k_sparse 100 --top_k_dense 100 --top_k_final 5 --nprobe 64

# Or weighted score fusion
poetry run python scripts/4b_hybrid_query.py --query "Explain FAISS IVF" \
  --fusion weighted --w_sparse 0.4 --w_dense 0.6 --top_k_final 5
"""

# scripts/4b_hybrid_query.py
"""
Hybrid retrieval (sparse + dense) for VectorRAG:
- Sparse: TF-IDF (scikit-learn) cosine scoring
- Dense: FAISS IVF (inner-product on L2-normalized embeddings)
- Fusion: RRF or weighted score fusion

Artifacts expected (created earlier):
- docs.jsonl
- faiss_index_ivf.faiss
- faiss_ids.npy

On first run, this script caches:
- tfidf_matrix.npz
- tfidf_vectorizer.pkl
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

import faiss
import joblib
import numpy as np
from scipy import sparse as sp
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize as sk_normalize

# -------- Defaults --------
DOCS_PATH = "docs.jsonl"
INDEX_PATH = "faiss_index_ivf.faiss"
IDS_PATH = "faiss_ids.npy"

TFIDF_MTX_PATH = "tfidf_matrix.npz"
TFIDF_VECT_PATH = "tfidf_vectorizer.pkl"

EMB_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL = "meta-llama/Llama-3.2-3B-Instruct"  # change to your preferred instruct model


# -------- IO --------
def load_docs(path: str) -> List[Dict]:
    docs = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            docs.append(json.loads(line))
    return docs


# -------- Sparse (TF-IDF) --------
def build_or_load_tfidf(docs: List[Dict]) -> Tuple[sp.csr_matrix, TfidfVectorizer]:
    if Path(TFIDF_MTX_PATH).exists() and Path(TFIDF_VECT_PATH).exists():
        X = sp.load_npz(TFIDF_MTX_PATH)
        vect: TfidfVectorizer = joblib.load(TFIDF_VECT_PATH)
        return X, vect

    texts = [d["page_content"] for d in docs]
    vect = TfidfVectorizer(
        ngram_range=(1, 2),
        max_df=0.9,
        min_df=2,
        strip_accents="unicode",
        lowercase=True,
    )
    X = vect.fit_transform(texts)  # (N_docs, V)
    # L2-normalize rows so dot = cosine
    X = sk_normalize(X, norm="l2", copy=False)
    sp.save_npz(TFIDF_MTX_PATH, X)
    joblib.dump(vect, TFIDF_VECT_PATH)
    return X, vect


def sparse_search(query: str, X: sp.csr_matrix, vect: TfidfVectorizer, top_k: int) -> List[Tuple[int, float]]:
    q = vect.transform([query])
    q = sk_normalize(q, norm="l2", copy=False)
    # cosine = q * X^T
    sims = (q @ X.T).toarray().ravel()
    if top_k >= len(sims):
        idxs = np.argsort(-sims)
    else:
        idxs = np.argpartition(-sims, top_k)[:top_k]
        idxs = idxs[np.argsort(-sims[idxs])]
    return [(int(i), float(sims[i])) for i in idxs]


# -------- Dense (FAISS IVF) --------
def dense_search(
    query: str,
    index: faiss.Index,
    ids: np.ndarray,
    embedder: SentenceTransformer,
    top_k: int,
) -> List[Tuple[int, float]]:
    qv = embedder.encode([query], normalize_embeddings=True).astype("float32")
    D, I = index.search(qv, top_k)
    I = I[0]
    D = D[0]
    out = []
    for idx, score in zip(I, D):
        if idx == -1:
            continue
        # map back to docs.jsonl row
        out.append((int(ids[idx]), float(score)))
    return out


# -------- Fusion --------
def reciprocal_rank_fusion(
    lists: List[List[Tuple[int, float]]],
    k: int,
    rrf_k: float = 60.0,
) -> List[Tuple[int, float]]:
    """
    lists: list of ranked lists [(doc_id, score), ...] (higher rank = earlier)
    Returns top-k fused by RRF: 1 / (rrf_k + rank)
    """
    agg = {}
    for L in lists:
        for rank, (doc_id, _) in enumerate(L, start=1):
            agg[doc_id] = agg.get(doc_id, 0.0) + 1.0 / (rrf_k + rank)
    items = sorted(agg.items(), key=lambda x: -x[1])[:k]
    return items


def minmax_scale(values: List[float]) -> List[float]:
    if not values:
        return values
    vmin, vmax = min(values), max(values)
    if vmax <= vmin + 1e-12:
        return [0.0 for _ in values]
    return [(v - vmin) / (vmax - vmin) for v in values]


def weighted_score_fusion(
    sparse: List[Tuple[int, float]],
    dense: List[Tuple[int, float]],
    k: int,
    w_sparse: float = 0.4,
    w_dense: float = 0.6,
) -> List[Tuple[int, float]]:
    """
    Normalize scores with min-max within each list and combine linearly.
    """
    s_ids, s_scores = zip(*sparse) if sparse else ([], [])
    d_ids, d_scores = zip(*dense) if dense else ([], [])
    s_norm = dict(zip(s_ids, minmax_scale(list(s_scores))))
    d_norm = dict(zip(d_ids, minmax_scale(list(d_scores))))

    all_ids = set(s_norm) | set(d_norm)
    fused = []
    for did in all_ids:
        score = w_sparse * s_norm.get(did, 0.0) + w_dense * d_norm.get(did, 0.0)
        fused.append((did, score))
    fused.sort(key=lambda x: -x[1])
    return fused[:k]


# -------- Prompting --------
def make_prompt(query: str, retrieved_chunks: List[Dict]) -> str:
    context = "\n\n".join(
        [f"[{i+1}] {c['metadata'].get('source','?')}: {c['page_content']}" for i, c in enumerate(retrieved_chunks)]
    )
    sys_prompt = (
        "You are a helpful assistant. Answer the user's question using ONLY the context chunks. "
        "If the answer is not in the context, say you don't have enough information."
    )
    return (
        f"<<SYS>>\n{sys_prompt}\n<</SYS>>\n\n"
        f"[CONTEXT]\n{context}\n[/CONTEXT]\n\n"
        f"[QUERY]\n{query}\n[/QUERY]\n\n"
        "Answer:"
    )


# -------- Main --------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--docs", default=DOCS_PATH)
    ap.add_argument("--index", default=INDEX_PATH)
    ap.add_argument("--ids", default=IDS_PATH)
    ap.add_argument("--top_k_sparse", type=int, default=50, help="Candidates from TF-IDF before fusion")
    ap.add_argument("--top_k_dense", type=int, default=50, help="Candidates from FAISS before fusion")
    ap.add_argument("--top_k_final", type=int, default=5, help="Final K after fusion → sent to the LLM")
    ap.add_argument("--fusion", choices=["rrf", "weighted"], default="rrf")
    ap.add_argument("--rrf_k", type=float, default=60.0)
    ap.add_argument("--w_sparse", type=float, default=0.4)
    ap.add_argument("--w_dense", type=float, default=0.6)
    ap.add_argument("--nprobe", type=int, default=64, help="FAISS IVF clusters to probe")
    ap.add_argument("--max_new_tokens", type=int, default=256)
    ap.add_argument("--temperature", type=float, default=0.2)
    args = ap.parse_args()

    # Load docs
    docs = load_docs(args.docs)
    N = len(docs)
    if N == 0:
        raise SystemExit("No docs found. Run scripts/2_data_prep.py first.")

    # Sparse artifacts
    X, vect = build_or_load_tfidf(docs)

    # Dense artifacts
    index = faiss.read_index(args.index)
    try:
        faiss.ParameterSpace().set_index_parameter(index, "nprobe", int(args.nprobe))
    except Exception:
        pass
    ids = np.load(args.ids)

    embedder = SentenceTransformer(EMB_MODEL)

    # Retrieve separately
    sparse_hits = sparse_search(args.query, X, vect, top_k=min(args.top_k_sparse, N))
    dense_hits = dense_search(args.query, index, ids, embedder, top_k=min(args.top_k_dense, N))

    # Fuse
    if args.fusion == "rrf":
        fused = reciprocal_rank_fusion(
            [
                [(doc_id, score) for doc_id, score in sparse_hits],
                [(doc_id, score) for doc_id, score in dense_hits],
            ],
            k=min(args.top_k_final, N),
            rrf_k=args.rrf_k,
        )
    else:
        fused = weighted_score_fusion(
            sparse_hits, dense_hits, k=min(args.top_k_final, N), w_sparse=args.w_sparse, w_dense=args.w_dense
        )

    # Materialize fused chunks
    id2doc = {i: d for i, d in enumerate(docs)}
    retrieved = []
    for rank, (doc_id, score) in enumerate(fused, start=1):
        d = id2doc[int(doc_id)]
        retrieved.append({"rank": rank, "score": float(score), **d})

    print(f"[Hybrid Retrieved {len(retrieved)} docs]")
    for r in retrieved:
        print(f"  [{r['rank']}] score={r['score']:.4f} source={r['metadata'].get('source','?')}")

    # LLM
    tok = AutoTokenizer.from_pretrained(LLM_MODEL)
    model = AutoModelForCausalLM.from_pretrained(
        LLM_MODEL,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto",
    )
    gen = pipeline("text-generation", model=model, tokenizer=tok)

    # Prompt + generate
    prompt = make_prompt(args.query, retrieved)
    out = gen(
        prompt,
        max_new_tokens=args.max_new_tokens,
        do_sample=(args.temperature > 0),
        temperature=args.temperature,
    )[0]["generated_text"]

    if "Answer:" in out:
        out = out.split("Answer:", 1)[-1].strip()

    print("\nRAG Response:")
    print(out)


if __name__ == "__main__":
    main()
