# First Deno Project
Deno 2 was just released and it now supports node_modules! Therefore, I'm taking another look at using Deno. (ty Fireship for re-introducing it to me: [https://www.youtube.com/watch?v=pcC4Dr6Wj2Q](https://www.youtube.com/watch?v=pcC4Dr6Wj2Q))

Features I Like
- Standard Library of Utils
- Juypter Notebook integration

## Local Setup
Windows
```powershell
choco install deno
```

## Local Commands
```
deno run --allow-read .\main.ts
deno run --allow-net server.ts
deno test tests/**/*.ts
```

# Notes
Things I Want to Try
- [X] add standard libraries => `deno add jsr:@std/path`
- [X] run API server
- [X] run unit tests
- [ ] setup Juypter Notebook w/ Deno

## Bootstrap Commands
```
mkdir first-deno && cd first-deno

deno init
deno main.ts
deno test

# VSCode Setup
## install Deno extension - https://marketplace.visualstudio.com/items?itemName=denoland.vscode-deno
## run "Deno: Initialize workspace Configuration"

# Package installation
deno add jsr:@luca/cases

# Jupyter Notebook setup
## pip install notebook  # assumes `jupyter` is availabled
deno jupyter --install
## create notebook - Create: New Jupyter Notebook
## set kernel - Notebook: Select Notebook Kernel | Deno
```

## Security and permissions
- Environment access - `--allow-env`
- File System Read Access - `--allow-read[=<PATH>...]`
- File System Write Access - `--allow-write[=<PATH>...]`
- Network Access - `--allow-net[=<IP_OR_HOSTNAME>...]`
- System Information - `--allow-sys[=<API_NAME>...]`
- Running Subprocesses - `--allow-run[=<PROGRAM_NAME>...]`
- FFI (Foreign Function Interface) - `--allow-ffi[=<PATH>...]`

## Reference
Running code
```
# run online script
deno run https://docs.deno.com/examples/hello-world.ts

## run online GitHub code
deno run https://raw.githubusercontent.com/denoland/docs/refs/heads/main/examples/hello-world.ts

## run online custom GitHub Gist code
#### create gist - https://gist.github.com/Borghese-Gladiator/cc05d1ca05ede876a8f5d5264a1aabab
deno run https://gist.github.com/Borghese-Gladiator/cc05d1ca05ede876a8f5d5264a1aabab

# Script Arguments
deno run main.ts arg1 arg2 arg3

# Argument and flag ordering
deno run --allow-net net_client.ts
deno run --watch main.ts
deno test --watch
deno fmt --watch
deno run --watch --watch-exclude=file1.ts,file2.ts main.ts
deno run --watch --watch-exclude='*.js' main.ts
deno run --watch-hmr main.ts

# Type checking
deno check main.ts
```

Useful commands
```
deno fmt
deno install
deno run
deno test
deno doc
deno compile   # builds .exe
```

Package Versioning
```
@scopename/mypackage           # highest version
@scopename/mypackage@16.1.0    # exact version
@scopename/mypackage@16        # highest 16.x version >= 16.0.0
@scopename/mypackage@^16.1.0   # highest 16.x version >= 16.1.0
@scopename/mypackage@~16.1.0   # highest 16.1.x version >= 16.1.0
```

Deno Help
```
PS C:\Users\Timot\Documents\GitHub\first-deno> deno help
Deno: A modern JavaScript and TypeScript runtime

Usage: deno [OPTIONS] [COMMAND]

Commands:
  Execution:
    run          Run a JavaScript or TypeScript program, or a task
                  deno run main.ts  |  deno run --allow-net=google.com main.ts  |  deno main.ts
    serve        Run a server
                  deno serve main.ts
    task         Run a task defined in the configuration file
                  deno task dev
    repl         Start an interactive Read-Eval-Print Loop (REPL) for Deno
    eval         Evaluate a script from the command line

  Dependency management:
    add          Add dependencies
                  deno add @std/assert  |  deno add npm:express
    install      Install script as an executable
    uninstall    Uninstall a script previously installed with deno install
    remove       Remove dependencies from the configuration file

  Tooling:
    bench        Run benchmarks
                  deno bench bench.ts
    cache        Cache the dependencies
    check        Type-check the dependencies
    compile      Compile the script into a self contained executable
                  deno compile main.ts  |  deno compile --target=x86_64-unknown-linux-gnu
    coverage     Print coverage reports
    doc          Genereate and show documentation for a module or built-ins
                  deno doc  |  deno doc --json  |  deno doc --html mod.ts
    fmt          Format source files
                  deno fmt  |  deno fmt main.ts
    info         Show info about cache or info related to source file
    jupyter      Deno kernel for Jupyter notebooks
    lint         Lint source files
    init         Initialize a new project
    test         Run tests
                  deno test  |  deno test test.ts
    publish      Publish the current working directory's package or workspace
    upgrade      Upgrade deno executable to given version
                  deno upgrade  |  deno upgrade 1.45.0  |  deno upgrade canary


Environment variables:
  DENO_AUTH_TOKENS      A semi-colon separated list of bearer tokens and hostnames
                        to use when fetching remote modules from private repositories
                         (e.g. "abcde12345@deno.land;54321edcba@github.com")
  DENO_FUTURE           Set to "1" to enable APIs that will take effect in Deno 2
  DENO_CERT             Load certificate authorities from PEM encoded file
  DENO_DIR              Set the cache directory
  DENO_INSTALL_ROOT     Set deno install's output directory
                         (defaults to $HOME/.deno/bin)
  DENO_NO_PACKAGE_JSON  Disables auto-resolution of package.json
  DENO_NO_UPDATE_CHECK  Set to disable checking if a newer Deno version is available
  DENO_TLS_CA_STORE     Comma-separated list of order dependent certificate stores.
                        Possible values: "system", "mozilla".
                         (defaults to "mozilla")
  HTTP_PROXY            Proxy address for HTTP requests
                         (module downloads, fetch)
  HTTPS_PROXY           Proxy address for HTTPS requests
                         (module downloads, fetch)
  NO_COLOR              Set to disable color
  NO_PROXY              Comma-separated list of hosts which do not use a proxy
                         (module downloads, fetch)
  NPM_CONFIG_REGISTRY   URL to use for the npm registry.

Docs: https://docs.deno.com
Standard Library: https://jsr.io/@std
Bugs: https://github.com/denoland/deno/issues
```
