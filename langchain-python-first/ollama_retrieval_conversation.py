"""
https://python.langchain.com/v0.1/docs/get_started/quickstart/#conversation-retrieval-chain
"""

from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import FAISS
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import OllamaEmbeddings, OllamaLLM
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
search_query_prompt = ChatPromptTemplate.from_messages([
    MessagesPlaceholder(variable_name="chat_history"),
    ("user", "{input}"),
    ("user", "Given the above conversation, generate a search query to look up to get information relevant to the conversation")
])
prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer the user's questions based on the below context:\n\n{context}"),
    MessagesPlaceholder(variable_name="chat_history"),
    ("user", "{input}"),
])

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

    # Retriever Chain - generates search query using most recent input + conversation history
    retriever = vector.as_retriever()
    retriever_chain = create_history_aware_retriever(llm, retriever, search_query_prompt)
    """
    # EXAMPLE showing how retriever_chain returns documents about testing in LangSmith
    chat_history = [HumanMessage(content="Can LangSmith help test my LLM applications?"), AIMessage(content="Yes!")]
    documents = retriever_chain.invoke({
        "chat_history": chat_history,
        "input": "Tell me how"
    })
    print("DOCUMENTS")
    print(documents)
    print()
    """
    
    # Retrieval Chain - take incoming question, dynamically select relevant documents, pass documents along with original question back to LLM
    retrieval_chain = create_retrieval_chain(retriever_chain, document_chain)
    
    # execute chain
    chat_history = [HumanMessage(content="Can LangSmith help test my LLM applications?"), AIMessage(content="Yes!")]
    resp = retrieval_chain.invoke({
        "chat_history": chat_history,
        "input": "Tell me how"
    })
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
