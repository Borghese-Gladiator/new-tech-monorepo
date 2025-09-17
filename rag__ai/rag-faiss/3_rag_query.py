# scripts/4_rag_query.py
import argparse
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
from typing import List, Dict

DEFAULT_INDEX = "faiss_index_ivf.faiss"
DEFAULT_IDS = "faiss_ids.npy"
DEFAULT_DOCS = "docs.jsonl"
EMB_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL = "meta-llama/Llama-3.2-3B-Instruct"  # change if you prefer another instruct model

def load_docs(path: str) -> List[Dict]:
    docs = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            docs.append(json.loads(line))
    return docs

def make_prompt(query: str, retrieved: List[Dict]) -> str:
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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True, help="User question.")
    ap.add_argument("--index", default=DEFAULT_INDEX)
    ap.add_argument("--ids", default=DEFAULT_IDS)
    ap.add_argument("--docs", default=DEFAULT_DOCS)
    ap.add_argument("--top_k", type=int, default=3)
    ap.add_argument("--nprobe", type=int, default=64, help="Clusters to probe in IVF.")
    ap.add_argument("--max_new_tokens", type=int, default=256)
    ap.add_argument("--temperature", type=float, default=0.2)
    args = ap.parse_args()

    # Load FAISS IVF + artifacts
    index = faiss.read_index(args.index)
    # Set IVF nprobe if supported
    try:
        faiss.ParameterSpace().set_index_parameter(index, "nprobe", int(args.nprobe))
    except Exception:
        pass

    ids = np.load(args.ids)
    docs = load_docs(args.docs)

    # Embedder (normalized => cosine equivalence with inner product)
    embedder = SentenceTransformer(EMB_MODEL)
    qv = embedder.encode([args.query], normalize_embeddings=True).astype("float32")

    # Search
    D, I = index.search(qv, args.top_k)
    I = I[0]
    D = D[0]

    retrieved = []
    for rank, (idx, score) in enumerate(zip(I, D)):
        if idx == -1:
            continue
        doc = docs[int(ids[idx])]
        retrieved.append({"rank": rank + 1, "score": float(score), **doc})

    print(f"[Retrieved {len(retrieved)} docs]")
    for r in retrieved:
        src = r["metadata"].get("source", "?")
        print(f"  [{r['rank']}] score={r['score']:.4f}  source={src}")

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

    # Heuristic: show the segment after "Answer:" if present
    if "Answer:" in out:
        out = out.split("Answer:", 1)[-1].strip()

    print("\nRAG Response:")
    print(out)

if __name__ == "__main__":
    main()
