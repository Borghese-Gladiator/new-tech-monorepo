# scripts/streamlit_app.py
import json, numpy as np, faiss, torch, streamlit as st
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

EMB_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL = "meta-llama/Llama-3.2-3B-Instruct"  # swap if you prefer another 3B instruct model

INDEX_PATH = "faiss_index_ivf.faiss"
IDS_PATH = "faiss_ids.npy"
DOCS_PATH = "docs.jsonl"

@st.cache_resource
def load_index_and_data():
    index = faiss.read_index(INDEX_PATH)
    ids = np.load(IDS_PATH)
    docs = []
    with open(DOCS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            docs.append(json.loads(line))
    return index, ids, docs

@st.cache_resource
def load_embedder():
    emb = SentenceTransformer(EMB_MODEL)
    return emb

@st.cache_resource
def load_llm():
    tok = AutoTokenizer.from_pretrained(LLM_MODEL)
    model = AutoModelForCausalLM.from_pretrained(
        LLM_MODEL,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto",
    )
    gen = pipeline("text-generation", model=model, tokenizer=tok)
    return gen

def make_prompt(query, retrieved_chunks):
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

st.set_page_config(page_title="VectorRAG Demo", layout="wide")
st.title("VectorRAG — IVF RAG Demo")
st.caption("LangChain (optional), FAISS IVF, Llama-3B-Instruct")

with st.sidebar:
    st.header("Search Settings")
    nprobe = st.slider("nprobe (clusters to probe)", min_value=1, max_value=512, value=64, step=1)
    top_k = st.slider("top-k retrieved", min_value=1, max_value=20, value=5, step=1)
    st.header("Generation Settings")
    max_new_tokens = st.slider("max_new_tokens", 32, 1024, 256, 32)
    temperature = st.slider("temperature", 0.0, 1.5, 0.2, 0.05)

query = st.text_input("Ask a question about your corpus", value="What is FAISS IVF indexing?", max_chars=500)

col1, col2 = st.columns([1, 1])
with col1:
    run = st.button("Retrieve + Generate", type="primary")

if run and query.strip():
    # Load resources
    index, ids, docs = load_index_and_data()
    emb = load_embedder()
    gen = load_llm()

    # Set IVF nprobe at runtime
    try:
        faiss.ParameterSpace().set_index_parameter(index, "nprobe", int(nprobe))
    except Exception:
        pass  # older FAISS versions: some indexes require direct attribute assignment

    # Embed query (normalize => cosine via inner product)
    qv = emb.encode([query], normalize_embeddings=True).astype("float32")

    # Search
    D, I = index.search(qv, top_k)  # inner product distances ~ cosine similarity
    I = I[0]
    D = D[0]

    retrieved = []
    for rank, (idx, score) in enumerate(zip(I, D)):
        if idx == -1:  # happens if fewer results available
            continue
        doc = docs[int(ids[idx])]
        retrieved.append({"rank": rank+1, "score": float(score), **doc})

    with col1:
        st.subheader("Retrieved Chunks")
        for r in retrieved:
            with st.expander(f"[{r['rank']}] {r['metadata'].get('source','?')} — score={r['score']:.4f}"):
                st.write(r["page_content"])

    # Build prompt and generate
    prompt = make_prompt(query, retrieved)
    outputs = gen(prompt, max_new_tokens=max_new_tokens, do_sample=(temperature > 0), temperature=temperature)
    answer = outputs[0]["generated_text"].split("Answer:", 1)[-1].strip()

    with col2:
        st.subheader("Answer")
        st.write(answer)
