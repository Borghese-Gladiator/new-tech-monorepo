from pathlib import Path

#==================
#  CONSTANTS
#==================
DATA_DIR = Path('data')
MODEL_NAME = "deepseek-r1:1.5b"

#==================
#  LOAD DOCUMENTS
#==================
def load_documents(dir_path: Path):
    documents = []
    for file_path in dir_path.glob('*.txt'):
        with open(file_path, 'r') as file:
            documents.append(file.read())
    return documents

print("Loading Documents")
documents = load_documents(DATA_DIR)
print("\t Done~")

#=========================
#  GENERATE EMBEDDINGS
#=========================
from langchain_huggingface import HuggingFaceEmbeddings
import faiss
import numpy as np


print("Generating Embeddings")
# Initialize the embeddings model
embeddings_model = HuggingFaceEmbeddings()

# Generate embeddings for all documents
document_embeddings = embeddings_model.embed_documents(documents)
document_embeddings = np.array(document_embeddings).astype('float32')

# Create FAISS index
index = faiss.IndexFlatL2(document_embeddings.shape[1])  # L2 distance metric
index.add(document_embeddings)  # Add document embeddings to the index

print("\t Done~")

#=========================
#  RAG
#=========================
class SimpleRetriever:
    def __init__(self, index, embeddings_model):
        self.index = index
        self.embeddings_model = embeddings_model
    
    def retrieve(self, query, k=3):
        query_embedding = self.embeddings_model.embed_query(query)
        distances, indices = self.index.search(np.array([query_embedding]).astype('float32'), k)
        return [documents[i] for i in indices[0]]

retriever = SimpleRetriever(index, embeddings_model)

#=========================
#  MAIN
#=========================
from ollama import chat
from ollama import ChatResponse
from string import Template
import textwrap

# Craft the prompt template using string. Template for better readability
prompt_template = Template("""
Use ONLY the context below.
If unsure, say "I don't know".
Keep answers under 4 sentences.

Context: $context
Question: $question
Answer:
""")

def answer_query(question):
    # Retrieve relevant context from the knowledge base
    context = retriever.retrieve(question)
    
    # Combine retrieved contexts into a single string (if multiple)
    combined_context = "n".join(context)
    
    # Generate an answer using DeepSeek R1 with the combined context
    response: ChatResponse = chat(
        model=MODEL_NAME,
        messages=[{
            'role': 'user',
            'content': prompt_template.substitute(context=combined_context, question=question)
        }]
    )
    
    return response.message.content

if __name__ == "__main__":
    test_queries = [
        "What are the key features of DeepSeek R1?",
        "How does FAISS help in similarity search?",
        "What are Hugging Face embeddings used for?",
        "What is Retrieval-Augmented Generation (RAG)?",
        "Why do pandas have an extra thumb?",
        "How do pandas communicate?",
        "Why are pandas black and white?"
    ]

    for idx, query in enumerate(test_queries):
        answer = answer_query(query)
        print(f"Question {idx + 1}: {query}")
        print(textwrap.indent(f"Answer: {answer}\n", '\t'))
        print()