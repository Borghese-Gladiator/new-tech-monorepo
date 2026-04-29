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


