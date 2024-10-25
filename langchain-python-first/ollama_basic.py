"""
https://python.langchain.com/v0.1/docs/get_started/quickstart/#llm-chain
"""

from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from utils import log_execution_duration

#==================
#  CONSTANTS
#==================
# LLM Model
MODEL_NAME = "llama3"
llm = OllamaLLM(model=MODEL_NAME)

# Prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a world class technical documentation writer."),
    ("user", "{input}")
])

# Output Parser
output_parser = StrOutputParser()

#==================
#  MAIN
#==================
@log_execution_duration
def main():
    # Chain - takes prompt, passes to LLM, and parses output as string instead of "Message" object
    chain = prompt | llm  | output_parser
    resp: str = chain.invoke({"input": "how can langsmith help with testing?"})

    print("FULL CHAIN RESPONSE")
    print(resp)
    print()

if __name__ == "__main__":
    main()
