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
