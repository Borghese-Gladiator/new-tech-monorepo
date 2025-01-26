# NX Monorepo
NX is a powerful build system and development tool designed to help teams manage large-scale monorepos. Developed by Nrwl, it supports modern front-end and back-end technologies, making it easier to scale applications, manage dependencies, and optimize build times.


## Steps to Build
- create empty monorepo
  - `npx create-nx-workspace` (`npx nx init` only adds nx to existing JS/TS projects)
- `npx nx list`
- add REACT frontend
  - `npm i -D @nx/react`
  - `npx nx generate @nx/react:application todo-frontend`
    ```
    NX  Generating @nx/react:application

    √ Which stylesheet format would you like to use? · css
    √ Would you like to add React Router to this application? (y/N) · false
    √ Which bundler do you want to use to build the application? · vite
    √ Which linter would you like to use? · eslint
    √ What unit test runner should be used? · jest
    √ Which E2E test runner would you like to use? · playwright
    ```
  - `npx nx serve todo-frontend`
  - `nx show project todo-frontend`
- add NODE backend
  - `npm install --save-dev @nx/node`
  - `npx nx generate @nx/node:application todo-backend`
  - `npx nx serve todo-backend`
  - `nx show project todo-backend`
  - `nx show project todo-backend-e2`
- add JS library shared utilities
  - `npm install --save-dev @nx/js`
  - `npx nx generate @nx/js:library shared-utils`
---
- todo-frontend - implemented TodoList to call backend
- todo-backend - implemented `/api/todos` to return constants
  - `npm i cors`
  - `npm i --save-dev @types/cors`
  - NOTE: `yarn` will not work (because the root directory uses `package-lock.json`?)

NOTE: `npm install --save-dev @nx/storybook` is for older versions. Use `nx add @nx/storybook` instead.

## Thoughts
NOTE: I wouldn't use this for prod based on errors I'm getting, cuz I get build errors from small changes + can't configure easy stuff like adding a local library.

ERROR: When you install packages inside the subfolder, they bubble up and are added to the parent `package-lock.json` and the child `package.json`. When I added `cors` to todo-backend and used it in `main.ts`, it immediately caused unclear build errors in todo-backend.
```
PS C:\Users\Timot\Documents\GitHub\new-tech-monorepo\nx-monorepo-first\todo-backend> npx nx serve todo-backend

 NX   Running target serve for project todo-backend and 1 task it depends on:

—————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————

> nx run todo-backend:build:production

✘ [ERROR] Could not resolve "todo-backend/src/main.ts"
 NX   Build failed with 1 error:
error: Could not resolve "todo-backend/src/main.ts"
Pass --verbose to see the stacktrace.

—————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————

 NX   Running target serve for project todo-backend and 1 task it depends on failed

Failed tasks:

- todo-backend:build:production

Hint: run the command with --verbose for more details.
```
SOLUTION: `npm install` directly inside NX Monorepo root. Though this is only a drawback for the DEV environment now that I think about it. The DEV environment will have a bloated `node_modules` while building for PROD will properly package each part separately (if they properly remove modules when building).

> Answer: It doesn't effect the size of the compiled code because an app will only include the code it uses thanks to webpack bundling and tree shaking. So there is no risk of D3 showing up in a bundle for an app that doesn't use it. In actuality you could have every npm package listed in your package.json and it wouldn't effect your bundle size. -> https://stackoverflow.com/questions/52761592/include-a-package-for-some-libs-in-nrwl-nx-workspace?rq=4

nrwl/nx is 100% intended to use only one package.json file. Don't try to break it up if you are using nx.

ERROR: Can't load my JavaScript library `shared-utils` into the todo-frontend and todo-backend. I have to fiddle around with `tsconfig.json` and have no idea what I'm doing. I would much rather some sort of CLI command....
```
```
SOLUTION: ??? => I give up, no idea how to configure JSON to pass the types

## Features
1. **Monorepo Support**:
   - Manage multiple projects in a single repository.
   - Share code and dependencies across applications and libraries.

2. **Intelligent Dependency Graph**:
   - Automatically analyzes and visualizes dependencies.
   - Allows selective builds and tests based on changes, reducing CI/CD times.

3. **Built-in Generators and Executors**:
   - Scaffolding tools to generate code quickly.
   - Executors to run custom tasks like builds, tests, or deployments.

4. **Plugin Ecosystem**:
   - Official plugins for frameworks like Angular, React, Node.js, and more.
   - Community plugins for additional support.

5. **Incremental Builds and Caching**:
   - Speeds up builds by caching results and reusing them when possible.
   - Optimized for local and CI environments.

## Concepts
1. **Workspaces**:
   - A workspace is the root directory of an NX monorepo.
   - Contains configuration files (`nx.json`, `workspace.json`, or `project.json`) and all projects.

2. **Projects**:
   - Can be applications or libraries.
   - Applications are typically deployable, while libraries are reusable code shared across projects.

3. **Dependency Graph**:
   - Visualizes relationships between projects.
   - Helps identify which parts of the monorepo are impacted by changes.

4. **Executors and Generators**:
   - **Executors**: Define how tasks like building or testing are executed.
   - **Generators**: Automate repetitive tasks like creating components, modules, or services.

5. **NX Cloud**:
   - Optional cloud-based service for distributed caching and task orchestration.
   - Useful for optimizing CI pipelines.

## Usage
Set Up NX
1. **Install NX CLI**:
   ```bash
   npx create-nx-workspace@latest
   ```

2. **Create a New Workspace**:
   Choose a preset based on your needs:
   - Integrated monorepo with a specific framework.
   - Empty workspace for custom setups.

3. **Add a Project**:
   Use built-in generators to add projects:
   ```bash
   nx generate @nrwl/react:application my-app
   nx generate @nrwl/node:application my-api
   ```

