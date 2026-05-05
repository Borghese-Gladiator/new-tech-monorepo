# Ollama Pi — Local Coding Agent Setup (macOS)

A fully local, terminal-native coding agent built on **Ollama** (model runtime) + **aider** (agent layer).

- **Ollama** = runs LLMs locally (Llama, Mistral, Code Llama, etc.)
- **aider** = agent on top of Ollama that reads/edits code, runs tools, iterates
- **You** = orchestrator via CLI

> **Why aider, not "Pi"?** The folder name is historical. `pi-agent` on PyPI is ambiguous (multiple unrelated projects use that name and none is the well-known Ollama agent). [`aider`](https://aider.chat) is the mature, actively maintained terminal coding agent: native Ollama support via `--model ollama_chat/<name>`, filesystem + git integration built in, no ambiguity.

> **Dependency management: Poetry, fully local.** All Python deps for this folder (aider + the embedding indexer) are pinned in a single `pyproject.toml` and installed into `./.venv/` inside this folder. No global pip installs, no site-packages pollution. The `.venv/` is gitignored.

Benefits: fully offline, no API costs, better privacy, fast iteration, customizable.

---

## Exact Setup Steps (macOS)

### 1. Install Ollama
```bash
brew install ollama
```
Or download from https://ollama.com/download

Start the service (leave running in a terminal tab):
```bash
ollama serve
```

### 2. Pull a coding model
Pick one based on RAM / speed needs:
```bash
ollama pull codellama   # strongest for code
ollama pull mistral     # lighter / faster
ollama pull llama3      # stronger general model (needs more RAM)
```

Quick sanity check before adding Pi on top:
```bash
ollama run mistral
```

### 3. Install Poetry (per-user, no system pollution)
```bash
curl -sSL https://install.python-poetry.org | python3 -
```
Verify:
```bash
poetry --version
```

### 4. Install the agent + embedding deps via Poetry
From this folder:
```bash
cd ollama-pi-coding-agent-first__ai
poetry config virtualenvs.in-project true --local   # already committed via poetry.toml
poetry install
```
This creates `./.venv/` inside this folder and installs `aider-chat`, `lancedb`, `pyarrow`, `requests`. Python is pinned to `>=3.10,<3.13` (aider does not yet support 3.13). On this machine Poetry resolved to **Python 3.10.9** (pyenv).

> Or run `bash setup.sh` for a one-shot bootstrap (Ollama + Poetry check + `poetry install`).

### 5. Point aider at Ollama (env vars)
```bash
export OPENAI_API_BASE=http://localhost:11434/v1
export OPENAI_API_KEY=ollama
```
(Optional — aider auto-detects Ollama from the `ollama_chat/` model prefix, but these env vars are useful for other OpenAI-compatible tools.)

### 6. Run aider in a project (no global install)
```bash
cd your-project
poetry --directory=/path/to/ollama-pi-coding-agent-first__ai run aider --model ollama_chat/qwen3-coder:30b
```
Or, if you `cd` into this folder first:
```bash
poetry run aider --model ollama_chat/codellama:13b-instruct
```
Pick whichever model you pulled in step 2. Aider's Ollama prefix is `ollama_chat/<name>`.

### 7. Use it
Example prompts inside aider:
- `Explain this repo`
- `Refactor this function to be async`
- `Add tests for the API routes`
- `Fix this bug: <paste error>`

---

## Common Issues

**`connection refused localhost:11434`** — Ollama isn't running:
```bash
ollama serve
```

**Model too slow** — switch to `mistral`, close RAM-heavy apps.

**Python env conflicts** — use a virtualenv (see step 3).

---

## Recommended Defaults
- **Model:** `mistral` or `llama3`
- **Best for:** small-to-medium repos
- **Combine with:** git + tests for safe iteration

---

## Resolved Questions

### 1. Agent to standardize on
**`aider`** is the Ollama-compatible coding agent we use here.
- `pi-agent` on PyPI is ambiguous (multiple unrelated projects use that name) and is not the well-known Ollama agent.
- `aider` (https://aider.chat) is the mature, actively maintained terminal coding agent, supports Ollama out of the box via `--model ollama_chat/<name>`, has filesystem + git integration built in, and avoids the "which Pi" ambiguity entirely.
- Installed via **Poetry**, scoped to `./.venv/` in this folder — no global pip install.

### 2. Mac specs (this machine)
- Chip: **Apple M2 Max** (arm64)
- RAM: **64 GB**
- macOS: **26.4** (build 25E246)

Model sizing for 64 GB Apple Silicon:
- Comfortably runs 7B–13B models at full speed (`mistral`, `codellama:7b`, `codellama:13b`, `llama3:8b`).
- Can run 34B quantized (`codellama:34b-instruct-q4_K_M`) — slower but viable.
- 70B is borderline; only worth it for one-shot batch tasks, not interactive coding.
- **Default pick:** `codellama:13b-instruct` for code, `llama3:8b` for general chat.

---

## Codebase Embeddings

Local LLMs have small context windows, so for any non-trivial repo the agent needs a retrieval layer to pull in the right files/symbols on demand. Two complementary approaches:

### Option A — Vector embeddings (semantic search)
Classic RAG: chunk the repo, embed each chunk, store in a local vector DB, retrieve top-k on each prompt.

- **Embedding model (local, via Ollama):** `nomic-embed-text` or `mxbai-embed-large`
  ```bash
  ollama pull nomic-embed-text
  ```
- **Vector store (local):** `chromadb`, `qdrant` (Docker), or `lancedb` (embedded, zero-server)
- **Indexer:** simple Python script that walks the repo, chunks by function/class (or fixed token windows), embeds, and upserts. Re-run on git changes (or wire to a `post-commit` hook).
- **Agent integration:** point `aider` (or whichever agent) at the vector DB as a retrieval tool, or pre-stuff top-k chunks into the system prompt before each turn.

Good for: "find code that does X conceptually," fuzzy questions, docs/comments search.

### Option B — Code knowledge graph (structural)
**GitNexus** (already installed locally, exposed via MCP). It indexes the repo into a graph of Files, Functions, Classes, Methods, Processes, and edges like `CALLS`, `IMPORTS`, `EXTENDS`, `IMPLEMENTS`, `DEFINES`, `MEMBER_OF`.

- Index a repo:
  ```bash
  npx gitnexus analyze
  ```
- Tools available via MCP: `query`, `context`, `impact`, `detect_changes`, `rename`, `cypher`, `list_repos`.
- Strengths: exact call graphs, blast-radius analysis, "what calls X / what does X call," safe rename/refactor — none of which embeddings give you reliably.
- Limitation: does **not** do semantic similarity. It won't find "code that conceptually handles auth" if the symbols aren't named that way.

### Recommendation: use both
- **GitNexus** for structural questions (impact, refactor, trace flows) — it's already wired up via MCP, so the Ollama+aider agent can call it as a tool.
- **Vector embeddings** for semantic search — add a small `nomic-embed-text` + `lancedb` layer on top.

### Implemented for this repo

Scripts live in `embeddings/` and are scoped strictly to **this repo only** (the `new-tech-monorepo` root). The indexer refuses to walk outside `REPO_ROOT`.

Decisions:
- **Chunking:** per-function / per-class (regex-based symbol splitter, falls back to whole-file).
- **Reindex trigger:** on-demand only (`python3 embeddings/index.py`). No hooks, no watchers.
- **Storage scope:** per-repo. The LanceDB store lives at `embeddings/.lancedb/` inside this folder and is git-ignored. No global cross-repo store.
- **Embedding model:** `embeddinggemma:latest` (already pulled locally via Ollama). Override with `EMBED_MODEL=...`.
- **Vector store:** `lancedb` (embedded, no server).

#### Setup
Embedding deps (`lancedb`, `pyarrow`, `requests`) are managed by the same root Poetry project as `aider` — no separate `requirements.txt`. After `poetry install`:
```bash
cd ollama-pi-coding-agent-first__ai
ollama serve   # in another tab if not already running
```

#### Index (run on demand)
```bash
poetry run python embeddings/index.py            # incremental (skips unchanged chunks by hash)
poetry run python embeddings/index.py --rebuild  # wipe and reindex
poetry run python embeddings/index.py --stats    # show row count + last index time
```

#### Search
```bash
poetry run python embeddings/search.py "where do we configure ollama"
poetry run python embeddings/search.py --k 10 "embedding indexer"
poetry run python embeddings/search.py --json "auth flow"     # machine-readable for agents
```

#### Wiring into aider (optional)
Add a custom command or shell-out that pipes `search.py --json` results into the aider prompt — the JSON shape is stable: `{query, results: [{path, symbol, start_line, score, snippet}]}`.

For "what calls / what breaks / rename" questions, prefer GitNexus MCP tools (`impact`, `query`, `rename`) — they are structurally precise where embeddings are only fuzzy.

#### Proof: live retrieval (recorded after rebuild)

Index built: `files=515 chunks_scanned=1271 chunks_added=1211` in 497.4s using `embeddinggemma:latest` (768-dim) into `embeddings/.lancedb/`.

The queries below intentionally avoid the obvious keywords (no "sleep", no "AbortController", no "row-level security") to verify the retrieval is **semantic**, not just lexical.

**Query 1 — "function that pauses execution for a duration"**

```
$ python3 embeddings/search.py --k 3 "function that pauses execution for a duration"
langchain-python-first/utils.py:2  [log_execution_duration]  d=0.855
  def log_execution_duration(func):

react-abort-controller/src/utils/index.ts:1  [<file>]  d=0.891
  export * from './wait';

snakeviz-first/example_script.py:2  [slow_function]  d=0.926
  def slow_function():
      time.sleep(2)  # Simulates a slow operation
```
Hit #3 is `slow_function` containing `time.sleep(2)` — found purely from meaning; the query contains neither `sleep` nor `time`.

**Query 2 — "cancel an in-flight HTTP request when the component unmounts"**

```
$ python3 embeddings/search.py --k 3 "cancel an in-flight HTTP request when the component unmounts"
github-speckit-first__ai/task-tracker-tutorial/src/components/TaskItem.tsx:32  [handleCancel]  d=1.115
  function handleCancel() {
    setEditTitle(task.title)
    setIsEditing(false)
  }

agentic-development-task-system__ai/src/client/components/ui/InlineTextField.tsx:60  [cancel]  d=1.120
  function cancel() {
    setDraft(value);
    setEditing(false);
  }

react-abort-controller/README.md:1  [<file>]  d=1.162
  ## Created on June 10th, 2022 12:35 AM
  # React Abort Controller
  First Abort Controller to handle race conditions in React
```
The query never says "abort" or "controller," yet the React Abort Controller project surfaces in the top 3 alongside `cancel`/`handleCancel` handlers.

**Query 3 — "isolate data per customer so one tenant cannot see another tenant's records"**

```
$ python3 embeddings/search.py --k 3 "isolate data per customer so one tenant cannot see another tenant's records"
python-multi-tenancy-first/README.md:1  [<file>]  d=1.069
  Quick PoC that I generated when looking at how companies implement multi-tenancy
  # Python Multi-Tenancy PoC
  Subdomain-based multi-tenant API using FastAPI + SQLAlchemy 2.0 + Postgres Row Level Security (RLS).

python-multi-tenancy-first/docs/design_for_multi_tenancy.md:343  [createProject]  d=1.086
  export async function createProject(token: string, name: string) {
    const tenant = getTenantSlug();
    ...
  }

python-multi-tenancy-first/tests/test_app.py:75  [test_tenant_isolation]  d=1.132
  def test_tenant_isolation(self, client, acme_headers, globex_headers):
      # Create a project under acme
      client.post("/projects?tenant=acme&name=acme-only", headers=acme_headers)
      # Globex should not see it (no RLS in SQLite, but we still test the endpoint works)
```
Top hit is the multi-tenancy PoC; rank 3 is literally `test_tenant_isolation`. The query phrasing ("isolate data per customer") doesn't match any function name — but the test that *exercises* tenant isolation is retrieved.

Conclusion: the index returns semantically relevant chunks for paraphrased intent, not just keyword matches. That's what the agent needs.

#### Verification (Poetry-based)

Recorded after the Poetry migration. The existing LanceDB index at `embeddings/.lancedb/` was preserved through the migration — no rebuild needed.

**1. Index intact (1211 rows):**
```
$ poetry run python embeddings/index.py --stats
{
  "last_indexed_at": 1777905088.1279738,
  "repo_root": "/Users/timothy.shee/GitHub/new-tech-monorepo",
  "embed_model": "embeddinggemma:latest",
  "dim": 768,
  "files_seen": 515,
  "chunks_scanned": 1271,
  "chunks_added": 1211
}
rows in code_chunks: 1211
```

**2. Semantic search still works:**
```
$ poetry run python embeddings/search.py --k 3 "function that pauses execution for a duration"
langchain-python-first/utils.py:2  [log_execution_duration]  d=0.855
  def log_execution_duration(func):

react-abort-controller/src/utils/index.ts:1  [<file>]  d=0.891
  export * from './wait';

snakeviz-first/example_script.py:2  [slow_function]  d=0.926
  def slow_function():
      time.sleep(2)  # Simulates a slow operation
```

**3. aider is installed locally (not globally):**
```
$ poetry run aider --version
aider 0.86.2
```

The aider binary lives in `./.venv/bin/aider` and is only on PATH inside `poetry run`. It is not installed globally.

**4. aider answers prompts via local Ollama (end-to-end):**
```
$ poetry run aider --model ollama_chat/mistral:latest --no-git --yes \
    --message "What is 2+2? Reply with just the number."
Aider v0.86.2
Model: ollama_chat/mistral:latest with whole edit format
Git repo: none
Repo-map: disabled

4

Tokens: 603 sent, 1 received.
```

That confirms the full chain: Poetry venv → aider → `ollama_chat/` provider → local Ollama on `:11434` → mistral 7B → correct one-token answer. Same prompt + same model went off-prompt under opencode's `plan` agent (system-prompt overload), but works cleanly through aider.

---

## Files in this folder
- `README.md` — this guide
- `env.sample` — sample env vars for aider → Ollama
- `setup.sh` — one-shot setup helper script (Ollama + Poetry-based install)
- `pyproject.toml` / `poetry.lock` — Poetry project + locked deps (aider, lancedb, pyarrow, requests)
- `poetry.toml` — pins venv to `./.venv/` inside this folder
- `.venv/` — local virtualenv (gitignored)
- `embeddings/` — local LanceDB index + search scripts (see "Codebase Embeddings" above)

---

## Addendum — Cross-agent comparison (session findings)

Findings from a single test session that bootstrapped and ran three coding agents (aider, omp, opencode) against the same local Ollama on this machine. Same content is mirrored in `../oh-my-pi-first__ai/README.md` and `../opencode-first__ai/README.md` so any one of these folders is self-sufficient.

### A/B/C/D test on the same model (`mistral:latest`, ~7B) and same prompt

Prompt: `"What is 2+2? Reply with just the number."` Expected: `4`.

| Caller | Result | Notes |
| --- | :---: | --- |
| `command curl http://localhost:11434/api/generate ...` (bare Ollama) | ✅ `4` | Baseline. The model itself is fine. |
| `omp -p --no-tools --no-extensions --model ollama/mistral:latest "..."` | ✅ `4` | omp's plain-Q&A path is healthy when the MCP storm is bypassed and tools are off. |
| `opencode run -m ollama/mistral:latest --agent plan "..."` | ❌ off-prompt rant about CI/CD, dark mode, CSRF tokens | opencode's `plan` agent injects a verbose architectural system prompt. mistral 7B's instruction-following collapses under the weight; it pattern-completes on the system prompt instead of answering the user. |
| `poetry run aider --model ollama_chat/mistral:latest --no-git --yes --message "..."` | ✅ `4` | aider's system prompt is light; the model has room to actually answer. |

### Layer-isolation finding

When the bare Ollama API returns the right answer but a wrapper agent does not, the failure is in the **harness**, not the model. Two distinct harness-layer failure modes were observed in this session:

- **omp:** ~11 inherited Claude-Code MCP servers (HTTP 401 / ENOENT every cold start) polluted the tool list and likely degraded function-calling on `qwen3-coder:30b` (the model hallucinated a fake monorepo listing). Same model + same Ollama under opencode's clean tool list invoked `ls -a` correctly.
- **opencode:** the `plan` agent's heavy system prompt overwhelms small (≤7B) instruction-following. `--agent build` has a lighter prompt; `qwen3-coder:30b` and larger handle either.

### Recommended pairing matrix

Picking by hardware/model size on this machine (M2 Max, 64 GB):

| Model class | Best agent here | Why |
| --- | --- | --- |
| ≤ 7B local (`mistral`, `llama3.2`) | **aider** (this folder, via `poetry run aider`) | Lightest system prompt, cleanest tool surface. Avoids opencode's `plan`-prompt overload and omp's MCP storm. |
| 13–30B local (`qwen3-coder:30b`, `qwen2.5:14b`) | **opencode** | Tool-call reliability beats omp on the same model (real `ls` vs hallucinated). Use `--agent plan` for read-only or `--agent build` for full access. |
| 30B+ local with tool-using sessions | Hybrid: cloud default, local `smol` | Local 30B at ~10 tok/s is too slow for productive agentic loops; pin a cloud model to the default role and keep Ollama for cheap exploration subagents. |
| Cloud frontier (Claude Opus/Sonnet, GPT-4-class) | **omp** or **opencode** (parity at this tier) | Both have feature-rich TUIs; pick by feature preference (omp: TTSR, IPython kernel, native engine; opencode: client/server, GitHub PR fetch, web UI). |

### Permanent setup mitigations worth doing

- **`OLLAMA_KEEP_ALIVE=30s`** — set before `ollama serve` starts. Prevents the 50–57 GB pinned-after-kill state we hit with `qwen3-coder-next` (79.7B / 262K context).
- **omp:** prune `~/.claude/` MCP servers you don't actually use, or `alias omp='omp --no-extensions'` to skip discovery entirely.
- **opencode:** use `--agent build` for small models; reserve `--agent plan` for ≥30B or cloud.
- **Timeouts:** budget 300–600s per turn for local 30B agentic sessions, not 180s.
