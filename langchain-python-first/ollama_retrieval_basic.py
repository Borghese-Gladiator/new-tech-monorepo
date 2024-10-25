"""
https://python.langchain.com/v0.1/docs/get_started/quickstart/#retrieval-chain
"""

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from utils import log_execution_duration

#==================
#  CONSTANTS
#==================
# LLM Model
MODEL_NAME = "llama3"
llm = OllamaLLM(model=MODEL_NAME)
embeddings = OllamaEmbeddings(model=MODEL_NAME)

# Prompt
prompt = ChatPromptTemplate.from_template("""Answer the following question based only on the provided context:

<context>
{context}
</context>

Question: {input}""")

#==================
#  SETUP
#==================

# load online data
loader = WebBaseLoader("https://docs.smith.langchain.com/user_guide")  # requires "beautifulsoup4"
docs = loader.load()

# store documents in Vector Store
text_splitter = RecursiveCharacterTextSplitter()
documents = text_splitter.split_documents(docs)
vector = FAISS.from_documents(documents, embeddings)

#==================
#  MAIN
#==================
@log_execution_duration
def main():
    # Document Chain - pass list of Documents to LLM
    document_chain = create_stuff_documents_chain(llm, prompt)
    """
    # EXAMPLE passing in documents directly to document_chain
    from langchain_core.documents import Document
    document_chain.invoke({
        "input": "how can langsmith help with testing?",
        "context": [Document(page_content="langsmith can let you visualize test results")]
    })
    """

    # Retrieval Chain - take incoming question, dynamically select relevant documents, pass documents along with original question back to LLM
    retriever = vector.as_retriever()
    retrieval_chain = create_retrieval_chain(retriever, document_chain)

    # execute chain
    resp: dict = retrieval_chain.invoke({"input": "how can langsmith help with testing?"})
    print("ANSWER")
    print(resp["answer"])
    print()

    print("FULL CHAIN RESPONSE")
    print(resp)
    print()
    """
    Example Output:
        "input": "how can langsmith help with testing?",
        "context": [
            Document(metadata={}, description="", language="en")
        ],
        "answer": "langsmith can let you visualize test results",
    """

if __name__ == "__main__":
    main()
