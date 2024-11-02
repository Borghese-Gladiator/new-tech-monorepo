"""
- Semantic Text Splitting - split text into semantically coherent chunks
- Fuzzy Deduplication - remove duplicate texts based on similarity threshold
- Embedding Text - build embeddings
"""
import os
import glob
from uuid import uuid4
import numpy as np
import chardet
from typing import Iterable
from pprint import pprint

import faiss
from langchain_core.documents import Document
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from wordllama import WordLlama


#====================================
#   CONSTANTS
#====================================
wl = WordLlama.load()
PATH_INPUT_DIR = "climate_change_texts"
PATH_VECTOR_STORE = "document_index"

embeddings = OllamaEmbeddings(
    model="llama3"
)

#====================================
#   UTILS
#====================================
def load_text_files(folder) -> Iterable[tuple[str, str]]:
    for file_path in glob.glob(f"{folder}/*.txt"):
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            encoding = chardet.detect(raw_data)['encoding']
            try:
                text = raw_data.decode(encoding) if encoding else None
                if text is not None:
                    title = os.path.basename(file_path)
                    yield title, text  # Yield only if decoding was successful
                else:
                    print(f"Encoding detection failed for {file_path}")
            except UnicodeDecodeError:
                print(f"Decoding failed for {file_path} with encoding {encoding}")


#======================================================
#   MAIN - save documents to vector_datastore
#======================================================

def seed_vector_store():

    documents_list = []

    for title, text in load_text_files(PATH_INPUT_DIR):
        print(title.upper())
        
        # Semantic Text Split - split text into semantically coherent chunks of similar sizes
        documents = wl.split(
            text,
            target_size=1536,  # 1536 chars is a good number for 512 token width models.
            window_size=3,
            poly_order=2,
            savgol_window=3,
        )
        pprint(documents[0:1])
        
        # Fuzzy Deduplication - remove duplicate texts based on similarity threshold
        documents_deduplicated = wl.deduplicate(documents, return_indices=False, threshold=0.5)
        print("Deduplicated documents:")
        pprint(documents_deduplicated)

        # Embedding Text - use pre-trained embeddings to convert text into vectors
        # embeddings_array = np.array(wl.embed(documents_deduplicated), dtype="float32")
        
        # FAISS - prepare documents for storage
        faiss_documents = [Document(page_content=doc, metadata={"title": title}) for doc in documents_deduplicated]
        documents_list.extend(faiss_documents)

        # FAISS - save documents to docstore
        # docstore.add({doc.metadata["title"]: doc for doc in faiss_documents})

    vector_store = FAISS.from_documents(
        documents_list,
        embeddings
    )
    vector_store.save_local(PATH_VECTOR_STORE)
    return vector_store

if not os.path.exists(PATH_VECTOR_STORE):
    vector_store = seed_vector_store()
    print("Documents saved to vector_datastore.")
else:
    vector_store = FAISS.load_local(
        PATH_VECTOR_STORE, embeddings, allow_dangerous_deserialization=True
    )
    print("Documents already saved to vector_datastore.")

#======================================================
#   QUERY - Verify documents saved in vector_datastore
#======================================================
print()
print("Top Retrieved Documents:")
results = vector_store.similarity_search(
    "What are the effects of climate change on biodiversity?",
    k=2,
)
for res in results:
    print(f"* {res.page_content} [{res.metadata}]")
    print()
