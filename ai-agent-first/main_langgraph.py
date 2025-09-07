"""
LangGraph Agent: LLM-policy + tool-use with guardrails & observability.

Setup
  pip install langgraph pydantic ollama loguru
  ollama serve
  ollama pull llama3.1
  python agent_langgraph.py
"""

from __future__ import annotations
from typing import TypedDict, Dict, Any, Optional, List, Tuple, Callable
from dataclasses import dataclass
from datetime import datetime
import concurrent.futures
import traceback
import json
import math
import time
import os

# ================
# OBSERVABILITY
# ================
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
    if LOGURU:
        logger.add(HUMAN_LOG_PATH, level="INFO", rotation="1 MB", retention=5)
    else:
        fh = logging.FileHandler(HUMAN_LOG_PATH)
        fh.setLevel(logging.INFO)
        logger.addHandler(fh)

_setup_logging()

def trace_event(event: str, payload: Dict[str, Any]):
    row = {"ts": datetime.utcnow().isoformat() + "Z", "event": event, "payload": payload}
    with open(TRACE_JSONL_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    if LOGURU:
        logger.bind(event=event).info(payload)
    else:
        logger.info(f"{event}: {payload}")

# ================
# TOOLS
# ================
@dataclass
class Tool:
    name: str
    description: str
    fn: Callable[[str, Dict[str, Any]], str]

def calculator_tool(inp: str, ctx: Dict[str, Any]) -> str:
    allowed_names = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
    allowed_names.update({"__builtins__": {}})
    expr = inp.strip()
    if any(tok in expr for tok in ["__", "import", "open(", "exec", "eval", "os.", "sys."]):
        return "Calculator error: disallowed token."
    try:
        return str(eval(expr, allowed_names, {}))
    except Exception as e:
        return f"Calculator error: {e}"

def memory_tool(inp: str, ctx: Dict[str, Any]) -> str:
    mem = ctx["memory"].setdefault("facts", {})
    cmd = inp.strip()
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
    return "Usage: 'remember: k=v' | 'recall: k' | 'dump'"

def todo_tool(inp: str, ctx: Dict[str, Any]) -> str:
    todos: List[str] = ctx["memory"].setdefault("todos", [])
    cmd = inp.strip().lower()
    if cmd.startswith("add:"):
        item = inp.split(":", 1)[1].strip()
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

# ================
# GUARDRAILS
# ================
class Guardrails:
    MAX_STEPS = 6
    MAX_TOOL_INPUT_CHARS = 400
    ALLOWED_TOOLS = set(TOOLS.keys())
    BLOCKLIST = ["rm -rf", "shutdown", "format c:", "DROP TABLE", "TRUNCATE TABLE"]
    TOOL_TIMEOUT_SECS = {"calculator": 2, "memory": 2, "todo": 2}

    @staticmethod
    def validate_plan(plan: Dict[str, Any]) -> Tuple[bool, str]:
        if not isinstance(plan, dict):
            return False, "Plan must be an object."
        if "action" not in plan:
            return False, "Missing 'action'."
        if plan["action"] not in ("final", "tool"):
            return False, "Invalid 'action'."
        if plan["action"] == "final":
            if not isinstance(plan.get("answer"), str):
                return False, "Final requires string 'answer'."
        if plan["action"] == "tool":
            tool = plan.get("tool")
            tool_input = plan.get("input")
            if tool not in Guardrails.ALLOWED_TOOLS:
                return False, f"Tool must be one of {sorted(Guardrails.ALLOWED_TOOLS)}."
            if not isinstance(tool_input, str):
                return False, "Tool plan requires string 'input'."
            if len(tool_input) > Guardrails.MAX_TOOL_INPUT_CHARS:
                return False, "Tool input too long."
            for bad in Guardrails.BLOCKLIST:
                if bad.lower() in tool_input.lower():
                    return False, f"Blocked content: {bad!r}"
        return True, ""

    @staticmethod
    def with_timeout(tool: Tool, tool_input: str, ctx: Dict[str, Any]) -> str:
        timeout = Guardrails.TOOL_TIMEOUT_SECS.get(tool.name, 3)
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(tool.fn, tool_input, ctx)
            return fut.result(timeout=timeout)

# ================
# LLM POLICY (Ollama)
# ================
try:
    from ollama import Client as OllamaClient
except Exception:
    OllamaClient = None

class LLMPolicy:
    def __init__(self, model: str = "llama3.1", host: str = "http://localhost:11434"):
        if OllamaClient is None:
            raise RuntimeError("Install 'ollama' (pip install ollama)")
        self.client = OllamaClient(host=host)
        self.model = model

    def system_prompt(self) -> str:
        tool_desc = "\n".join([f"- {t.name}: {t.description}" for t in TOOLS.values()])
        
        return (
            "You are a tool-using agent. Respond with EXACTLY one JSON object.\n"
            "Tools:\n" + tool_desc + "\n\n"
            "Schemas:\n"
            '{"action":"tool","tool":"<tool>","input":"<string>","reason":"<short>"}\n'
            'OR {"action":"final","answer":"<string>","reason":"<short>"}\n'
            "Rules:\n"
            "- If the last observation indicates success or directly answers the user (e.g., todo added, list printed, value computed, fact recalled), respond with a FINAL answer. Do NOT call the same tool twice with the same input.\n"
            "- JSON only. No extra text.\n"
        )

    def fewshot(self) -> List[Dict[str, str]]:
        return [
            {"role": "user", "content": "calc: sqrt(2)**2 + 3"},
            {"role": "assistant", "content": json.dumps({"action":"tool","tool":"calculator","input":"sqrt(2)**2 + 3","reason":"Compute."})},
            {"role": "user", "content": "remember: snack=banana"},
            {"role": "assistant", "content": json.dumps({"action":"tool","tool":"memory","input":"remember: snack=banana","reason":"Store fact."})},
            {"role": "user", "content": "What can you do?"},
            {"role": "assistant", "content": json.dumps({"action":"final","answer":"I can use calculator/memory/todo tools.","reason":"General answer"})},
        ]

    def plan(self, goal: str, last_observation: Optional[str]) -> Dict[str, Any]:
        msgs = [{"role": "system", "content": self.system_prompt()}]
        msgs.extend(self.fewshot())
        msgs.append({"role": "user", "content": goal if not last_observation else f"{goal}\n(last_observation: {last_observation})"})

        trace_event("llm_request", {"model": self.model, "messages_len": len(msgs)})
        resp = self.client.chat(model=self.model, messages=msgs, options={"temperature": 0.2})
        raw = resp["message"]["content"].strip().strip("`")
        trace_event("llm_raw_response", {"raw": raw[:500] + ("..." if len(raw) > 500 else "")})

        try:
            plan = json.loads(raw)
        except Exception as e:
            trace_event("llm_parse_error", {"error": str(e), "raw": raw})
            return {"action": "final", "answer": "Sorry—I couldn't understand the plan.", "reason": "Invalid JSON"}
        ok, why = Guardrails.validate_plan(plan)
        if not ok:
            trace_event("llm_plan_invalid", {"why": why, "plan": plan})
            return {"action": "final", "answer": "Sorry—my plan failed validation.", "reason": why}
        return plan

# ================
# LANGGRAPH STATE
# ================
from langgraph.graph import StateGraph, END

class AgentState(TypedDict, total=False):
    goal: str
    step: int
    plan: Dict[str, Any]
    observation: Optional[str]
    done: bool
    answer: Optional[str]
    memory: Dict[str, Any]  # long-lived, mutated by tools

# ================
# NODES
# ================
policy = LLMPolicy(model="llama3.1")

def policy_node(state: AgentState) -> AgentState:
    step = state.get("step", 0) + 1
    if step > Guardrails.MAX_STEPS:
        msg = f"Stopped after {Guardrails.MAX_STEPS} steps. Last observation: {state.get('observation') or '(none)'}"
        trace_event("agent_max_steps", {"goal": state["goal"], "last_observation": state.get("observation")})
        # Force a final plan so the router takes the final edge
        return {
            "step": step,
            "done": True,
            "answer": msg,
            "plan": {"action": "final", "answer": msg, "reason": "max_steps"}
        }

    plan = policy.plan(state["goal"], state.get("observation"))
    trace_event("agent_plan", {"step": step, "plan": plan})

    # --- cycle breaker: if same tool+input repeats, finalize with last observation
    if plan.get("action") == "tool":
        current_call = (plan["tool"], plan.get("input", ""))
        last_call = state.get("last_tool_call")
        if last_call == current_call:
            obs = state.get("observation") or "Done."
            final = {"action": "final", "answer": obs, "reason": "repeat_tool_call"}
            return {"step": step, "plan": final, "done": True, "answer": obs}
        # remember last tool call for next step
        return {"step": step, "plan": plan, "last_tool_call": current_call}

    return {"step": step, "plan": plan}

def tool_node(state: AgentState) -> AgentState:
    plan = state["plan"]
    tool_name = plan["tool"]
    tool = TOOLS.get(tool_name)
    if not tool or tool_name not in Guardrails.ALLOWED_TOOLS:
        msg = f"Unknown or disallowed tool: {tool_name}"
        trace_event("agent_tool_error", {"error": msg})
        return {"observation": msg}

    tool_input = plan["input"]
    try:
        start = time.time()
        result = Guardrails.with_timeout(tool, tool_input, {"memory": state.setdefault("memory", {"facts": {}, "todos": []})})
        elapsed = round(time.time() - start, 4)
        trace_event("agent_tool_result", {"tool": tool_name, "elapsed": elapsed, "result": result[:500]})
        return {"observation": result}
    except concurrent.futures.TimeoutError:
        trace_event("agent_tool_timeout", {"tool": tool_name})
        return {"observation": f"Tool '{tool_name}' timed out."}
    except Exception as e:
        trace_event("agent_tool_exception", {"tool": tool_name, "error": str(e), "trace": traceback.format_exc()})
        return {"observation": f"Tool '{tool_name}' failed: {e}"}

def final_node(state: AgentState) -> AgentState:
    answer = state["plan"].get("answer", "")
    trace_event("agent_final", {"answer": answer})
    return {"done": True, "answer": answer}

# ================
# ROUTER (edges)
# ================
def route_from_policy(state: AgentState) -> str:
    if state.get("done"):
        return "to_final"
    plan = state.get("plan", {})
    if plan.get("action") == "final":
        return "to_final"
    if plan.get("action") == "tool":
        return "to_tool"
    return "to_final"  # fail-closed

# ================
# BUILD GRAPH
# ================
def build_graph():
    sg = StateGraph(AgentState)
    sg.add_node("policy", policy_node)
    sg.add_node("tool", tool_node)
    sg.add_node("final", final_node)

    sg.set_entry_point("policy")
    sg.add_conditional_edges("policy", route_from_policy, {
        "to_final": "final",
        "to_tool": "tool",
    })
    # After tool, loop back to policy
    sg.add_edge("tool", "policy")
    # Final ends
    sg.add_edge("final", END)
    return sg.compile()

GRAPH = build_graph()

# ================
# PUBLIC RUN API
# ================
def run_agent(goal: str) -> str:
    state: AgentState = {"goal": goal, "step": 0, "memory": {"facts": {}, "todos": []}}
    trace_event("agent_start", {"goal": goal})
    # Run to completion; bump recursion_limit in case the model needs a few hops
    result = GRAPH.invoke(state, config={"recursion_limit": 50})
    return result.get("answer", "(no answer)")

# ================
# DEMO
# ================
if __name__ == "__main__":
    if OllamaClient is None:
        raise SystemExit("Please install dependencies first: pip install langgraph pydantic ollama loguru")

    print("Example 1 (math):")
    print(run_agent("calc: 13**2 + 7"))

    print("\nExample 2 (todo):")
    print(run_agent("todo: add: buy oat milk"))
    print(run_agent("todo: list"))

    print("\nExample 3 (memory):")
    print(run_agent("remember: favorite_color=green"))
    print(run_agent("recall: favorite_color"))
    print(run_agent("dump"))

    print("\nExample 4 (open):")
    print(run_agent("What can you do?"))
