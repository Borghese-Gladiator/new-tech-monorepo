# First Langchain (Python)
LangChain is a framework to build language model applications.

LangChain applications create chains, sequences of operations that process input to generate output. This enables simplified code logic where one LLM can be swapped for another. Furthermore, you can use community boilerplate to instantiates integrations like Bedrock, OpenAI, LiteLLM, Sagemaker, llama-python-cpp, vLLM, Ollama, etc. w/o actually knowing those services very well.

## Getting Started
Run Chatbot Locally
- download Ollama from [website](https://ollama.com/)
- download model
  ```
  ollama pull llama3
  ollama run llama3
  ```

Run local langchain example
- install dependencies
  ```
  poetry install
  ```
- `poetry run basic_ollama.py`
  - Give the script a little while to run (~45 seconds). Local models take a while

# Prompt Engineering
Basics
- Prompt templates convert raw user input to better input to the LLM
