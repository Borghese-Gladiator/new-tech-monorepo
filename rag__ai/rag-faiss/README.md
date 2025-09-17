## 🧩 Concepts Used

* **LangChain** — Provides orchestration for building end-to-end RAG pipelines, managing the flow from retrieval to generation.
* **FAISS IVF Indexing** — Vector search with *Inverted File* (IVF) clustering:

  * Partitions embeddings into `nlist` coarse clusters.
  * At query time, probes only `nprobe` clusters.
  * Balances **recall vs latency** for scalable retrieval on large corpora.
* **SentenceTransformers** — Encodes document chunks and queries into dense vector embeddings (L2-normalized for cosine similarity).
* **Document Chunking** — Splits large documents into manageable passages for retrieval.
* **Llama-3B-Instruct** — Local instruction-tuned LLM used for grounded answer generation.
* **Evaluation Suite**:

  * **Cosine Similarity** — Measures semantic alignment between generated answers and references.
  * **Token-level F1** — Precision/recall overlap of tokens between predictions and references.

### Retrieval Modes

* **Dense Retrieval** — Uses FAISS IVF index to quickly find semantically similar chunks.
* **Sparse Retrieval** — Uses TF-IDF (scikit-learn) for exact lexical matches.
* **Hybrid Retrieval** — Combines sparse + dense results:

  * **RRF (Reciprocal Rank Fusion):** Merges ranks by reciprocal weighting.
  * **Weighted Score Fusion:** Normalizes scores and blends them (e.g., 40% sparse, 60% dense).

### Demo & Interfaces

* **Streamlit Web Demo** — Interactive UI to:

  * Enter queries
  * Adjust IVF `nprobe` (recall vs latency)
  * Adjust retrieval `k` and generation params
  * Inspect retrieved chunks and generated answers side by side

# rag-faiss
**Retrieval-Augmented Generation with LangChain, FAISS IVF, and Llama-3B-Instruct**

This is a lightweight framework for experimenting with RAG pipelines.  
It combines:
- **LangChain** for orchestration
- **FAISS IVF indexing** for scalable vector search
- **Llama-3B-Instruct** for generation
- **Evaluation** using cosine similarity and token-level F1-score

---

## 🚀 Features
- Document chunking & embedding with [SentenceTransformers](https://www.sbert.net/).
- IVF-based FAISS index for efficient retrieval.
- Query-time retrieval + response generation using Llama-3B-Instruct.
- Built-in evaluation suite (cosine similarity + token-level F1).

---

## 📦 Setup

### 1. Clone repo
```bash
git clone https://github.com/yourname/vectorrag.git
cd vectorrag
````

### 2. Install dependencies with Poetry

```bash
poetry install
```

### 3. Download or prepare a dataset

Place your `.txt` or `.md` files inside the `corpus/` folder.

## Usage

1. **Prepare**
   `poetry run python 1_build_embeddings.py` → `embeddings.npy`, `docs.jsonl`

2. **Index**
   `poetry run python 2_build_faiss_ivf_index.py --nlist 2048 --metric ip` → `faiss_index_ivf.faiss`, `faiss_ids.npy`

### 🌐 Web Demo (Streamlit)

Run a local UI to search, inspect retrieved chunks, and generate answers with Llama-3B-Instruct.

3. **Demo**
   `poetry run streamlit run 3_streamlit_app.py` → interactively search/generate

* Tune `nprobe` for accuracy vs speed
* Inspect chunks to validate grounding

## Normal Run

3. **Demo**
   - `poetry run 3_rag_query.py`
   - `poetry run 4_evaluate.py`

## Hybrid Retrieval
Here's a drop-in hybrid retrieval script that fuses sparse (TF-IDF) and dense (FAISS IVF) results.
It supports RRF (reciprocal rank fusion) or weighted score fusion, and then runs the same
Llama-3B-Instruct generation as your other scripts.

Ensure previous artifacts exist
```
poetry run python scripts/2_data_prep.py
poetry run python scripts/3_build_faiss_ivf.py --nlist 2048 --metric ip
```

Run hybrid query (RRF fusion)
```
poetry run python scripts/4b_hybrid_query.py --query "How does IVF indexing trade recall for latency?" \
  --fusion rrf --top_k_sparse 100 --top_k_dense 100 --top_k_final 5 --nprobe 64
```

Or weighted score fusion
```
poetry run python scripts/4b_hybrid_query.py --query "Explain FAISS IVF" \
  --fusion weighted --w_sparse 0.4 --w_dense 0.6 --top_k_final 5
```