# scripts/5_evaluate.py
import argparse
import json
import re
import numpy as np
import faiss
import pandas as pd
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
from pathlib import Path

DEFAULT_INDEX = "faiss_index_ivf.faiss"
DEFAULT_IDS = "faiss_ids.npy"
DEFAULT_DOCS = "docs.jsonl"
EMB_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL = "meta-llama/Llama-3.2-3B-Instruct"  # swap if needed

TOKEN_RE = re.compile(r"\w+", re.UNICODE)

def load_jsonl(path: str) -> List[Dict]:
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            data.append(json.loads(line))
    return data

def load_docs(path: str) -> List[Dict]:
    docs = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            docs.append(json.loads(line))
    return docs

def tokenize(text: str) -> List[str]:
    # Lowercase + alphanumeric tokens
    return [t.lower() for t in TOKEN_RE.findall(text)]

def token_f1(pred: str, ref: str) -> float:
    pred_tokens = tokenize(pred)
    ref_tokens = tokenize(ref)
    if not pred_tokens and not ref_tokens:
        return 1.0
    if not pred_tokens or not ref_tokens:
        return 0.0
    # multiset overlap
    from collections import Counter
    pc, rc = Counter(pred_tokens), Counter(ref_tokens)
    overlap = sum(min(pc[t], rc[t]) for t in set(pc) | set(rc))
    precision = overlap / max(1, sum(pc.values()))
    recall = overlap / max(1, sum(rc.values()))
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)

def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    # expects 1D vectors; both already L2-normalized
    return float(np.dot(a, b))

def build_prompt(query: str, retrieved: List[Dict]) -> str:
    context = "\n\n".join(
        [f"[{i+1}] {r['metadata'].get('source','?')}: {r['page_content']}" for i, r in enumerate(retrieved)]
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

def run_retrieval(
    index, ids: np.ndarray, docs: List[Dict], embedder: SentenceTransformer, query: str, top_k: int
) -> List[Dict]:
    qv = embedder.encode([query], normalize_embeddings=True).astype("float32")
    D, I = index.search(qv, top_k)
    I = I[0]
    D = D[0]
    out = []
    for rank, (idx, score) in enumerate(zip(I, D)):
        if idx == -1:
            continue
        doc = docs[int(ids[idx])]
        out.append({"rank": rank + 1, "score": float(score), **doc})
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval_file", default="eval.jsonl",
                    help="JSONL with objects: {\"query\": str, \"reference\": str}")
    ap.add_argument("--index", default=DEFAULT_INDEX)
    ap.add_argument("--ids", default=DEFAULT_IDS)
    ap.add_argument("--docs", default=DEFAULT_DOCS)
    ap.add_argument("--top_k", type=int, default=5)
    ap.add_argument("--nprobe", type=int, default=64)
    ap.add_argument("--max_new_tokens", type=int, default=256)
    ap.add_argument("--temperature", type=float, default=0.2)
    ap.add_argument("--out_csv", default="eval_report.csv")
    args = ap.parse_args()

    # Load artifacts
    index = faiss.read_index(args.index)
    try:
        faiss.ParameterSpace().set_index_parameter(index, "nprobe", int(args.nprobe))
    except Exception:
        pass

    ids = np.load(args.ids)
    docs = load_docs(args.docs)
    embedder = SentenceTransformer(EMB_MODEL)

    # LLM
    tok = AutoTokenizer.from_pretrained(LLM_MODEL)
    model = AutoModelForCausalLM.from_pretrained(
        LLM_MODEL,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto",
    )
    gen = pipeline("text-generation", model=model, tokenizer=tok)

    # Load eval set
    eval_rows = load_jsonl(args.eval_file)

    records = []
    for i, row in enumerate(eval_rows, 1):
        query = row["query"]
        reference = row["reference"]

        # Retrieve chunks
        retrieved = run_retrieval(index, ids, docs, embedder, query, args.top_k)

        # Build prompt + generate
        prompt = build_prompt(query, retrieved)
        out = gen(
            prompt,
            max_new_tokens=args.max_new_tokens,
            do_sample=(args.temperature > 0),
            temperature=args.temperature,
        )[0]["generated_text"]
        if "Answer:" in out:
            out = out.split("Answer:", 1)[-1].strip()
        prediction = out

        # Cosine similarity (embed ref & pred, normalized)
        ref_vec = embedder.encode([reference], normalize_embeddings=True).astype("float32")[0]
        pred_vec = embedder.encode([prediction], normalize_embeddings=True).astype("float32")[0]
        cos = cosine_sim(ref_vec, pred_vec)

        # Token-level F1
        f1 = token_f1(prediction, reference)

        records.append({
            "idx": i,
            "query": query,
            "reference": reference,
            "prediction": prediction,
            "cosine_similarity": cos,
            "token_f1": f1,
            "retrieved_sources": " | ".join([r["metadata"].get("source", "?") for r in retrieved]),
            "retrieval_scores": " | ".join([f"{r['score']:.4f}" for r in retrieved]),
        })

        print(f"[{i}/{len(eval_rows)}] cos={cos:.4f}  f1={f1:.4f}")

    # Save report
    df = pd.DataFrame(records)
    df.to_csv(args.out_csv, index=False)
    print(f"\nSaved per-example report → {args.out_csv}")

    # Aggregates
    print("\nAggregate metrics:")
    print(f"  Cosine similarity (mean): {df['cosine_similarity'].mean():.4f}")
    print(f"  Token F1 (mean):          {df['token_f1'].mean():.4f}")

if __name__ == "__main__":
    main()
