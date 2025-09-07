"""
Agent: LLM-driven plan→act loop with tool-use via Ollama,
including guardrails and observability.

Setup:
  1) Install Python deps (optional):
       pip install ollama loguru
  2) Start Ollama locally:
       ollama serve
  3) Pull the model:
       ollama pull llama3.1
  4) Run this file.

Why llama3.1?
  - Good reasoning, tool-use prompting works well
  - Fast on consumer GPUs/CPUs in 8B form
  - Available in Ollama with an open, simple API
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Callable, Dict, Any, List, Optional, Tuple
import json
import math
import time
import traceback
import concurrent.futures
import os
from datetime import datetime

# -------------------------------
# OBSERVABILITY (logs + tracing)
# -------------------------------
try:
    from loguru import logger
    LOGURU = True
except Exception:
    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    logger = logging.getLogger("agent")
    LOGURU = False

TRACE_JSONL_PATH = "agent_trace.jsonl"
HUMAN_LOG_PATH = "agent.log"

def _setup_logging():
    """Configure file sinks for both human-readable and JSONL traces."""
    if LOGURU:
        # human-readable log
        logger.add(HUMAN_LOG_PATH, level="INFO", rotation="1 MB", retention=5)
    else:
        # stdlib already configured above; also mirror to a file
        fh = logging.FileHandler(HUMAN_LOG_PATH)
        fh.setLevel(logging.INFO)
        logger.addHandler(fh)

_setup_logging()

def trace_event(event: str, payload: Dict[str, Any]):
    """Append a structured trace row (JSONL)."""
    row = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "event": event,
        "payload": payload,
    }
    with open(TRACE_JSONL_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    if LOGURU:
        logger.bind(event=event).info(payload)
    else:
        logger.info(f"{event}: {payload}")

# -------------------------------
# TOOLS
# -------------------------------
@dataclass
class Tool:
    name: str
    description: str
    fn: Callable[[str, Dict[str, Any]], str]

def calculator_tool(input_text: str, context: Dict[str, Any]) -> str:
    """
    Safe-ish arithmetic only: + - * / ** ( ) and math.<fn>.
    Example: 'sqrt(2)**2 + 13/5'
    """
    allowed_names = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
    allowed_names.update({"__builtins__": {}})
    expr = input_text.strip()
    # very basic guard to avoid sneaky identifiers
    if any(tok in expr for tok in ["__", "import", "open(", "exec", "eval", "os.", "sys."]):
        return "Calculator error: disallowed token."
    try:
        result = eval(expr, allowed_names, {})
        return str(result)
    except Exception as e:
        return f"Calculator error: {e}"

def memory_tool(input_text: str, context: Dict[str, Any]) -> str:
    """
    Save/recall small facts.
      'remember: key=value'
      'recall: key'
      'dump'
    """
    mem = context["memory"].setdefault("facts", {})
    cmd = input_text.strip()
    if cmd.startswith("remember:"):
        payload = cmd.split(":", 1)[1].strip()
        if "=" in payload:
            k, v = payload.split("=", 1)
            mem[k.strip()] = v.strip()
            return f"Remembered {k.strip()}."
        return "Use 'remember: key=value'"
    elif cmd.startswith("recall:"):
        key = cmd.split(":", 1)[1].strip()
        return mem.get(key, f"(no fact for '{key}')")
    elif cmd == "dump":
        return json.dumps(mem, indent=2)
    else:
        return "Usage: 'remember: k=v' | 'recall: k' | 'dump'"

def todo_tool(input_text: str, context: Dict[str, Any]) -> str:
    """
    Simple todos:
      'add: buy milk' | 'list' | 'clear'
    """
    todos: List[str] = context["memory"].setdefault("todos", [])
    cmd = input_text.strip().lower()
    if cmd.startswith("add:"):
        item = input_text.split(":", 1)[1].strip()
        if not item:
            return "Provide an item after 'add:'."
        todos.append(item)
        return f"Added todo: {item}"
    if cmd == "list":
        return "Todos:\n" + "\n".join(f"- {t}" for t in todos) if todos else "No todos."
    if cmd == "clear":
        todos.clear()
        return "Cleared todos."
    return "Usage: 'add: <item>' | 'list' | 'clear'"

TOOLS: Dict[str, Tool] = {
    "calculator": Tool("calculator", "Do arithmetic and math()", calculator_tool),
    "memory":     Tool("memory",     "Remember/recall short facts", memory_tool),
    "todo":       Tool("todo",       "Manage a simple todo list",   todo_tool),
}

# -------------------------------
# GUARDRAILS (clearly delineated)
# -------------------------------
class Guardrails:
    """
    Centralized runtime constraints and validation.
    Modify here without touching core logic.
    """
    # Step & tool limits
    MAX_STEPS = 6
    MAX_TOOL_INPUT_CHARS = 400
    ALLOWED_TOOLS = set(TOOLS.keys())

    # Content safety / blocklist (simple example)
    BLOCKLIST = [
        "rm -rf", "shutdown", "format c:", "powershell -command Stop-Computer",
        "DROP TABLE", "TRUNCATE TABLE",
    ]

    # Tool execution timeouts (seconds)
    TOOL_TIMEOUT_SECS = {
        "calculator": 2,
        "memory": 2,
        "todo": 2,
    }

    # LLM output schema (very small validator)
    @staticmethod
    def validate_plan(plan: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Expected forms:
          {"action": "final", "answer": "<text>", "reason": "<optional>"}
        OR
          {"action": "tool", "tool": "<name>", "input": "<text>", "reason": "<optional>"}
        """
        if not isinstance(plan, dict):
            return False, "Plan must be a JSON object."
        if "action" not in plan:
            return False, "Missing 'action'."
        action = plan["action"]
        if action not in ("final", "tool"):
            return False, "Invalid 'action' value."
        if action == "final":
            if "answer" not in plan or not isinstance(plan["answer"], str):
                return False, "Final plan must include string 'answer'."
        if action == "tool":
            if "tool" not in plan or plan["tool"] not in Guardrails.ALLOWED_TOOLS:
                return False, f"'tool' must be one of {sorted(Guardrails.ALLOWED_TOOLS)}."
            if "input" not in plan or not isinstance(plan["input"], str):
                return False, "Tool plan must include string 'input'."
            if len(plan["input"]) > Guardrails.MAX_TOOL_INPUT_CHARS:
                return False, f"Tool input too long (> {Guardrails.MAX_TOOL_INPUT_CHARS} chars)."
            for bad in Guardrails.BLOCKLIST:
                if bad.lower() in plan["input"].lower():
                    return False, f"Blocked content detected: {bad!r}"
        return True, ""

    @staticmethod
    def with_timeout(tool: Tool, tool_input: str, context: Dict[str, Any]) -> str:
        """Run a tool with a timeout to prevent hangs."""
        timeout = Guardrails.TOOL_TIMEOUT_SECS.get(tool.name, 3)
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(tool.fn, tool_input, context)
            return fut.result(timeout=timeout)

