# 2_data_prep.py
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from sentence_transformers import SentenceTransformer
import numpy as np
import json

DATA_DIR = Path("corpus")
EMB_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# 2.1 Load your raw texts (replace with your loader of choice)
raw_docs = []
for p in DATA_DIR.glob("**/*.txt"):
    raw_docs.append((p.name, p.read_text(encoding="utf-8", errors="ignore")))

# 2.2 Chunk
splitter = RecursiveCharacterTextSplitter(
    chunk_size=800, chunk_overlap=120, length_function=len
)
docs: list[Document] = []
for name, text in raw_docs:
    for chunk in splitter.split_text(text):
        docs.append(Document(page_content=chunk, metadata={"source": name}))

# 2.3 Embed chunks
emb = SentenceTransformer(EMB_MODEL)
X = emb.encode([d.page_content for d in docs], normalize_embeddings=True)  # cosine-ready

# 2.4 Persist lightweight artifacts (so later scripts can load fast)
np.save("embeddings.npy", X.astype("float32"))
with open("docs.jsonl", "w", encoding="utf-8") as f:
    for d in docs:
        f.write(json.dumps({"page_content": d.page_content, "metadata": d.metadata}) + "\n")
print(f"Saved {len(docs)} chunks, shape={X.shape}")
