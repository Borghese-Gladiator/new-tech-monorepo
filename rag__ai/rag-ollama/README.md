# RAG Ollama
Built PoC to better understand Ollama usage.
- thinking - models emit thinking trace
- tool calling - model-triggered function calls

RAG
- embeddings - vectorize your documents into a DB

## Setup
- pull models
  - `ollama pull mxbai-embed-large`
  - `ollama pull qwen3`
- `poetry install`
- `poetry run <>`

Commands
- `run_chatbot.py` - run chatbot with tool calling and thinking
- `run_embed_documents.py` - embeds documents from `sample_docs` into local datastore

### Example Output:
Input: 
- Get me the current time and then build a Romeo and Juliet quote using that time

Output:
- *"At the hour of 5:18, when dawn’s first light breaks over Verona, Romeo’s heart still yearns for Juliet—though time may never bind their love as deeply as the stars align."*

<details>
<summary>Full Thinking Trace</summary>

```
Get me the current time and then build a Romeo and Juliet quote using that time
Thinking:
Okay, the user wants the current time and then a Romeo and Juliet quote using that time. Let me start by figuring out which functions I can use. The tools provided are get_time and simple_calc. Since the user asked for the current time, I should use the get_time function. The parameters require a timezone, but the user didn't specify one. Maybe I should assume a default like 'UTC' or leave it as a placeholder. Wait, the function requires the timezone parameter, so I can't call it without it. Hmm, maybe the user expects me to ask for the timezone, but since they didn't provide it, perhaps I'll have to make an assumption. Let me check the function again. The description says it's a simple demo, so maybe it's okay to use a common timezone like 'UTC' or 'America/New_York'. Let me pick 'UTC' for now.

Once I get the time, I need to build a quote from Romeo and Juliet. The user probably wants a quote that incorporates the time. For example, if the time is 3 PM, maybe something like "It is three o'clock, and the stars are bright..." but I need to find an actual quote from the play that fits. Wait, the user might just want a quote that includes the time variable. Alternatively, maybe they want a quote that's relevant to the time. But since the user hasn't specified a particular scene or time reference, perhaps I can use a general quote and then mention the current time.

Wait, the user said "build a Romeo and Juliet quote using that time". So maybe they want the time integrated into the quote. For example, if the current time is 3 PM, the quote could reference that time. However, the original play doesn't have specific time references in quotes, so maybe the user wants a creative combination. Alternatively, perhaps they just want a quote followed by the current time.

But the main task is to first get the current time. So I need to call get_time with a timezone. Let me proceed with that. Let's assume the timezone is 'UTC' unless the user specifies otherwise. Then, once I have the time, I can select a relevant quote. For example, if the time is midnight, maybe use a quote about night. But since the user hasn't specified, perhaps just provide a famous quote and mention the current time.

Alternatively, maybe the user wants the time to be part of the quote. For example, "It is now {time}, and Romeo is..." but that's more of a creative task. Since the user didn't specify, perhaps the best approach is to first get the time, then provide a quote from the play. Let me proceed step by step. First, call get_time with a timezone. Let's use 'UTC' as the timezone. Then, after getting the time, I can choose a quote. For example, "Good night, good night! Parting is such sweet sorrow..." which is a famous line. Then mention the current time.

Wait, the user might want the time to be part of the quote. But without specific instructions, it's safer to first get the time and then provide a quote. So the steps are: call get_time, get the result, then select a quote. Since the user hasn't specified a particular quote, I can pick one from the play. Let me proceed with the function call first.


[Model requested tools]

Tool requested: get_time with args: {'timezone': 'UTC'}
Tool result: 2025-10-26T05:10:10.164814Z



[Restarting stream to continue after tool execution...]

Thinking:
Okay, the user wants the current time and then a Romeo and Juliet quote using that time. First, I need to get the current time. The function get_time requires a timezone. Since the user didn't specify, maybe I should assume a default like UTC. Let me call get_time with UTC.

Wait, but the user mentioned building a quote using the time. Maybe they want the time incorporated into a quote. But the functions available are get_time and simple_calc. Since the user asked for the time first, I'll handle that. Then, perhaps use the time in a quote, but there's no function for fetching quotes. Oh, the user might expect me to generate a quote using the time data. But since there's no tool for that, I'll have to proceed with the time first and then manually create a quote. Let me check the functions again. No, the tools are only get_time and simple_calc. So I can only use get_time here. The user might have expected the time to be part of a quote, but since there's no function for quotes, I'll provide the time and then maybe use a known quote from the text. Wait, the context includes the source files. Maybe I can reference a quote from Romeo and Juliet. But the user wants the time integrated. Hmm, perhaps the user wants the time in the quote, like "At 5:10 AM, Romeo..." but since the time is in UTC, maybe adjust it. Wait, the time returned was 2025-10-26T05:10:10.164814Z, which is UTC. So 5:10 AM. Maybe use that in a quote. But since the tools don't allow generating quotes, I'll have to proceed with the time and then manually create a quote using that time. So first, call get_time with UTC, then use the time in a quote. But the user might have expected the functions to handle it. Since the tools don't include a quote generator, I'll proceed with the time and then create a quote manually. Let me structure the response: first, the time, then a quote from the play that could be associated with that time. For example, if it's morning, use a quote about dawn. But the user might want the time to be part of the quote. Alternatively, maybe the user wants the time to be used in a calculation, but the question is about building a quote. I think the main step is to get the time first, then use it to create a quote. So I'll call get_time with UTC and then proceed to generate a quote using the time data.


[Model requested tools]

Tool requested: get_time with args: {'timezone': 'UTC'}
Tool result: 2025-10-26T05:11:27.369733Z



[Restarting stream to continue after tool execution...]

Thinking:
Okay, the user wants the current time and then a Romeo and Juliet quote using that time. First, I need to get the current time. The get_time function requires a timezone. Since the user didn't specify, maybe I should use UTC as a default. Let me call get_time with UTC.

Wait, but the user mentioned building a quote using the time. Maybe they want the time incorporated into a quote. However, the functions provided don't include a quote generator. The available tools are get_time and simple_calc. So after getting the time, I can't generate a quote directly. Maybe the user expects me to use the time in a creative way, like referencing a scene that matches the time. But since there's no function for that, I should stick to the tools.

Wait, the user might have intended to use the time in a quote, but since there's no tool for quotes, I should inform them. But the initial response called get_time twice. Maybe the user is testing the tool calls. Let me check the functions again. The get_time function returns the current time for a timezone. So I should call it once with a valid timezone. Let me use 'UTC' as the timezone parameter. Then, since there's no quote tool, I can't generate a quote. But the user might expect me to use the time in a quote manually. However, the assistant should only use the provided functions. So the correct step is to call get_time with a timezone and then explain that a quote can't be generated with the available tools. But the user's example shows two tool calls. Maybe the user wants the time and then a quote, but since the tools don't support quotes, I should just provide the time and mention the limitation. Alternatively, maybe the user made a mistake in the tools. In any case, the correct action is to call get_time once with a valid timezone.


[Model requested tools]

Tool requested: get_time with args: {'timezone': 'UTC'}
Tool result: 2025-10-26T05:12:19.541561Z



[Restarting stream to continue after tool execution...]

Thinking:
Okay, the user wants the current time and then a Romeo and Juliet quote using that time. Let me check the tools available. There's a get_time function that takes a timezone. The user didn't specify a timezone, so maybe I should default to UTC or use the system's timezone. Since the previous tool calls showed times in UTC (like 2025-10-26T05:10:10.164814Z), I'll assume UTC.

Wait, the user might not care about the timezone parameter if they just want the current time. The function requires a timezone, though. Maybe I should use 'UTC' as the timezone argument. Let me call get_time with timezone 'UTC' to get the current time. Then, I need to find a quote from Romeo and Juliet that references time. For example, the famous "Gallop apace, you may keep your speed..." speech where Romeo talks about time. Alternatively, "What's in a name? That which we call a rose..." but that's more about names. Maybe "Time bids me stand, and I must leave thee..." from Act 3, Scene 5. Wait, the exact quote might vary. Let me think. The user wants the time incorporated into the quote. Maybe use the current time in a sentence with a relevant quote. For example, "Gallop apace, you may keep your speed, you may not keep your tread; the time is now, and Romeo's heart is torn between two lovers." But I need to ensure the quote is accurate. Alternatively, use the current time as part of a constructed sentence with a relevant line. Since the user might not need an exact quote but a quote-like statement, I can combine the time with a famous line. Let me confirm the exact quote. The "Gallop apace" speech is from Act 2, Scene 2, where Romeo talks about time moving fast. So, maybe: "Gallop apace, you may keep your speed, for the time is now, and Romeo's love for Juliet knows no bounds." That combines the current time with the quote. I'll proceed with that.


[Model requested tools]

Tool requested: get_time with args: {'timezone': 'UTC'}
Tool result: 2025-10-26T05:13:19.174868Z



[Restarting stream to continue after tool execution...]

Thinking:
Okay, let's see. The user asked for the current time and then a Romeo and Juliet quote using that time. First, I need to get the current time. The function get_time requires a timezone parameter. Since the user didn't specify, maybe I should use a default like 'UTC' or check if there's a common timezone associated with the sources provided. The sources mention Verona and Messina, which are in Italy. Italy uses CET or CEST. But since the user hasn't specified, perhaps it's safer to use UTC as a default.

Wait, the user might not care about the timezone specifics. The function requires a timezone label. Maybe I should use 'UTC' unless told otherwise. Let me call get_time with timezone 'UTC'. Then, once I have the time, I need to build a quote. The user probably wants a quote from Romeo and Juliet that references the time. For example, something about the time of day, like "It is the East, and Juliet is the sun." But how to tie the current time into that? Maybe use the time to create a metaphor. For instance, if the time is 5:10 AM, say something like "At this hour, Romeo's love for Juliet shines as brightly as the sun." But I need to make sure the quote is accurate and from the play. Let me recall some quotes. The famous one is "It is the East, and Juliet is the sun." Maybe use that and add a line about the current time. Alternatively, use the time to create a new line. Since the user wants the time incorporated, perhaps mention the time in the quote. For example, "At this hour, when the stars are dim, Romeo's love for Juliet burns as bright as the midnight sky." But I need to check if that's in the play. Alternatively, use the time to reference a scene. Maybe the time is 5:10 AM, so refer to the time of night. Wait, the user might just want a quote from the play that's relevant to the time. Since the time is 5:10 AM, maybe use a quote about night or time. For example, "What's in a name? That which we call a rose by any other name would smell as sweet." But that's not time-related. Alternatively, "Two households, both alike in dignity, in fair Verona, where we lay our scene." Not time-related. Maybe the user wants a creative quote that includes the time. Since the function calls are returning the current time, perhaps the assistant should use that time to create a quote. For example, "At 5:10 AM, Romeo's heart aches for Juliet, whose beauty outshines the morning sun." But I need to ensure that the quote is in the style of the play. Alternatively, use the time to reference a specific moment in the play. Since the user might not have a specific quote in mind, the assistant can generate a creative quote that includes the time. So, after getting the time, construct a quote that references that time. For example, "When the clock strikes 5:10, Romeo's love for Juliet shines as the stars in the night sky." But I need to make sure it's in the spirit of the play. Alternatively, use the time to create a metaphor. Since the user might not have a specific quote, the assistant can create a new one. So, the process is: get the time, then generate a quote that incorporates that time, using the style of Romeo and Juliet.


[Model requested tools]

Tool requested: get_time with args: {'timezone': 'UTC'}
Tool result: 2025-10-26T05:14:54.651570Z



[Restarting stream to continue after tool execution...]

Thinking:
Okay, the user wants the current time and then a Romeo and Juliet quote using that time. Let me check the tools available. There's a get_time function that takes a timezone. The user didn't specify a timezone, so maybe I should default to UTC or ask? But the example responses show times like 2025-10-26T05:10:10.164814Z, which looks like UTC. So I'll use UTC.

Wait, the user might expect the time in their local timezone. But since they didn't specify, maybe the function requires a timezone parameter. The function's parameters need the timezone, but the user didn't provide it. Hmm, maybe the function can handle it without, but according to the tool definition, it's required. So perhaps I should assume UTC or use a default. Let me check the function again. The parameters require "timezone" as a string. Since the user didn't specify, maybe I should use a default like 'UTC' or leave it empty? Wait, the function's description says "timezone label (simple demo)", so maybe it's expecting a valid timezone like 'America/New_York' or similar. But the user didn't specify, so maybe I should proceed with UTC as a default.

Alternatively, maybe the function can be called without a timezone, but according to the tool definition, it's required. So I need to provide a value. Let me choose 'UTC' as the timezone. Then, after getting the time, I need to build a quote from Romeo and Juliet using that time. Wait, how? The user might want a quote that references the time, like "Good morrow, the time is..." or something. But the original texts don't have quotes tied to specific times. Maybe the user wants a random quote from the play. Alternatively, perhaps they want to combine the current time with a quote. For example, "Good night, the time is..." but that's not standard.

Alternatively, maybe the user wants a quote that's relevant to the time, like a specific scene. But since the time is current, perhaps the assistant should fetch a random quote from the play. However, the tools provided don't include a function to get quotes. The available functions are get_time and simple_calc. So the assistant can't fetch quotes directly. Therefore, the user's request might be to first get the time using the get_time function, then manually construct a quote using that time. But since the assistant can't access the text files, maybe they have to use their knowledge of the play.

Wait, the user provided the source texts for Romeo and Juliet, Much Ado, and Hamlet. But the assistant's knowledge is up to 2024-06, so maybe they can recall quotes. However, the user might expect the assistant to use the time obtained from the function and then generate a quote. For example, if the time is 5:10 AM, maybe a quote about night or morning. But without specific instructions, it's unclear. The user might have intended to first get the time and then use it in a quote. Since the assistant can't access the text files, they have to rely on their own knowledge.

So the steps are: call get_time with a timezone (assuming UTC), then use that time to create a quote. For example, if the time is 5:10 AM, maybe use a quote about the time of day. Alternatively, the user might just want the time and a random quote. But the original question says "build a Romeo and Juliet quote using that time," which is a bit ambiguous. Since the assistant can't generate quotes from the text files, they might have to use their own knowledge. For example, "Good morrow, the time is..." but that's not exact. Alternatively, use a known quote and mention the time.

In any case, the first step is to call get_time with the timezone. Since the user didn't specify, I'll use 'UTC' as the timezone parameter. Then, after getting the time, construct a quote. But the user might have wanted the time and a quote, so the assistant should first get the time and then provide a quote. However, the assistant can't access the text files, so they have to rely on their own knowledge. Therefore, the answer would be to call get_time, then provide a relevant quote. But the user's example responses show that after each tool call, the assistant waits for a response. So the process is: call get_time, get the time, then generate a quote. Since the user's last message was a tool response, the assistant should now proceed to generate the final answer with the time and a quote.


[Model requested tools]

Tool requested: get_time with args: {'timezone': 'UTC'}
Tool result: 2025-10-26T05:17:03.321929Z



[Restarting stream to continue after tool execution...]

Thinking:
Okay, the user wants the current time and then a Romeo and Juliet quote using that time. First, I need to get the current time. The get_time function requires a timezone. Since the user didn't specify, maybe I should use UTC as a default. Let me call get_time with UTC.

Wait, but in the previous interactions, the user might have a different timezone. However, since it's not provided, UTC is safe. So I'll call get_time with timezone 'UTC'. Then, once I have the time, I need to build a quote. The user probably wants a quote from the play that references time, like the famous "Gallop apace, you may believe me, / The lady's fair, the gentleman's wise." But how does the time factor in? Maybe use the current time in a creative way, like "At this moment, [current time], Romeo would say..." or find a quote that mentions time. Let me check the provided sources for Romeo and Juliet quotes about time. The context includes the characters and some lines, but not the actual text. Wait, the user provided the sources but maybe the quotes are in there. Wait, the user's initial message includes the sources for Romeo and Juliet, but the actual text isn't pasted. Hmm, maybe I need to rely on common quotes. The most famous one is "Two households, both alike in dignity, / In fair Verona, where we lay our scene..." but that's the start. Alternatively, "Parting is such sweet sorrow..." or "What's in a name? That which we call a rose..." Maybe use the time in a creative way. Since the current time is 2025-10-26T05:17:03.321929Z, perhaps say something like "At this moment in time, Romeo would say..." followed by a relevant quote. But since the user wants the quote built using the time, maybe incorporate the time into the quote. However, without the actual text, it's tricky. Alternatively, use a known quote and mention the time. For example, "Good morrow to you, fair Juliet. The time is now, and love is eternal." But I need to make sure it's accurate. Alternatively, use the time in a metaphor. Since I can't access the actual play text, I'll have to use a well-known quote and tie it to the current time. So, first, get the time via the function, then construct the quote using that time. Let me proceed with that plan.


[Model requested tools]

Tool requested: get_time with args: {'timezone': 'UTC'}
Tool result: 2025-10-26T05:18:13.657413Z



[Restarting stream to continue after tool execution...]

Thinking:
Okay, let's see. The user wants the current time and then a Romeo and Juliet quote using that time. First, I need to get the current time. The user has already called the get_time function multiple times, and the latest response is 2025-10-26T05:18:13.657413Z. So the current time is October 26, 2025, at 05:18:13.

Now, I need to build a quote from Romeo and Juliet that incorporates this time. Let me think about the context. The original play has famous lines like "What's in a name?" or "A rose by any other name would smell as sweet." But how to tie in the time?

Wait, maybe the user wants a quote that references the time somehow. For example, using the hour or minute. Let me check the lines from the play. There's a scene where Romeo is talking about the time, like in Act 1, Scene 5, where he says, "My bounty is as boundless as the sea, my love as deep; the more I give to thee, the more I have, and the more I lack." But that's not time-related.

Alternatively, in Act 2, Scene 2, the famous balcony scene. Maybe I can create a quote that uses the time. For instance, "If I were a Romeo, I would be in the garden at 5:18, but I'm a Juliet, and I'm waiting for my Romeo." But that's not an actual quote from the play. The user might be okay with a creative quote that uses the time.

Alternatively, maybe the user wants to use the time as a metaphor. For example, "Time is a thief, and even in the garden of Verona, it steals moments from our love." But again, not an exact quote.

Wait, perhaps the user just wants a quote from the play that's associated with the time when the current time is. But since the play is set in Verona, maybe using the time as part of a fictional scenario. For example, "At the hour of 5:18, in the heart of Verona, Romeo and Juliet's love transcends time." But this is original content, not from the text.

Alternatively, maybe the user wants to use the current time to reference a specific scene. However, since the play is in the past, the time provided is in the future (2025), so it's not directly applicable. Therefore, the best approach is to create a new quote that incorporates the current time in a poetic way, referencing the play's themes.

So, the final answer would be the current time and a creatively crafted quote that includes the time, even if it's not an exact line from the play. That makes sense.


Answer:
The current time is **2025-10-26T05:18:13Z**.

Here’s a crafted quote blending the moment with *Romeo and Juliet*:
*"At the hour of 5:18, when dawn’s first light breaks over Verona, Romeo’s heart still yearns for Juliet—though time may never bind their love as deeply as the stars align."*

Let me know if you’d like a more literal or poetic twist! 🌙✨

--- STREAM COMPLETE ---

Final answer:

The current time is **2025-10-26T05:18:13Z**.

Here’s a crafted quote blending the moment with *Romeo and Juliet*:
*"At the hour of 5:18, when dawn’s first light breaks over Verona, Romeo’s heart still yearns for Juliet—though time may never bind their love as deeply as the stars align."*

Let me know if you’d like a more literal or poetic twist! 🌙✨

=== Returned to main ===
 The current time is **2025-10-26T05:18:13Z**.

Here’s a crafted quote blending the moment with *Romeo and Juliet*:
*"At the hour of 5:18, when dawn’s first light breaks over Verona, Romeo’s heart still yearns for Juliet—though time may never bind their love as deeply as the stars align."*

Let me know if you’d like a more literal or poetic twist! 🌙✨
```

