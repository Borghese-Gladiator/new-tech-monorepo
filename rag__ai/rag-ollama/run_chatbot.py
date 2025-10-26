# run_chatbot.py
"""
RAG chat with Ollama streaming thinking trace and basic tool-call handling.

Behavior:
- Retrieve top-k docs from VectorDB and include as CONTEXT.
- Start a streaming ollama.chat(...) with think=True, stream=True.
- Print thinking chunks as they arrive.
- If the model emits tool_calls, execute them, append tool results to messages,
  then re-invoke a new streaming chat so the model can continue (consumes tool outputs).
- Print final assistant content at the end.

Notes:
- This is a simple synchronous tool executor. For complex tool flows (parallel tools,
  multi-step tool interactions), you'd expand the agent loop.
- Update MODEL and EMBED_MODEL names if needed.
"""

from ollama import chat
from vector_db import VectorDB
from tools import get_time, simple_calc  # example functions you already defined
import time
import json

MODEL = "qwen3"
EMBED_MODEL = "mxbai-embed-large"  # only used in vector_db, shown for reference

# Map function names (as the model will call them) to python callables
# Make sure the function names here match the function names the model will use.
AVAILABLE_TOOLS = {
    "get_time": get_time,
    "simple_calc": simple_calc,
}


def make_context_snippet(retrieved):
    parts = []
    for r in retrieved:
        meta = r.get("meta", {})
        text = meta.get("text") or meta.get("snippet") or meta.get("content") or ""
        parts.append(f"Source: {meta.get('id','unknown')}\n{text[:800]}")
    return "\n\n".join(parts)


def execute_tool_call(tc):
    """
    Execute a single tool-call object coming from the model.
    Expects tc to have .function.name and .function.arguments (sdk ToolCall shape).
    Returns a string result.
    """
    # Defensive access because SDK tool-call shapes can vary
    try:
        func_name = tc.function.name
    except Exception:
        # fallback: try dict-like access
        func_name = getattr(tc.function, "name", None) or tc["function"]["name"]

    args = {}
    try:
        args = tc.function.arguments or {}
    except Exception:
        args = getattr(tc.function, "arguments", None) or {}

    fn = AVAILABLE_TOOLS.get(func_name)
    if not fn:
        return f"Unknown tool requested: {func_name}"

    # call the tool (simple sync call)
    try:
        if isinstance(args, dict):
            result = fn(**args)
        else:
            # if args are positional represented as list/tuple
            if isinstance(args, (list, tuple)):
                result = fn(*args)
            else:
                result = fn(args)
    except Exception as e:
        result = f"Tool {func_name} raised exception: {e}"

    # coerce to string for insertion into the conversation
    try:
        return json.dumps(result) if not isinstance(result, str) else result
    except Exception:
        return str(result)


def start_rag_stream(user_query: str):
    db = VectorDB()
    retrieved = db.query(user_query, k=3)
    context = make_context_snippet(retrieved)

    system_msg = {
        "role": "system",
        "content": (
            "You are a helpful assistant. Use the CONTEXT when relevant. "
            "If you need to call tools, call them as functions. Emit internal reasoning as 'thinking' chunks."
        ),
    }

    user_msg = {
        "role": "user",
        "content": f"CONTEXT:\n{context}\n\nQUESTION: {user_query}"
    }

    # conversation history we will maintain and pass into chat each time we (re)start streaming
    messages = [system_msg, user_msg]

    # This outer loop cycles through streaming sessions. We restart a stream if the model requests tools.
    while True:
        stream = chat(
            model=MODEL,
            messages=messages,
            think=True,
            stream=True,
            # pass python callables so the SDK can include tool schemas (optional)
            tools=list(AVAILABLE_TOOLS.values()),
        )

        in_thinking = False
        final_accum = []
        assistant_partial_content = ""  # store the last assistant content if provided
        tool_calls_detected = []

        # iterate streaming chunks
        for chunk in stream:
            # chunk.message may be None in some partial chunks — guard access
            msg = getattr(chunk, "message", None)
            if msg is None:
                continue

            # 1) Thinking trace appears: print continuously
            thinking = getattr(msg, "thinking", None)
            if thinking and not in_thinking:
                in_thinking = True
                print("Thinking:\n", end="")
            if thinking:
                # print thinking without adding extra newline so it appears continuous
                print(thinking, end="", flush=True)
                continue

            # 2) Check if model emitted tool_calls
            tcalls = getattr(msg, "tool_calls", None)
            if tcalls:
                # collect tool calls (could be a list)
                # Print a newline if we were in thinking mode so output stays readable
                if in_thinking:
                    print("\n", end="")
                    in_thinking = False
                print("\n[Model requested tools]\n")
                # Save a reference to the partial assistant content if provided
                assistant_partial_content = getattr(msg, "content", "") or assistant_partial_content

                # We'll execute each tool call synchronously, append the results as tool messages,
                # and then restart the streaming chat with the updated messages.
                # Some models may emit multiple tool_calls; handle them in order.
                for tc in tcalls:
                    # Provide a readable printout of the request
                    try:
                        fname = tc.function.name
                        fargs = tc.function.arguments or {}
                    except Exception:
                        fname = getattr(tc.function, "name", None) or str(tc)
                        fargs = getattr(tc.function, "arguments", None) or {}
                    print(f"Tool requested: {fname} with args: {fargs}")

                    result = execute_tool_call(tc)
                    print(f"Tool result: {result}\n")

                    # Append the tool's response into the conversation as a tool-role message
                    messages.append({
                        "role": "tool",
                        "tool_name": fname,
                        "content": result
                    })

                # If the model included a partial assistant content before asking for tools, append it
                if assistant_partial_content:
                    messages.append({
                        "role": "assistant",
                        "content": assistant_partial_content
                    })

                # After executing tools and appending tool results, break the current streaming loop
                # and restart streaming so the model continues (now with tool outputs available).
                tool_calls_detected = tcalls
                break  # break out of the for chunk in stream loop

            # 3) Normal assistant content chunk (final or partial)
            content = getattr(msg, "content", None)
            if content:
                # If we were in thinking, print a separator before the answer
                if in_thinking:
                    print("\n\nAnswer:\n", end="")
                    in_thinking = False
                print(content, end="", flush=True)
                final_accum.append(content)

        # end of this streaming session
        # If we detected tool calls, restart streaming loop with updated messages.
        if tool_calls_detected:
            print("\n\n[Restarting stream to continue after tool execution...]\n")
            # continue outer while True to re-open stream with messages that include tool outputs
            time.sleep(0.05)
            continue

        # No tool calls were detected and stream finished -> we're done
        final_answer = "".join(final_accum).strip()
        print("\n\n--- STREAM COMPLETE ---\n")
        if final_answer:
            print("Final answer:\n")
            print(final_answer)
        else:
            print("(no final answer parsed from stream)")

        # Return final answer (or thinking trace if no final)
        return final_answer or "".join(final_accum)


if __name__ == "__main__":
    q = input("Ask something: ")
    ans = start_rag_stream(q)
    print("\n=== Returned to main ===\n", ans)
