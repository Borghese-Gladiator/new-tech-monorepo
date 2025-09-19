Here’s a condensed summary of the article with the **key code snippets preserved** so you can test the implementation yourself.

---

## 🔹 Overview

The article walks through building an **MCP-powered AI agent** that integrates:

* **Gemini** for reasoning
* An **MCP tool server** for structured actions (web search, data analysis, code execution, weather info)
* Asynchronous design, JSON tool schemas, and extensibility

The flow:

1. Install dependencies
2. Define an **MCPToolServer** with async tool handlers
3. Build an **MCPAgent** that wires Gemini to the tool server
4. Run scripted demos and an **interactive loop**

---

## 🔹 Step 1: Install Dependencies

```python
import subprocess, sys

def install_packages():
    packages = [
        'mcp', 'google-generativeai', 'requests',
        'beautifulsoup4', 'matplotlib', 'numpy',
        'websockets', 'pydantic'
    ]
    for package in packages:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Installed {package}")

install_packages()
```

---

## 🔹 Step 2: Imports

```python
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import numpy as np

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent, ImageContent, EmbeddedResource
import mcp.types as types

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

---

## 🔹 Step 3: MCP Tool Server

Defines **web\_search**, **data\_analysis**, **code\_execution**, **weather\_info**.

```python
class MCPToolServer:
    def __init__(self):
        self.tools = {
            "web_search": {...},
            "data_analysis": {...},
            "code_execution": {...},
            "weather_info": {...}
        }

    async def list_tools(self):
        return [types.Tool(**tool) for tool in self.tools.values()]

    async def call_tool(self, name, arguments):
        if name == "web_search":
            return await self._web_search(arguments["query"])
        elif name == "data_analysis":
            return await self._data_analysis(arguments["data_type"], arguments.get("parameters", {}))
        elif name == "code_execution":
            return await self._code_execution(arguments["language"], arguments["task"])
        elif name == "weather_info":
            return await self._weather_info(arguments["location"])
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
```

---

### 🔹 Example Tool Implementations

**Web Search (Wikipedia scrape)**

```python
async def _web_search(self, query: str):
    search_url = f"https://www.wikipedia.org/wiki/Special:Search?search={query.replace(' ', '%20')}"
    response = requests.get(search_url, headers={'User-Agent': 'MCP Agent'}, timeout=10)
    ...
    return [types.TextContent(type="text", text=result)]
```

**Data Analysis (plot + stats)**

```python
async def _data_analysis(self, data_type, parameters):
    x = np.linspace(0, 4*np.pi, 100)
    y = np.sin(x) + np.random.normal(0, 0.1, 100)
    plt.scatter(x, y); plt.show()
    return [types.TextContent(type="text", text="📊 Analysis results...")]
```

**Code Execution (Fibonacci example)**

```python
async def _code_execution(self, language, task):
    if language.lower() == "python" and "fibonacci" in task.lower():
        code = '''def fibonacci(n): ...'''
        exec(code)
        return [types.TextContent(type="text", text=f"✅ Executed Fibonacci code")]
```

**Weather Info (simulated)**

```python
async def _weather_info(self, location: str):
    weather_data = {"temperature": 25, "condition": "Sunny"}
    return [types.TextContent(type="text", text=f"🌤️ Weather for {location}: {weather_data}")]
```

---

## 🔹 Step 4: MCP Agent with Gemini

```python
class MCPAgent:
    def __init__(self, gemini_api_key=None):
        self.gemini_api_key = gemini_api_key or os.environ.get('GEMINI_API_KEY')
        self.mcp_server = MCPToolServer()
        self.conversation_history = []
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            print("✅ MCP Agent initialized with Gemini!")
        else:
            self.model = None

    async def process_request(self, user_input: str) -> str:
        tools = await self.mcp_server.list_tools()
        if not self.model:
            return "🤖 No Gemini, tools available: " + ", ".join([t.name for t in tools])
        ...
```

---

## 🔹 Step 5: Run Demo & Interactive Mode

```python
async def run_mcp_demo():
    agent = MCPAgent()
    queries = [
        "Search for information about machine learning",
        "Create a data visualization with sine wave analysis",
        "What's the weather like in New York?",
        "Explain how artificial intelligence works"
    ]
    for q in queries:
        print(await agent.process_request(q))
    return agent

async def interactive_mcp_mode(agent: MCPAgent):
    while True:
        user_input = input("🗣️ You: ")
        if user_input.lower() == "quit": break
        print(await agent.process_request(user_input))

if __name__ == "__main__":
    agent = asyncio.run(run_mcp_demo())
    asyncio.run(interactive_mcp_mode(agent))
```

---

✅ **End Result**:
You get an **AI agent** where Gemini decides if a tool is needed, invokes the MCP server, and merges the results into responses. You can run the demo or enter interactive mode to try arbitrary prompts.

---

Do you want me to **extract just the runnable “minimum working code”** (single `.py` file) so you can copy-paste and verify, instead of all modular sections?
