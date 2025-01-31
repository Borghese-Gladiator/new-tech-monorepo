"""
NOT WORKING as of 2025-01-31
"""

import asyncio

from langchain_ollama import OllamaLLM
from browser_use import Agent, Browser, BrowserConfig
from browser_use.browser.context import BrowserContext, BrowserContextConfig
from dotenv import load_dotenv


load_dotenv()

#==================
#  CONSTANTS
#==================
# LLM Model
MODEL_NAME = "llama3"  # "deepseek-r1:1.5b"
llm = OllamaLLM(model=MODEL_NAME)

# Browser Configuration
context_config = BrowserContextConfig(
    # allowed_domains=['reddit.com'],
    wait_for_network_idle_page_load_time=5.0,
)
config = BrowserConfig(
    # chrome_instance_path="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",  # uncomment to use local
    new_context_config=context_config,
)
browser = Browser(config=config)

# PROMPT
PRICE_PROMPT = "Compare the price of gpt-4o and DeepSeek-V3"

## not working
REDDIT_PROMPT = "Go to Reddit, search for 'browser-use', click on the first post and return the first comment."

#==================
#  MAIN
#==================
async def main():
    agent = Agent(
        browser=browser,
        task=PRICE_PROMPT,
        llm=OllamaLLM(model=MODEL_NAME),
    )
    result = await agent.run()
    print(result)

asyncio.run(main())
