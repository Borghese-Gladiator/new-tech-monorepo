> https://realpython.com/llamaindex-examples/

Notes
- **LlamaIndex** lets you load your data and documents, create and persist searchable indexes, and query an LLM using your data as context.
- llama-index is a core starter bundle of packages containing the following:
  - llama-index-core
  - llama-index-llms-openai
  - llama-index-embeddings-openai
  - llama-index-readers-file

# LlamaIndex + Ollama RAG Example

This project demonstrates how to use **LlamaIndex** with a **local Ollama LLM** to build a small retrieval-augmented generation (RAG) pipeline using local models. You’ll:

* Load documents from disk
* Create and **persist a vector index**
* Query the index with a local LLM served by **Ollama**

*Works fully offline once your Ollama models are installed.* ([Real Python][1])

---

## 🛠 Prerequisites

✔ Python 3.10+
✔ Ollama installed and running locally
✔ Local models pulled in Ollama (e.g., `llama3.1:latest`) ([LlamaIndex][2])

---

## 📦 Bootstrap Commands

### 1) Create & activate a Python virtual environment

#### **macOS / Linux (Zsh):**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### **Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

---

### 2) Install Python dependencies

```bash
python -m pip install --upgrade pip
python -m pip install llama-index llama-index-llms-ollama llama-index-embeddings-ollama
```

> These install the LlamaIndex core + local embedding & LLM integrations for Ollama. ([PyPI][3])

---

### 3) Start Ollama & pull a local model

#### **Run Ollama daemon**

```bash
ollama serve
```

#### **Download (pull) a model**

```bash
ollama pull llama3.1:latest
```

> Replace `llama3.1:latest` with any supported Ollama model you prefer. ([LlamaIndex][2])

---

### 4) Add sample data

We’ll index a text file (`pep8.rst`) similar to the RealPython example: ([Real Python][1])

```bash
mkdir -p data
curl -L https://raw.githubusercontent.com/python/peps/main/peps/pep-0008.rst -o data/pep8.rst
```

---

## 🧠 Synchronous Index + Query Script

Create `single_query_ollama.py`:

```bash
cat > single_query_ollama.py <<'PY'
from pathlib import Path

from llama_index.core import (
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "data" / "pep8.rst"
PERSIST_DIR = BASE_DIR / "storage"

def get_index():
    if PERSIST_DIR.exists():
        storage_context = StorageContext.from_defaults(persist_dir=str(PERSIST_DIR))
        index = load_index_from_storage(storage_context)
        print("Loaded index from storage…")
    else:
        reader = SimpleDirectoryReader(input_files=[str(DATA_FILE)])
        documents = reader.load_data()
        embed_model = OllamaEmbedding(model_name="embeddinggemma")
        index = VectorStoreIndex.from_documents(documents, embed_model=embed_model)
        index.storage_context.persist(persist_dir=str(PERSIST_DIR))
        print("Created & persisted index…")
    return index

def main():
    index = get_index()
    llm = Ollama(model="llama3.1:latest", request_timeout=120.0)
    query_engine = index.as_query_engine(llm=llm)
    resp = query_engine.query("What is this document about?")
    print(resp)

if __name__ == "__main__":
    main()
PY
```

> This script persists your index and then queries it with a local LLM via Ollama embeddings & LLM. ([PyPI][3])

---

## 🚀 Run the scripts

#### **macOS / zsh**

```bash
python single_query_ollama.py
```

#### **Windows PowerShell**

```powershell
python single_query_ollama.py
```

You should see a local model response summarizing `pep8.rst`.

---

## 🌀 Async Queries (Optional)

Create `async_query_ollama.py`:

```bash
cat > async_query_ollama.py <<'PY'
import asyncio
from pathlib import Path

from llama_index.core import (
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "data" / "pep8.rst"
PERSIST_DIR = BASE_DIR / "storage"

def get_index():
    if PERSIST_DIR.exists():
        storage_context = StorageContext.from_defaults(persist_dir=str(PERSIST_DIR))
        return load_index_from_storage(storage_context)
    reader = SimpleDirectoryReader(input_files=[str(DATA_FILE)])
    docs = reader.load_data()
    embed_model = OllamaEmbedding(model_name="embeddinggemma")
    index = VectorStoreIndex.from_documents(docs, embed_model=embed_model)
    index.storage_context.persist(persist_dir=str(PERSIST_DIR))
    return index

async def main():
    index = get_index()
    llm = Ollama(model="llama3.1:latest", request_timeout=120.0)
    query_engine = index.as_query_engine(llm=llm)

    queries = [
        "What is this text about?",
        "Summarize the styling recommendations.",
    ]
    tasks = [query_engine.aquery(q) for q in queries]
    results = await asyncio.gather(*tasks)
    for q, r in zip(queries, results):
        print(f"\n{q}\n→ {r}\n")

if __name__ == "__main__":
    asyncio.run(main())
PY
```

Run with:

```bash
python async_query_ollama.py
```

---

## 🗂 How It Works

### 📄 Document loading & indexing

You read your docs with `SimpleDirectoryReader` and build a vector index **with local embeddings** from Ollama. ([LlamaIndex][4])

### 💾 Persistence

The first run creates a `storage/` directory. Future runs reuse the index without re-computing embeddings. ([Real Python][1])

### 🤖 Querying

You pass the index and LLM into a **query engine** and either call `.query()` (sync) or `.aquery()` (async). ([Real Python][1])

---

## 🧠 Tips

* To pull more Ollama models (e.g., larger ones), use:

  ```bash
  ollama pull <model_name>:latest
  ```
* Use `embeddinggemma` for embeddings; you can switch to a different Ollama embedding model. ([LlamaIndex][4])

## 🧪 Next Steps

1. Index more than one document.
2. Experiment with other local models (e.g., larger LLaMA variants).
3. Try different indexing types (Tree, List, etc.).


[1]: https://realpython.com/llamaindex-examples/?utm_source=chatgpt.com "LlamaIndex in Python: A RAG Guide With Examples"
[2]: https://developers.llamaindex.ai/python/examples/llm/ollama/?utm_source=chatgpt.com "Ollama LLM | LlamaIndex Python Documentation"
[3]: https://pypi.org/project/llama-index-llms-ollama/?utm_source=chatgpt.com "llama-index-llms-ollama · PyPI"
[4]: https://developers.llamaindex.ai/python/examples/embeddings/ollama_embedding/?utm_source=chatgpt.com "Ollama Embeddings | LlamaIndex Python Documentation"
