# Chrome DevTools MCP — Setup Guide

Connect Chrome DevTools to an AI client (Claude Desktop, ChatGPT Desktop, Claude Code, etc.) via the **Model Context Protocol (MCP)** so the AI can inspect the DOM, debug network/console, analyze performance, and drive the browser.

```
AI Agent  ⇄  MCP  ⇄  Chrome DevTools Protocol  ⇄  Browser
```

---

## Prerequisites

- **Node.js ≥ 18** — verify: `node -v`
- **Google Chrome** installed
- **An MCP-compatible client** (Claude Desktop, ChatGPT Desktop, Claude Code, etc.)

---

## Step 1 — Install the MCP server

```bash
npm install -g chrome-devtools-mcp
chrome-devtools-mcp --help
```

---

## Step 2 — Launch Chrome with remote debugging

This opens a **separate** Chrome session dedicated to debugging (uses an isolated user profile).

**macOS** — use the helper script in this folder:
```bash
./launch-chrome-debug.sh
```

Or run manually:
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-devtools
```

**Windows:**
```bat
"C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --user-data-dir=C:\temp\chrome-devtools
```

**Linux:**
```bash
google-chrome \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-devtools
```

Verify it's listening: open <http://localhost:9222/json> — you should see a JSON list of tabs.

---

## Step 3 — Start the MCP server

```bash
chrome-devtools-mcp
```

Defaults: connects to `http://localhost:9222` and exposes DevTools over MCP.

Custom port / Chrome URL:
```bash
chrome-devtools-mcp --port 3001 --chrome-url http://localhost:9222
```

---

## Step 4 — Register the server in your MCP client

See `mcp-config.example.json` in this folder. Drop the `mcpServers.chrome-devtools` block into your client's config:

- **Claude Desktop (macOS):** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Claude Desktop (Windows):** `%APPDATA%\Claude\claude_desktop_config.json`
- **Claude Code:** `~/.claude/settings.json` (or project-level `.claude/settings.json`)

If the client needs an absolute path, use the output of `which chrome-devtools-mcp`.

---

## Step 5 — Restart the MCP client

Fully quit and relaunch the client so it picks up the new config.

---

## Step 6 — Open a page in the debug Chrome instance

In the Chrome window launched in Step 2, navigate to any site you want to inspect (e.g., `http://localhost:3000`).

---

## Step 7 — Drive it from the AI

Try prompts like:
- "List all open tabs in Chrome"
- "Inspect the DOM and explain this layout issue"
- "Why is this API call failing?"
- "Show console errors on the current page"
- "Find performance bottlenecks"
- "Click the login button and capture the network requests"

---

## Step 8 — Verify it's wired up

Smoke test prompt:
> "List open tabs"

If the AI returns real tab data from the debug Chrome session, you're connected.

---

## Troubleshooting

**"Cannot connect to Chrome"**
- Confirm Chrome is running with `--remote-debugging-port=9222`
- Hit <http://localhost:9222/json> — should return a tab list

**MCP client doesn't see the server**
- Fully restart the client
- Validate the config JSON (trailing commas, quotes)
- Use an absolute path for `command`

**Permission denied on the binary**
```bash
chmod +x "$(which chrome-devtools-mcp)"
```

**Port already in use**
- Pick a different `--remote-debugging-port` and pass `--chrome-url` to the MCP server to match

---

## Files in this folder

- `README.md` — this guide
- `mcp-config.example.json` — drop-in config snippet for MCP clients
- `launch-chrome-debug.sh` — macOS helper to start Chrome with debugging enabled

---

## Going further

- Script automated debugging workflows (record → replay)
- Wire it to a local React/Next dev server for live inspection
- Build custom MCP tools on top of the DevTools Protocol

---

## Addendum — Local setup findings (2026-05-04)

Notes captured while wiring this up on macOS with `fnm`-managed Node.

### Environment

- Node v22.17.1 via `fnm` (default alias)
- Chrome 147.0.7727.138
- Claude Code as the MCP client

### `which` returns an unstable path under fnm

`npm install -g chrome-devtools-mcp` lands the binary in fnm's per-shell multishell dir, e.g.:

```
/Users/<user>/.local/state/fnm_multishells/<PID>_<TS>/bin/chrome-devtools-mcp
```

That path is **shell-session scoped** — when Claude Code restarts, the shell PID/timestamp segment goes away and the path 404s. Don't paste this into MCP config.

**Use the fnm `default` alias path instead** — it's a real symlink and survives sessions:

```
/Users/<user>/.local/share/fnm/aliases/default/bin/chrome-devtools-mcp
```

### Registering with Claude Code

Skip JSON editing — use the CLI:

```bash
claude mcp add chrome-devtools /Users/<user>/.local/share/fnm/aliases/default/bin/chrome-devtools-mcp
```

This writes a `local`-scope entry into `~/.claude.json` for the current project only. Verify with:

```bash
claude mcp list | grep chrome
```

Expected: `chrome-devtools: <abs-path>  - ✓ Connected`.

**The current Claude Code session must be fully restarted** to load the new tool schemas — registering does not retroactively expose tools to a running session.

### Chrome lifecycle gotcha

