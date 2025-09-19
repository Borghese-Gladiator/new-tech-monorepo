# mcp_agent_demo.py
import subprocess
import sys
import os
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional

import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import numpy as np

# Install dependencies if missing
def install_packages():
    packages = [
        "mcp",
        "google-generativeai",
        "requests",
        "beautifulsoup4",
        "matplotlib",
        "numpy",
        "websockets",
        "pydantic"
    ]
    for package in packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ Installed {package}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}")

# install_packages()  # uncomment if you need auto-install

import google.generativeai as genai
import mcp.types as types

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# -------------------------------
# MCP Tool Server
# -------------------------------
class MCPToolServer:
    def __init__(self):
        self.tools = {
            "web_search": {
                "name": "web_search",
                "description": "Search the web for information",
                "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
            },
            "data_analysis": {
                "name": "data_analysis",
                "description": "Analyze data and create visualizations",
                "inputSchema": {
                    "type": "object",
                    "properties": {"data_type": {"type": "string"}, "parameters": {"type": "object"}},
                    "required": ["data_type"],
                },
            },
            "code_execution": {
                "name": "code_execution",
                "description": "Execute or generate code",
                "inputSchema": {
                    "type": "object",
                    "properties": {"language": {"type": "string"}, "task": {"type": "string"}},
                    "required": ["language", "task"],
                },
            },
            "weather_info": {
                "name": "weather_info",
                "description": "Get weather information (simulated)",
                "inputSchema": {
                    "type": "object",
                    "properties": {"location": {"type": "string"}},
                    "required": ["location"],
                },
            },
        }

    async def list_tools(self):
        return [types.Tool(**tool) for tool in self.tools.values()]

    async def call_tool(self, name: str, arguments: Dict[str, Any]):
        if name == "web_search":
            return await self._web_search(arguments.get("query", ""))
        elif name == "data_analysis":
            return await self._data_analysis(arguments.get("data_type", ""), arguments.get("parameters", {}))
        elif name == "code_execution":
            return await self._code_execution(arguments.get("language", ""), arguments.get("task", ""))
        elif name == "weather_info":
            return await self._weather_info(arguments.get("location", ""))
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

    async def _web_search(self, query: str):
        try:
            url = f"https://www.wikipedia.org/wiki/Special:Search?search={query.replace(' ', '%20')}"
            resp = requests.get(url, headers={"User-Agent": "MCP Agent"}, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, "html.parser")
                paragraphs = soup.find_all("p")[:3]
                content = "\n".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
                result = f"🔍 Results for '{query}':\n\n{content[:500]}..."
            else:
                result = f"❌ Search failed: status {resp.status_code}"
        except Exception as e:
            result = f"❌ Web search error: {e}"
        return [types.TextContent(type="text", text=result)]

    async def _data_analysis(self, data_type: str, params: Dict):
        try:
            if "sine" in data_type.lower():
                x = np.linspace(0, 4 * np.pi, 100)
                y = np.sin(x) + np.random.normal(0, 0.1, 100)
                title = "Sine Wave Analysis"
            else:
                x = np.random.normal(0, 1, 100)
                y = np.random.normal(0, 1, 100)
                title = "Random Data Analysis"

            plt.scatter(x, y, alpha=0.6)
            plt.title(title)
            plt.show()

            stats = {
                "mean_x": np.mean(x),
                "mean_y": np.mean(y),
                "std_x": np.std(x),
                "std_y": np.std(y),
                "correlation": np.corrcoef(x, y)[0, 1],
            }

            result = f"📊 {title}:\nMeanX={stats['mean_x']:.2f}, MeanY={stats['mean_y']:.2f}, Corr={stats['correlation']:.2f}"
        except Exception as e:
            result = f"❌ Data analysis error: {e}"
        return [types.TextContent(type="text", text=result)]

    async def _code_execution(self, language: str, task: str):
        try:
            if language.lower() == "python" and "fibonacci" in task.lower():
                code = """def fibonacci(n):
    if n <= 0: return []
    elif n == 1: return [0]
    elif n == 2: return [0,1]
    fib = [0,1]
    for i in range(2,n):
        fib.append(fib[i-1] + fib[i-2])
    return fib

print("Fibonacci(10):", fibonacci(10))"""
                exec(code)
                result = f"💻 Code for '{task}':\n{code}\n\n✅ Executed!"
            else:
                result = f"💻 Template for {language}: // {task}"
        except Exception as e:
            result = f"❌ Code exec error: {e}"
        return [types.TextContent(type="text", text=result)]

    async def _weather_info(self, location: str):
        weather_data = {
            "temperature": np.random.randint(15, 30),
            "condition": np.random.choice(["Sunny", "Cloudy", "Rainy", "Partly Cloudy"]),
        }
        result = f"🌤️ Weather for {location}: {weather_data['temperature']}°C, {weather_data['condition']} (simulated)"
        return [types.TextContent(type="text", text=result)]


# -------------------------------
# MCP Agent
# -------------------------------
class MCPAgent:
    def __init__(self, gemini_api_key: Optional[str] = None):
        self.gemini_api_key = gemini_api_key or os.environ.get("GEMINI_API_KEY")
        self.mcp_server = MCPToolServer()
        self.conversation_history = []
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
            print("✅ MCP Agent initialized with Gemini!")
        else:
            self.model = None
            print("⚠️ No Gemini API key, limited functionality.")

    async def process_request(self, user_input: str) -> str:
        tools = await self.mcp_server.list_tools()
        if not self.model:
            return "🤖 (No Gemini) Available tools: " + ", ".join([t.name for t in tools])
        try:
            # naive: always try to use web_search for demo
            if "weather" in user_input.lower():
                tool_name, args = "weather_info", {"location": "New York"}
            elif "sine" in user_input.lower():
                tool_name, args = "data_analysis", {"data_type": "sine"}
            elif "fibonacci" in user_input.lower():
                tool_name, args = "code_execution", {"language": "python", "task": "fibonacci sequence"}
            else:
                tool_name, args = "web_search", {"query": user_input}

            tool_results = await self.mcp_server.call_tool(tool_name, args)
            tool_output = "\n".join([c.text for c in tool_results])
            return f"🤖 Gemini + MCP used {tool_name}:\n{tool_output}"
        except Exception as e:
            return f"❌ MCPAgent error: {e}"


# -------------------------------
# Demo Runner
# -------------------------------
async def run_mcp_demo():
    agent = MCPAgent()
    queries = [
        "Search for information about machine learning",
        "Create a data visualization with sine wave analysis",
        "What's the weather like in New York?",
        "Generate fibonacci sequence in python",
    ]
    for q in queries:
        print("\n📝", q)
        resp = await agent.process_request(q)
        print(resp)
    return agent


if __name__ == "__main__":
    print("🎯 Running MCP Agent Demo")
    asyncio.run(run_mcp_demo())
