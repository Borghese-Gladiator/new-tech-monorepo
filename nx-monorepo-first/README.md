# NX Monorepo
NX is a powerful build system and development tool designed to help teams manage large-scale monorepos. Developed by Nrwl, it supports modern front-end and back-end technologies, making it easier to scale applications, manage dependencies, and optimize build times.


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

---

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