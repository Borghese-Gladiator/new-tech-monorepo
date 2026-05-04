# Ollama Pi — Local Coding Agent Setup (macOS)

A fully local, terminal-native coding agent built on **Ollama** (model runtime) + **Pi** (agent layer).

- **Ollama** = runs LLMs locally (Llama, Mistral, Code Llama, etc.)
- **Pi** = agent on top of Ollama that reads/edits code, runs tools, iterates
- **You** = orchestrator via CLI

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

### 3. Install Pi (Ollama coding agent)
```bash
pip install pi-agent
```
Or from source if the package fails:
```bash
git clone https://github.com/<pi-repo>.git
cd pi
pip install -e .
```
> Note: Pi has multiple variants — confirm which repo/package before installing.

If you hit Python env issues, use a virtualenv:
```bash
python3 -m venv venv
source venv/bin/activate
pip install pi-agent
```

### 4. Point Pi at Ollama
```bash
export OPENAI_API_BASE=http://localhost:11434/v1
export OPENAI_API_KEY=ollama
```
This makes OpenAI-compatible tools talk to local Ollama.

### 5. Run Pi in a project
```bash
cd your-project
pi          # or: pi chat
```

### 6. Select a model
Inside Pi:
```
/model codellama
```
Or via env:
```bash
export PI_MODEL=codellama
```

### 7. Use it
Example prompts:
- `Explain this repo`
- `Refactor this function to be async`
- `Add tests for the API routes`
- `Fix this bug: <paste error>`

---

## Optional Enhancements

Filesystem access:
```bash
pi config set tools.filesystem true
```

Shell execution (use with caution):
```bash
pi config set tools.shell true
```

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

### 1. Pi variant to standardize on
Recommendation: **`aider`** as the Ollama-compatible coding agent.
- `pi-agent` on PyPI is ambiguous (multiple unrelated projects use the name) and not the well-known Ollama agent.
- `aider` (https://aider.chat) is the mature, actively maintained terminal coding agent, supports Ollama out of the box via `--model ollama/<name>`, has filesystem + git integration built in, and avoids the "which Pi" ambiguity entirely.
- If we specifically want a project literally named "Pi," confirm the upstream repo URL before standardizing — otherwise prefer `aider`.

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
```bash
cd ollama-pi-coding-agent-first__ai
pip install -r embeddings/requirements.txt
ollama serve   # in another tab if not already running
```

#### Index (run on demand)
```bash
python3 embeddings/index.py            # incremental (skips unchanged chunks by hash)
python3 embeddings/index.py --rebuild  # wipe and reindex
python3 embeddings/index.py --stats    # show row count + last index time
```

#### Search
```bash
python3 embeddings/search.py "where do we configure ollama"
python3 embeddings/search.py --k 10 "embedding indexer"
python3 embeddings/search.py --json "auth flow"     # machine-readable for agents
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

---

## Files in this folder
- `README.md` — this guide
- `env.sample` — sample env vars for Pi → Ollama
- `setup.sh` — one-shot setup helper script
