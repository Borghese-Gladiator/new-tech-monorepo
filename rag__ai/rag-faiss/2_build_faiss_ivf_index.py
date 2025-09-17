# scripts/3_build_faiss_ivf.py
import argparse, json, numpy as np, faiss, os, sys

def load_docs(path="docs.jsonl"):
    docs = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            docs.append(json.loads(line))
    return docs

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--emb", default="embeddings.npy")
    p.add_argument("--docs", default="docs.jsonl")
    p.add_argument("--out_index", default="faiss_index_ivf.faiss")
    p.add_argument("--out_ids", default="faiss_ids.npy")
    p.add_argument("--nlist", type=int, default=2048)
    p.add_argument("--metric", choices=["ip", "l2"], default="ip",
                   help="Use 'ip' if embeddings are L2-normalized (cosine).")
    args = p.parse_args()

    X = np.load(args.emb).astype("float32")
    N, d = X.shape
    if N == 0:
        print("No embeddings found. Run 2_data_prep.py first.", file=sys.stderr)
        sys.exit(1)

    metric = faiss.METRIC_INNER_PRODUCT if args.metric == "ip" else faiss.METRIC_L2
    index_str = f"IVF{args.nlist},Flat"
    quantizer = faiss.IndexFlatIP(d) if metric == faiss.METRIC_INNER_PRODUCT else faiss.IndexFlatL2(d)
    index = faiss.IndexIVFFlat(quantizer, d, args.nlist, metric)

    # IVF requires training
    print(f"[build] training IVF (nlist={args.nlist}) on {N} vectors, dim={d} …")
    index.train(X)
    print("[build] adding vectors …")
    index.add(X)

    # Persist
    faiss.write_index(index, args.out_index)
    np.save(args.out_ids, np.arange(N, dtype=np.int64))
    print(f"[build] wrote index → {args.out_index} and ids → {args.out_ids}")
    print("[build] done.")

if __name__ == "__main__":
    main()
