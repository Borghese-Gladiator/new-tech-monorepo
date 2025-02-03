# RAG with DeepSeek
RAG (Retrieval Augmented Generation) retrieves relevant information from a knowledge base and uses it to generate accurate and contextually relevant responese to user queries. In general, RAG systems supplement chatbots with accurate info.

## Setup
```
#==============
#  OLLAMA
#==============
ollama --version
ollama run deepseek-r1:1.5b

#==============
#  POETRY
#==============
poetry init
poetry add faiss-cpu langchain_huggingface
python main.py
```

# Total Steps
[Tutorial](https://www.marktechpost.com/2025/01/27/building-a-retrieval-augmented-generation-rag-system-with-deepseek-r1-a-step-by-step-guide/) and [Tutoral Code](https://colab.research.google.com/drive/1CDpc5L4B1BXZ6U3gjkXZOte5nnrsCmRw?authuser=1#scrollTo=HAIYG3kr0V6x) (not working by default)
- package change
  - `poetry remove huggingface-hub`
  - `poetry add langchain_huggingface`
  - mistake: `poetry add langchain langchain-community sentence-transformers` (langchain has split each into smaller packages for easier downloading)
- code change
  - update from `embeddings_model.embed(doc)` -> `embeddings_model.embed_documents(documents)`
  - update from `self.embeddings_model.embed(query)` -> `query_embedding = self.embeddings_model.embed_query(query)`
- code change
  - tutorial code reflects way old version of langchain `OllamaLLM` (though the snippet is `llm = Ollama(model="deepseek-r1:1.5b")`)
  - followed [docs](https://pypi.org/project/ollama/) for `ollama` package
    - `from ollama import chat`
- generated documents using ChatGPT in `data`

<details>
<summary>Console Output (success!)</summary>

```
```
</details>