4. **Run Tasks**:
   Execute tasks like building or testing:
   ```bash
   nx build my-app
   nx test my-app
   ```

5. **View Dependency Graph**:
   Visualize project dependencies:
   ```bash
   nx graph
   ```

Commands
- **Generate a Library**:
  ```bash
  nx generate @nrwl/react:library shared-ui
  ```

- **Run Linting**:
  ```bash
  nx lint my-app
  ```

- **Run Tests**:
  ```bash
  nx test my-app
  ```

- **Serve Applications**:
  ```bash
  nx serve my-app
  ```

- **Affected Projects**:
  Run tasks only for projects affected by recent changes:
  ```bash
  nx affected:build
  ```


---
# NX Default README

<a alt="Nx logo" href="https://nx.dev" target="_blank" rel="noreferrer"><img src="https://raw.githubusercontent.com/nrwl/nx/master/images/nx-logo.png" width="45"></a>

✨ Your new, shiny [Nx workspace](https://nx.dev) is ready ✨.

[Learn more about this workspace setup and its capabilities](https://nx.dev/nx-api/js?utm_source=nx_project&amp;utm_medium=readme&amp;utm_campaign=nx_projects) or run `npx nx graph` to visually explore what was created. Now, let's get you up to speed!

## Generate a library

```sh
npx nx g @nx/js:lib packages/pkg1 --publishable --importPath=@my-org/pkg1
```

## Run tasks

To build the library use:

```sh
npx nx build pkg1
```

To run any task with Nx use:

```sh
npx nx <target> <project-name>
```

These targets are either [inferred automatically](https://nx.dev/concepts/inferred-tasks?utm_source=nx_project&utm_medium=readme&utm_campaign=nx_projects) or defined in the `project.json` or `package.json` files.

[More about running tasks in the docs &raquo;](https://nx.dev/features/run-tasks?utm_source=nx_project&utm_medium=readme&utm_campaign=nx_projects)

## Versioning and releasing

To version and release the library use

```
npx nx release
```

Pass `--dry-run` to see what would happen without actually releasing the library.

[Learn more about Nx release &raquo;](hhttps://nx.dev/features/manage-releases?utm_source=nx_project&utm_medium=readme&utm_campaign=nx_projects)

## Keep TypeScript project references up to date

Nx automatically updates TypeScript [project references](https://www.typescriptlang.org/docs/handbook/project-references.html) in `tsconfig.json` files to ensure they remain accurate based on your project dependencies (`import` or `require` statements). This sync is automatically done when running tasks such as `build` or `typecheck`, which require updated references to function correctly.

To manually trigger the process to sync the project graph dependencies information to the TypeScript project references, run the following command:

```sh
npx nx sync
```

You can enforce that the TypeScript project references are always in the correct state when running in CI by adding a step to your CI job configuration that runs the following command:

```sh
npx nx sync:check
```

[Learn more about nx sync](https://nx.dev/reference/nx-commands#sync)

## Set up CI!

### Step 1

To connect to Nx Cloud, run the following command:

```sh
npx nx connect
```

Connecting to Nx Cloud ensures a [fast and scalable CI](https://nx.dev/ci/intro/why-nx-cloud?utm_source=nx_project&utm_medium=readme&utm_campaign=nx_projects) pipeline. It includes features such as:

- [Remote caching](https://nx.dev/ci/features/remote-cache?utm_source=nx_project&utm_medium=readme&utm_campaign=nx_projects)
- [Task distribution across multiple machines](https://nx.dev/ci/features/distribute-task-execution?utm_source=nx_project&utm_medium=readme&utm_campaign=nx_projects)
- [Automated e2e test splitting](https://nx.dev/ci/features/split-e2e-tasks?utm_source=nx_project&utm_medium=readme&utm_campaign=nx_projects)
- [Task flakiness detection and rerunning](https://nx.dev/ci/features/flaky-tasks?utm_source=nx_project&utm_medium=readme&utm_campaign=nx_projects)

### Step 2

Use the following command to configure a CI workflow for your workspace:

```sh
npx nx g ci-workflow
```

[Learn more about Nx on CI](https://nx.dev/ci/intro/ci-with-nx#ready-get-started-with-your-provider?utm_source=nx_project&utm_medium=readme&utm_campaign=nx_projects)

## Install Nx Console

Nx Console is an editor extension that enriches your developer experience. It lets you run tasks, generate code, and improves code autocompletion in your IDE. It is available for VSCode and IntelliJ.

[Install Nx Console &raquo;](https://nx.dev/getting-started/editor-setup?utm_source=nx_project&utm_medium=readme&utm_campaign=nx_projects)

## Useful links

Learn more:

- [Learn more about this workspace setup](https://nx.dev/nx-api/js?utm_source=nx_project&amp;utm_medium=readme&amp;utm_campaign=nx_projects)
- [Learn about Nx on CI](https://nx.dev/ci/intro/ci-with-nx?utm_source=nx_project&utm_medium=readme&utm_campaign=nx_projects)
- [Releasing Packages with Nx release](https://nx.dev/features/manage-releases?utm_source=nx_project&utm_medium=readme&utm_campaign=nx_projects)
- [What are Nx plugins?](https://nx.dev/concepts/nx-plugins?utm_source=nx_project&utm_medium=readme&utm_campaign=nx_projects)

And join the Nx community:
- [Discord](https://go.nx.dev/community)
- [Follow us on X](https://twitter.com/nxdevtools) or [LinkedIn](https://www.linkedin.com/company/nrwl)
- [Our Youtube channel](https://www.youtube.com/@nxdevtools)
- [Our blog](https://nx.dev/blog?utm_source=nx_project&utm_medium=readme&utm_campaign=nx_projects)