Launching the debug Chrome via `./launch-chrome-debug.sh` from inside Claude Code as a backgrounded task ties Chrome's lifetime to the Claude session — closing/restarting Claude kills Chrome.

For a debug Chrome that survives Claude restarts (which you'll need, since the restart is part of the registration flow), launch the script from a **separate terminal window** outside Claude Code.

### Verification commands

```bash
# Chrome debug endpoint health
curl -s http://localhost:9222/json/version

# Confirm MCP server is connected
claude mcp list | grep chrome
```

### Tool surface (post-restart)

Once Claude Code reloads, the `chrome-devtools` MCP exposes tools under the `mcp__chrome-devtools__*` namespace, including:

- Page control: `list_pages`, `new_page`, `select_page`, `navigate_page`, `close_page`
- Interaction: `click`, `fill`, `fill_form`, `hover`, `type_text`, `press_key`, `drag`, `upload_file`, `select_option` (via `fill_form`)
- Inspection: `take_snapshot`, `take_screenshot`, `evaluate_script`
- Diagnostics: `list_console_messages`, `get_console_message`, `list_network_requests`, `get_network_request`
- Performance: `performance_start_trace`, `performance_stop_trace`, `performance_analyze_insight`, `lighthouse_audit`, `take_memory_snapshot`
- Misc: `emulate`, `resize_page`, `wait_for`, `handle_dialog`

---

## Addendum — End-to-end verification (2026-05-05)

Confirmed the full path **Claude Code → MCP → CDP → Chrome** with live tool calls, not just a handshake.

### What was verified

1. **Chrome launched in background** via `launch-chrome-debug.sh` from inside the Claude Code session (backgrounded Bash task). Reachable at `http://localhost:9222/json/version` → `Chrome/147.0.7727.138`.
2. **Five MCP tools exercised against the running browser:**

   | Tool | Result |
   |---|---|
   | `list_pages` | returned the initial `about:blank` tab |
   | `new_page` (`https://example.com`) | new tab opened and auto-selected |
   | `take_snapshot` | a11y tree returned (`RootWebArea "Example Domain"`, h1, link) |
   | `evaluate_script` | `{title:"Example Domain", url:"https://example.com/", h1:"Example Domain"}` |
   | `list_console_messages` | captured a 404 (favicon) |

3. **Chrome stopped** by killing the background task — clean teardown.

### Caveat from the earlier addendum, now refined

The previous note said the debug Chrome must be launched from a separate terminal so it survives Claude Code restarts. That's still true **for the registration flow** (where you have to restart Claude Code to load tool schemas).

For *ad-hoc* validation in an already-registered session, launching Chrome as a backgrounded Bash task inside Claude Code works fine — just accept that Chrome dies when the session (or the task) ends. Use whichever mode matches your need:

- **Registering / changing MCP config:** launch Chrome from a separate terminal (survives Claude restart).
- **One-shot validation in an existing session:** background-launch from inside Claude Code (auto-cleanup at session end).

### Verdict

The flow works end-to-end. The MCP server is correctly wired, tools are reachable, and the round-trip (Claude → tool call → CDP → page state → response) is functional.

---

## Conclusion — chrome-devtools MCP vs. Playwright MCP

### Two demos that show where this MCP earns its keep

**Demo 1 — Live debug a real bug (DevTools' sweet spot)**
Open a dev/staging page in the debug Chrome, then use the MCP to:
- pull `list_console_messages` for errors
- pull `list_network_requests`, filter to failing/slow XHRs, drill in with `get_network_request`
- run `lighthouse_audit` for a perf snapshot

This is the demo where DevTools beats Playwright — *diagnostic depth* on a page a human is already looking at, no script authoring required.

**Demo 2 — Auto-validate a feature end-to-end (overlaps with Playwright)**
Pick a small flow (e.g., load a page, click a known control, assert a network call fires + no console errors). Drive it via `navigate_page` → `click` → `wait_for` → `list_network_requests` → `list_console_messages`.

This is the demo that exposes whether DevTools MCP is *additive* or *redundant* vs. Playwright for the auto-validation goal.

### Should it be added globally?

**Recommendation: keep it project-local, not global.** Reasons:

- Playwright MCP is already registered globally and is the better fit for *automated feature validation* (the stated goal): deterministic selectors, auto-waits, headless, suited to CI. DevTools MCP is weaker here — it's an interactive debugger surface, not a test runner.
- DevTools MCP's real edge is **diagnostic on a live page** (real console, real network, lighthouse, perf traces, memory snapshots). That's a **complement** to Playwright, not a replacement.
- The fnm-default `command` path is stable on this machine, but a global config baked with that path will not transfer cleanly to other machines or to CI.

### Suggested split of responsibilities

| Use case | Tool |
|---|---|
| Repeatable feature validation, regression checks, anything to be re-run | **Playwright (global)** |
| Ad-hoc "why is this page broken" investigations, perf/lighthouse work, network/console deep-dives on live sessions | **chrome-devtools (project-local)** |

Revisit globalizing `chrome-devtools` only if it gets reached for across multiple repos *and* the diagnostic use case starts to dominate over scripted validation.
