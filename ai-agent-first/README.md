# Ai Agent First
There's been some hype around AI Agents since they have been able to accomplish more complex tasks in one shot.

My understanding is:
- RAG - direct information lookup + summarization
- Agents - reasoning, sequencing, and orchestration
  - I can tell an agent to build a frontend with ShadCN and then it can call the ShadCN tools to generate components and then adjust the code.

## Setup Steps
```
# 1) Install (optional but recommended)
pip install ollama loguru

# 2) Run Ollama
ollama serve

# 3) Pull the model
ollama pull llama3.1

# 4) Run the script
python main.py

```

## Implementation Steps
- Prompted ChatGPT #1
  ```
  Write me example Python code for an AI Agent. Tell me about real world examples for AI Agents too.
  ```
- Prompted ChatGPT #2 (main.py)
  ```
  Swap the policy call for an LLM call with Ollama. Pick an appropriate model for this task.
  Add guardrails. Cleanly delineate them separately from other code.
  Add observability. Use whatever is most suitable, standard logging, logguru, or other
  ```
- Prompted ChatGPT #3 (`main_langgraph.py`)
  ```
  update to use LangGraph state orchestration
  ```
- Re-prompt with error in `main_langgraph.py`

## Agent
- see [main.jsonl](main.jsonl)
  - Note JSONL is a JSON object per new line
- An LLM (Ollama llama3.1) is the policy. Each turn it returns a plan in strict JSON:

```
[policy (LLM)] --final--> [final (return answer)]
       |
       '--tool--> [tool exec] --observation--> (back to) [policy]
                         |
                         '--timeout/error--> (observation carries error) -> [policy]
```

Steps
1. **Plan**: Call LLM with system prompt + few-shots + (optional) last observation.
2. **Validate** (guardrails): JSON shape, allowed action/tool, input size, blocklist.
3. **Act**:

   * If `final` → return answer.
   * If `tool` → run tool with timeout, set `observation`.
4. **Iterate**: Continue until `final` or `MAX_STEPS`.

Tools
* `calculator` — safe arithmetic via `math` (sanitized eval).
* `memory` — `remember:/recall:/dump`.
* `todo` — `add:/list/clear`.
  *Add more by defining a function, documenting it, and adding to the allowlist.*

## Agent (LangGraph)
```
[policy] ──(final)──▶ [final]
    │
    └─(tool) ───────▶ [tool] ──▶ (loop back to) [policy]
                         │
                         └─(timeout/err)──▶ [policy]
```

# Notes
It's kind of hard to get the LLM to call the correct tool. I assume lots of people prob just use if statements to detect certain phrases and then use the tool.

I thought AI Agents would be hard to debug, but ChatGPT does a great job with adding log statements. I think if I wrote my own code, I could simply replicate that for my AI Agent.

It's very cool how easy it is to implement an AI Agent nowadays (and build more complicated stuff with LangGraph).