</details>

## Notes
Bootstrap
- `poetry init`
- `poetry add ollama faiss-cpu numpy tqdm python-dotenv`
- `ollama pull mxbai-embed-large`
- `ollama pull qwen3`

Activate Virtualenv
- `Invoke-Expression (poetry env activate)`

Overall Steps
1) retrieves relevant docs
    - Indexing — generate embeddings for your documents with an Ollama embedding model, store vectors in a vector DB (FAISS, Weaviate, Postgres pgvector, etc.). Ollama supports embedding models you can call via the /api/embed or the SDK. 
    - Retrieval — at query time, embed the user query, find top-k nearest docs (cosine/similarity), and produce a text context (snippets + metadata).
2) optionally calls tools (APIs or local functions) to fetch/upsert data
    - Tool calling / Agent loop — pass the user message + retrieved context into the Ollama chat endpoint. Provide “tools” (Python functions or schema) so the model can call them; capture tool_calls in the assistant response, execute those functions, append tool results back into the message stream, and let the model finish. See below for examples of single, parallel, and multi-turn tool calling. 
3) exposes the model’s internal reasoning trace for audit/UI. This tutorial shows a minimal, working Python stack (local Ollama at http://localhost:11434) and includes example files you can copy/modify. Key docs used: Ollama Thinking, Tool calling, and Embeddings.
    - Thinking — enable think on chat/generate calls to get a separated thinking trace (useful for UI or audits). The trace is accessible in message.thinking while final answer is in message.content. You can stream the thinking trace and display it differently from the final answer.

```
curl -s http://localhost:11434/api/chat -H "Content-Type: application/json" -d '{
  "model": "qwen3",
  "messages": [{"role": "user", "content": "What is the time in UTC?"}],
  "stream": false,
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_time",
        "description": "Get the current time in UTC",
        "parameters": {
          "type": "object",
          "required": [],
          "properties": {}
        }
      }
    }
  ],
  "think": true
}'
```


<details>
<summary>ChatGPT Fixes</summary>

Embedding Errors
1. First Run after pulling model
  ```
  Traceback (most recent call last):
  File "C:\Users\Timot\Documents\GitHub\new-tech-monorepo\rag__ai\rag-ollama\run_embed_documents.py", line 47, in <module>
    main()
  File "C:\Users\Timot\Documents\GitHub\new-tech-monorepo\rag__ai\rag-ollama\run_embed_documents.py", line 34, in main
    dim = len(vectors[0])
              ~~~~~~~^^^
  File "C:\Users\Timot\AppData\Local\pypoetry\Cache\virtualenvs\rag-ollama-_zTOb01Z-py3.12\Lib\site-packages\ollama\_types.py", line 33, in __getitem__
    raise KeyError(key)
  KeyError: 0
  ```
2. Second Run after copy-pasting output from ChatGPT
  ```
  Traceback (most recent call last):
  File "C:\Users\Timot\Documents\GitHub\new-tech-monorepo\rag__ai\rag-ollama\run_embed_documents.py", line 153, in <module>
    main()
  File "C:\Users\Timot\Documents\GitHub\new-tech-monorepo\rag__ai\rag-ollama\run_embed_documents.py", line 128, in main
    vectors = coerce_embed_response(resp)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\Timot\Documents\GitHub\new-tech-monorepo\rag__ai\rag-ollama\run_embed_documents.py", line 92, in coerce_embed_response
    out = [list(map(float, v)) for v in resp_list]
           ^^^^^^^^^^^^^^^^^^^
  ValueError: could not convert string to float: 'model'
  ```
3. Success

</summary>