# -------------------------------
# LLM POLICY via OLLAMA
# -------------------------------
# pip install ollama
try:
    from ollama import Client as OllamaClient
except Exception:
    OllamaClient = None

class LLMPolicy:
    """
    Uses Ollama to produce a strict JSON plan.
    Model: 'llama3.1'
    """
    def __init__(self, model: str = "llama3.1", host: str = "http://localhost:11434"):
        if OllamaClient is None:
            raise RuntimeError("Missing 'ollama' package. Install with: pip install ollama")
        self.client = OllamaClient(host=host)
        self.model = model

    def build_system_prompt(self) -> str:
        tool_desc = "\n".join([f"- {t.name}: {t.description}" for t in TOOLS.values()])
        return (
            "You are a tool-using agent. You must respond ONLY with a single JSON object.\n"
            "You have these tools:\n"
            f"{tool_desc}\n\n"
            "Respond with one of two shapes:\n"
            '{"action":"tool","tool":"<one of the tools>","input":"<string>","reason":"<short>"}\n'
            'OR {"action":"final","answer":"<string>","reason":"<short>"}\n'
            "Never include markdown, commentary, or extra text—JSON only.\n"
        )

    def fewshot(self) -> List[Dict[str, str]]:
        return [
            {
                "role": "user",
                "content": "calc: sqrt(2)**2 + 3",
            },
            {
                "role": "assistant",
                "content": json.dumps({"action": "tool", "tool": "calculator", "input": "sqrt(2)**2 + 3", "reason": "User asked to compute."})
            },
            {
                "role": "user",
                "content": "remember: snack=banana",
            },
            {
                "role": "assistant",
                "content": json.dumps({"action": "tool", "tool": "memory", "input": "remember: snack=banana", "reason": "Store a fact."})
            },
            {
                "role": "user",
                "content": "What can you do?",
            },
            {
                "role": "assistant",
                "content": json.dumps({"action": "final", "answer": "I can use calculator/memory/todo tools. Try 'calc: 2+2' or 'todo: add: buy milk'.", "reason": "General answer"})
            },
        ]

    def plan(self, user_goal: str, last_observation: Optional[str]) -> Dict[str, Any]:
        msgs = [{"role": "system", "content": self.build_system_prompt()}]
        msgs.extend(self.fewshot())
        content = user_goal if not last_observation else f"{user_goal}\n(last_observation: {last_observation})"
        msgs.append({"role": "user", "content": content})

        trace_event("llm_request", {"model": self.model, "messages_len": len(msgs)})
        resp = self.client.chat(model=self.model, messages=msgs, options={"temperature": 0.2})
        raw = resp["message"]["content"].strip()
        trace_event("llm_raw_response", {"raw": raw[:500] + ("..." if len(raw) > 500 else "")})

        # ensure it's pure JSON (some models add stray code fences)
        raw = raw.strip().lstrip("`").rstrip("`")
        try:
            plan = json.loads(raw)
        except Exception as e:
            trace_event("llm_parse_error", {"error": str(e), "raw": raw})
            # Fail closed with a safe final response
            return {"action": "final", "answer": "Sorry—I couldn't understand the plan.", "reason": "Invalid JSON"}

        ok, why = Guardrails.validate_plan(plan)
        if not ok:
            trace_event("llm_plan_invalid", {"why": why, "plan": plan})
            return {"action": "final", "answer": "Sorry—my plan failed validation.", "reason": why}
        return plan

