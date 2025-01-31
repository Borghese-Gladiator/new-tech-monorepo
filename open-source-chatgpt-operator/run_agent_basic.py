"""
Ollama - QWEN
https://github.com/browser-use/browser-use/blob/main/examples/models/qwen.py

Ollama - qwen instruct
https://github.com/browser-use/browser-use/blob/main/examples/models/ollama.py

(neither work....)

QWEN
```
(open-source-chatgpt-operator-py3.11) PS C:\Users\Timot\Documents\GitHub\new-tech-monorepo\open-source-chatgpt-operator> python .\run_agent_basic.py
INFO     [browser_use] BrowserUse logging setup complete with level info
INFO     [root] Anonymized telemetry enabled. See https://docs.browser-use.com/development/telemetry for more information.
INFO     [agent] 🚀 Starting task: 1. Go to https://www.reddit.com/r/LocalLLaMA2. Search for 'browser use' in the search bar3. Click search4. Call done
INFO     [agent] 📍 Step 1
ERROR    [agent] ❌ Result failed 1/3 times:
 Could not parse response.
INFO     [agent] 📍 Step 1
ERROR    [agent] ❌ Result failed 2/3 times:
 Could not parse response.
INFO     [agent] 📍 Step 1
INFO     [agent] 🤷 Eval: Unknown - No previous actions to evaluate.
INFO     [agent] 🧠 Memory:
INFO     [agent] 🎯 Next goal: Start browser and navigate to Reddit page
INFO     [agent] 🛠️  Action 1/1: {}
INFO     [agent] 📍 Step 2
ERROR    [agent] ❌ Result failed 1/3 times:
 Could not parse response.
INFO     [agent] 📍 Step 2
INFO     [agent] 🤷 Eval: Unknown - No previous actions to evaluate.
INFO     [agent] 🧠 Memory:
INFO     [agent] 🎯 Next goal: Navigate to the specified Reddit page and search for 'browser use'.
INFO     [agent] 🛠️  Action 1/1: {"go_to_url":{"url":"https://www.reddit.com/r/LocalLLaMA"}}
INFO     [controller] 🔗  Navigated to https://www.reddit.com/r/LocalLLaMA
INFO     [agent] 📍 Step 3
INFO     [agent] 🤷 Eval: Unknown - No previous actions to evaluate.
INFO     [agent] 🧠 Memory:
INFO     [agent] 🎯 Next goal: Search for 'browser use' and click the search button.
INFO     [agent] 🛠️  Action 1/1: {"input_text":{"index":2,"text":"browser use"}}
INFO     [controller] ⌨️  Input "browser use" into index 2
INFO     [agent] 📍 Step 4
INFO     [agent] 👍 Eval: Successfully navigated to the specified Reddit page and input 'browser use' in the search bar. Now, clicking the search button.
INFO     [agent] 🧠 Memory: Navigated to https://www.reddit.com/r/LocalLLaMA and entered 'browser use' in the search bar. The next action is to click the search button.
INFO     [agent] 🎯 Next goal: Click the search button to perform the search
INFO     [agent] 🛠️  Action 1/1: {"click_element":{"index":8}}
INFO     [controller] 🖱️  Clicked button with index 8:
INFO     [agent] 📍 Step 5
INFO     [agent] 👍 Eval: Successfully navigated to the specified Reddit page and input 'browser use' in the search bar. Now, clicking the search button.
INFO     [agent] 🧠 Memory: Navigated to https://www.reddit.com/r/LocalLLaMA and entered 'browser use' in the search bar. The next action is to click the search button.
INFO     [agent] 🎯 Next goal: Click on a relevant post related to 'browser use'.
INFO     [agent] 🛠️  Action 1/1: {"click_element":{"index":8}}
INFO     [controller] 🖱️  Clicked button with index 8:
INFO     [agent] 📍 Step 6
INFO     [agent] 👍 Eval: Successfully navigated to the specified Reddit page and performed a search. The next action is to scroll down to view more results.
INFO     [agent] 🧠 Memory: Navigated to https://www.reddit.com/r/LocalLLaMA/search/?q=browser+use, entered 'browser use' in the search bar, and clicked the search button.
INFO     [agent] 🎯 Next goal: Scroll down and interact with relevant posts related to 'browser use'. If a specific post is found, click on it.
INFO     [agent] 🛠️  Action 1/1: {"scroll_down":{"amount":null}}
INFO     [controller] 🔍  Scrolled down the page by one page
INFO     [agent] 📍 Step 7
INFO     [agent] 🤷 Eval: Scrolled down the page and viewed more search results related to 'browser use' on Reddit. The next step is to identify a relevant post, click on it, and then call done if the task is complete.
INFO     [agent] 🧠 Memory: Successfully navigated to https://www.reddit.com/r/LocalLLaMA/search/?q=browser+use and performed a search. Viewed more results by scrolling down. If a specific post related to 'browser use' with browser interaction is found, click on it to read its content.
INFO     [agent] 🎯 Next goal: Scroll down the page or extract content to find a relevant post for further analysis.
INFO     [agent] 🛠️  Action 1/1: {"scroll_down":{"amount":null}}
INFO     [controller] 🔍  Scrolled down the page by one page
INFO     [agent] 📍 Step 8
INFO     [agent] 👍 Eval: Successfully navigated to the specified Reddit page and performed a search. The next step is to find and click on a relevant post related to 'browser use' for further analysis.
INFO     [agent] 🧠 Memory: Navigated to https://www.reddit.com/r/LocalLLaMA/search/?q=browser+use, entered 'browser use' in the search bar, clicked the search button, and scrolled down. Identified a relevant post titled 'Browser Use' and will click on it.
INFO     [agent] 🎯 Next goal: Click on the identified relevant post related to 'browser use'.
INFO     [agent] 🛠️  Action 1/1: {"scroll_to_text":{"text":"Browser Use"}}
INFO     [controller] 🔍  Scrolled to text: Browser Use
INFO     [agent] 📍 Step 9
INFO     [agent] 👍 Eval: Successfully navigated to the specified Reddit page and performed a search. The next step is to find and click on a relevant post related to 'browser use' for further analysis.
INFO     [agent] 🧠 Memory: Navigated to https://www.reddit.com/r/LocalLLaMA/search/?q=browser+use, entered 'browser use' in the search bar, clicked the search button, and scrolled down. Identified a relevant post titled 'Browser Use' and will click on it to read its content.
INFO     [agent] 🎯 Next goal: Click on the identified relevant post related to 'browser use'.
INFO     [agent] 🛠️  Action 1/1: {"click_element":{"index":7}}
INFO     [controller] 🖱️  Clicked button with index 7:
INFO     [agent] 📍 Step 10
INFO     [agent] 🤷 Eval: Clicked on a relevant post related to 'browser use' and need to read its content. The next goal is to click the first comment or proceed with reading the post's text.
INFO     [agent] 🧠 Memory: Navigated to https://www.reddit.com/r/LocalLLaMA/search/?q=browser+use, performed a search for 'browser use', clicked on a relevant post titled 'Browser Use', and now need to interact with its content. The goal is to ensure the interaction with a comment or reading the post's text.
INFO     [agent] 🎯 Next goal: Read the first comment or click to view more of the post.
INFO     [agent] 🛠️  Action 1/1: {"click_element":{"index":7}}
INFO     [controller] 🖱️  Clicked button with index 7:
INFO     [agent] 📍 Step 11
INFO     [agent] 🤷 Eval: Clicked on a relevant post related to 'browser use' and need to read its content. The next goal is to input text into the username or password field if needed, but since no such fields are visible, we will proceed with reading the post's text.
INFO     [agent] 🧠 Memory: Navigated to https://www.reddit.com/r/LocalLLaMA/search/?q=browser+use, performed a search for 'browser use', clicked on a relevant post titled 'Browser Use', and now need to interact with its content. The goal is to ensure the interaction with a comment or reading the post's text.
INFO     [agent] 🎯 Next goal: Read the first comment or proceed with further analysis.
INFO     [agent] 🛠️  Action 1/1: {"input_text":{"index":5,"text":"browser use"}}
INFO     [controller] ⌨️  Input "browser use" into index 5
INFO     [agent] 📍 Step 12
INFO     [agent] 🤷 Eval: Clicked on a relevant post related to 'browser use' and need to read its content. The next step is to scroll down the page if more comments are present and extract or read the relevant text.
INFO     [agent] 🧠 Memory: Navigated to https://www.reddit.com/r/LocalLLaMA/search/?q=browser+use, performed a search for 'browser use', clicked on a relevant post titled 'Browser Use', and now need to interact with its content. The goal is to ensure the interaction with a comment or reading the post's text.
INFO     [agent] 🎯 Next goal: Scroll down if more comments are present and extract or read the relevant text.
INFO     [agent] 🛠️  Action 1/1: {"scroll_down":{"amount":null}}
INFO     [controller] 🔍  Scrolled down the page by one page
INFO     [agent] 📍 Step 13
INFO     [agent] 📍 Step 13
ERROR    [agent] ❌ Result failed 1/3 times:
 Browser closed: no valid pages available
INFO     [agent] 📍 Step 13
ERROR    [agent] ❌ Result failed 2/3 times:
 Browser closed: no valid pages available
INFO     [agent] 📍 Step 13
ERROR    [agent] ❌ Result failed 3/3 times:
 Browser closed: no valid pages available
ERROR    [agent] ❌ Stopping due to 3 consecutive failures
INFO     [agent] Created GIF at agent_history.gif
```

DeepSeek-R1
```
INFO     [agent] 🚀 Starting task: Compare the price of gpt-4o and DeepSeek-V3
INFO     [agent] 📍 Step 1
ERROR    [agent] ❌ Result failed 1/3 times:

INFO     [agent] 📍 Step 1
ERROR    [agent] ❌ Result failed 2/3 times:

INFO     [agent] 📍 Step 1
ERROR    [agent] ❌ Result failed 3/3 times:

ERROR    [agent] ❌ Stopping due to 3 consecutive failures
INFO     [agent] Created GIF at agent_history.gif
```

Llama3
```
INFO     [browser_use] BrowserUse logging setup complete with level info
INFO     [root] Anonymized telemetry enabled. See https://docs.browser-use.com/development/telemetry for more information.
INFO     [agent] 🚀 Starting task: Search for a 'browser use' post on the r/LocalLLaMA subreddit and open it.
INFO     [agent] 📍 Step 1
ERROR    [agent] ❌ Result failed 1/3 times:
 registry.ollama.ai/library/llama3:latest does not support tools (status code: 400)
INFO     [agent] 📍 Step 1
ERROR    [agent] ❌ Result failed 2/3 times:
 registry.ollama.ai/library/llama3:latest does not support tools (status code: 400)
INFO     [agent] 📍 Step 1
ERROR    [agent] ❌ Result failed 3/3 times:
```
"""
import asyncio
import os

from langchain_ollama import ChatOllama

from browser_use import Agent


async def run_search():
	agent = Agent(
		task=(
			'1. Go to https://www.reddit.com/r/LocalLLaMA'
			"2. Search for 'browser use' in the search bar"
			'3. Click search'
			'4. Call done'
		),
		llm=ChatOllama(
			# model='qwen2.5:32b-instruct-q4_K_M',
			# model='qwen2.5:14b',
			model='qwen2.5:latest',
			num_ctx=128000,
		),
		max_actions_per_step=1,
	)

	await agent.run()


if __name__ == '__main__':
	asyncio.run(run_search())