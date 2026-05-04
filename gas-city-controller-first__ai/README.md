# Gas Town First
Gas City is the next-generation successor to Gas Town.

Instead of being a monolithic system, it’s a general-purpose SDK for building agent orchestration systems. Gas City ≈ “Terraform + Kubernetes primitives for agent systems” => Instead of using a prebuilt “town,” you design your own city.

## Features
- declarative city config `city.toml`
- runtime providers - tmux, subprocesses, Kubernetes, etc.
- work routing system
- formulas + orders (task orchestration)
- supervisor loop (desired state -> actual state)
- health patrol (monitoring & recovery)


## Setup
read: https://github.com/gastownhall/gascity/blob/main/docs/getting-started/quickstart.md
- install
  ```
  brew install gastownhall/gascity/gascity
  ```
- fix alias so you can run it
  - open `~/.zshrc`
  - delete usages of `alias gc`
  - if not enough, add `unalias gc unalias gc 2>/dev/null`
    - This fixes `gc` from the default git plugin in Oh My Zsh with iterm2
- run bootstrap script from ChatGPT (note that it'll delete this README)
  ```
  chmod+ bootstrap.sh
  ./bootstrap poker-city
  ```
- create City Controller
  ```
  gc init gas-city-controller-first__ai
  cd gas-city-controller-first__ai
  ```
  - NOTE: City Controller does NOT need an explicit Beads database. Do not run `bd init` inside the city controller
- create City Rig
  ```
  mkdir ~/GitHub/LOCAL_worktrees/202604_gas_city_first__ai/gas-city-rig-first__ai
  gc rig add ~/GitHub/LOCAL_worktrees/202604_gas_city_first__ai/gas-city-rig-first__ai
  ```
  - `gc rig list`
  - `gc rig remove gas-city-rig-first__ai`
- create Beads Database inside Controller
  ```
  gc rig add ~/GitHub/LOCAL_worktrees/202604_gas_city_first__ai/gas-city-controller-first__ai
  bd init --prefix gccfa  # NOTE: use prefix based on the `gc rig` results
  ```
- Sling Work at the rig from inside the controller
  ```
  gc sling claude "Create a script that prints gas city works"
  ```


#### Troubleshooting
<details>
<summary>Wiping and getting a clean slate</summary>


How to build a clean slate
- delete repo
  ```
  rm -rf
  ```
- check for hidden files (eg: `beads`)
  - `ls -la`
  - `rm -rf .beads`
- unregister the cities from gc
  ```
  gc cities
  gc unregister <city_name>
  ```
</details>

<details>
<summary>bd autocommit</summary>

- initialize beads
  ```
  bd init
  ```
  - ensure you click `No` on this option, otherwise, you will get a random WIP commit every 10 minutes
    ```
      Auto-export keeps .beads/issues.jsonl up to date after every write command.
      This is useful for viewers (bv) and git-based sync workflows.

    Enable auto-export? [Y/n]: n
    ```
</details>


# Multiplayer Poker PoC

Stack:
- Next.js web app
- Node.js Socket.IO server
- Drizzle persistence
- TypeScript monorepo
- Playwright-ready browser journeys

Start by implementing:
1. packages/poker-core
2. packages/db
3. apps/server
4. apps/web
5. Playwright journeys


---

# Addendum — End-to-end sling verification (2026-05-04)

This addendum records the working end-to-end sling pipeline and the orphan-bead diagnosis that preceded it. Refer back here whenever `gc sling` fails with `database not initialized` or beads appear to vanish.

## Verified pipeline

A hello-world bead was slung from the controller, picked up by an auto-spawned rig session, implemented, committed, and closed.

```bash
gc --city gas-city-controller-first__ai sling \
  gas-city-rig-first__ai/claude \
  "Create a hello.txt file in the rig root with the contents: hello from gas city"
```

Result:
- Bead `gcrfa-cx5` created in the rig's Dolt DB (`gcrfa`).
- Auto-convoy `gcrfa-7r9` and wisp `gcrfa-z3o` (formula `mol-do-work`) attached.
- Session `hq-bho` (template `gas-city-rig-first__ai/claude`) auto-spawned by the controller. After the first session went idle without closing the bead, the reconciler spawned `hq-4jv` which finished the work.
- `hello.txt` written to the rig root and committed: `d0903a3 feat: add hello.txt to rig root`.
- Bead closed with note: `"Done: Created hello.txt in rig root with 'hello from gas city' content and committed."`

## Beads topology

There is **one** Dolt SQL server (`dolt sql-server`, port 40036) hosting multiple databases. Each `.beads/dolt-server.port` file in both controller and rig points at the same port.

| Location | Database | Prefix | Purpose |
|----------|----------|--------|---------|
| `gas-city-controller-first__ai/.beads/` | `hq` | `hq` | Controller-side beads (orders, runtime, supervisor work) |
| `gas-city-rig-first__ai/.beads/` | `gcrfa` | `gcrfa` | Rig-side application work |

Use `gc bd context` to confirm which database `bd` is talking to from any cwd. The `--rig <name>` flag selects the rig DB; without it, you talk to the controller DB.

## The orphan-bead bug

**Symptom:** `gc sling` failed with `bd create: database not initialized: issue_prefix config is missing (run 'bd init --prefix <prefix>' for a new project, or 'bd bootstrap' to clone an existing remote)`. Beads from earlier slings appeared to be missing.

**Root cause:** the `gcrfa` and `hq` Dolt databases were missing the `issue_prefix` row in the `config` table. `bd bootstrap --yes` printed `Created fresh database with prefix "gcrfa"` but did not actually persist that row to the running Dolt server. Every subsequent `bd create` failed before reaching the bead-creation path.

**Secondary symptom:** the controller has a stale `.gc/beads.json` containing 76 orphaned beads (`gc-1` through `gc-76`) from a previous run that used the JSON backend. The active backend is now Dolt, so those beads are unreachable. They are not loaded by the supervisor, do not appear in `bd list`, and never execute. Safe to delete or archive.

**Fix (idempotent, safe to re-run):**

```bash
# Rig DB
gc --city gas-city-controller-first__ai --rig gas-city-rig-first__ai \
  bd sql "INSERT INTO config (\`key\`, value) VALUES ('issue_prefix', 'gcrfa')"

# Controller DB
gc --city gas-city-controller-first__ai \
  bd sql "INSERT INTO config (\`key\`, value) VALUES ('issue_prefix', 'hq')"
```

Verify:

```bash
gc --city gas-city-controller-first__ai --rig gas-city-rig-first__ai bd config get issue_prefix
# → gcrfa
gc --city gas-city-controller-first__ai bd config get issue_prefix
# → hq
```

After this, `gc sling` works.

## How to verify a sling end-to-end

1. Sling: `gc --city <controller> sling <rig>/claude "<task text>"`. Note the bead id returned (e.g. `gcrfa-cx5`).
2. Confirm bead is in the live Dolt DB (not orphaned in `.gc/beads.json`):

   ```bash
   gc --city <controller> --rig <rig> bd show <bead-id>
   ```

3. Confirm a session was auto-spawned: `gc --city <controller> session list`. Expect a row with template `<rig>/claude` and state `creating` → `active`.
4. Watch for closure: poll `bd show <bead-id> --json` until `status` is `closed`. The reconciler may spawn a follow-up session if the first one goes idle without finishing — this is expected.
5. Verify side effects: the file/commit the bead asked for is in the rig.

## Next steps for the poker PoC

The 8 implementation beads (monorepo skeleton, poker-core, db, shared, server, server verification, web, web verification, Playwright journeys, review) can now be slung the same way. Stale `.gc/beads.json` should be deleted before the run so it doesn't get confused with live beads.