# -------------------------------
# AGENT CORE
# -------------------------------
class Agent:
    def __init__(self, tools: Dict[str, Tool], policy: LLMPolicy, max_steps: int = Guardrails.MAX_STEPS):
        self.tools = tools
        self.policy = policy
        self.max_steps = max_steps
        self.memory: Dict[str, Any] = {"facts": {}, "todos": []}

    def run(self, goal: str) -> str:
        observation = None
        for step in range(self.max_steps):
            trace_event("agent_step_begin", {"step": step + 1, "goal": goal, "observation": observation})
            plan = self.policy.plan(goal, observation)
            trace_event("agent_plan", {"step": step + 1, "plan": plan})

            action = plan["action"]
            if action == "final":
                ans = plan.get("answer", "")
                trace_event("agent_final", {"answer": ans})
                return ans

            if action == "tool":
                tool_name = plan["tool"]
                tool = self.tools.get(tool_name)
                if not tool or tool_name not in Guardrails.ALLOWED_TOOLS:
                    msg = f"Unknown or disallowed tool: {tool_name}"
                    trace_event("agent_tool_error", {"error": msg})
                    return msg

                tool_input = plan["input"]
                # Execute tool with timeout + capture exceptions
                try:
                    start = time.time()
                    result = Guardrails.with_timeout(tool, tool_input, {"memory": self.memory})
                    elapsed = round(time.time() - start, 4)
                    observation = result
                    trace_event("agent_tool_result", {"tool": tool_name, "elapsed": elapsed, "result": result[:500]})
                except concurrent.futures.TimeoutError:
                    observation = f"Tool '{tool_name}' timed out."
                    trace_event("agent_tool_timeout", {"tool": tool_name})
                except Exception as e:
                    observation = f"Tool '{tool_name}' failed: {e}"
                    trace_event("agent_tool_exception", {"tool": tool_name, "error": str(e), "trace": traceback.format_exc()})
                # loop continues
            else:
                trace_event("agent_invalid_plan", {"plan": plan})
                return "Invalid plan."

        trace_event("agent_max_steps_reached", {"goal": goal, "last_observation": observation})
        return f"Stopped after {self.max_steps} steps.\nLast observation: {observation or '(none)'}"

# -------------------------------
# DEMO
# -------------------------------
if __name__ == "__main__":
    # Verify environment early
    if OllamaClient is None:
        raise SystemExit("Please install dependencies first: pip install ollama loguru")

    agent = Agent(TOOLS, policy=LLMPolicy(model="llama3.1"))

    print("Example 1 (math):")
    print(agent.run("calc: 13**2 + 7"))

    print("\nExample 2 (todo):")
    print(agent.run("todo: add: buy oat milk"))
    print(agent.run("todo: list"))

    print("\nExample 3 (memory):")
    print(agent.run("remember: favorite_color=green"))
    print(agent.run("recall: favorite_color"))
    print(agent.run("dump"))

    print("\nExample 4 (open):")
    print(agent.run("What can you do?"))
