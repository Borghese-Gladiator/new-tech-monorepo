## December 7th, 2023 1:11 AM

# First Astro.js
Previously I worked with Gatsby, but Astro is the most famous now since it can ship with minimal JavaScript which can speed up time to render significantly.

## Implementation Steps
- [X] bootstrap project
  - ```bash
  npm create astro@latest
  npm run dev
  ```
- Implement
  - [X] product lists page
  - [X] product details page
  - [X] tsconfig.json paths
- [X] deploy to Vercel

### Troubleshooting
- Error: `Cannot find module 'astro:content'`
  - Problem: Empty content folder
  - Solution:
    - Create files ([reference](https://docs.astro.build/en/guides/content-collections/#getcollection))
      - `src/content/config.ts` - defines Product Collection
      - `src/content/product/product-01.md`
      - `src/content/product/product-02.md`
      - `src/content/product/product-03.md`
      - `src/content/product/product-mdx.mdx`
    - Reset TS language server - [reference](https://stackoverflow.com/questions/64454845/where-is-vscodes-restart-ts-server)
    - `npx astro sync`
- Error: `The left-hand side of an arithmetic operation must be of type 'any', 'number' or an enum type`
  - [https://stackoverflow.com/questions/36560806/the-left-hand-side-of-an-arithmetic-operation-must-be-of-type-any-number-or](https://stackoverflow.com/questions/36560806/the-left-hand-side-of-an-arithmetic-operation-must-be-of-type-any-number-or)

### Info
- Astro enables you to use whatever state management library you want (React, Vue, Svelte). Basically an Astro page loads your components.
- 
Astro processes, optimizes, and bundles your src/ files to create the final website that is shipped to the browser. Unlike the static public/ directory, your src/ files are built and handled for you by Astro.

Some files (like Astro components) are not even sent to the browser as written but are instead rendered to static HTML. Other files (like CSS) are sent to the browser but may be optimized or bundled with other CSS files for performance.
### Reference
- [Astro Code Examples](https://github.com/withastro/astro/tree/main/examples)

---
# Astro Starter Kit: Basics

```sh
npm create astro@latest -- --template basics
```

[![Open in StackBlitz](https://developer.stackblitz.com/img/open_in_stackblitz.svg)](https://stackblitz.com/github/withastro/astro/tree/latest/examples/basics)
[![Open with CodeSandbox](https://assets.codesandbox.io/github/button-edit-lime.svg)](https://codesandbox.io/p/sandbox/github/withastro/astro/tree/latest/examples/basics)
[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/withastro/astro?devcontainer_path=.devcontainer/basics/devcontainer.json)

> 🧑‍🚀 **Seasoned astronaut?** Delete this file. Have fun!

![just-the-basics](https://github.com/withastro/astro/assets/2244813/a0a5533c-a856-4198-8470-2d67b1d7c554)

## 🚀 Project Structure

Inside of your Astro project, you'll see the following folders and files:

```text
/
├── public/
│   └── favicon.svg
├── src/
│   ├── components/
│   │   └── Card.astro
│   ├── layouts/
│   │   └── Layout.astro
│   └── pages/
│       └── index.astro
└── package.json
```

Astro looks for `.astro` or `.md` files in the `src/pages/` directory. Each page is exposed as a route based on its file name.

There's nothing special about `src/components/`, but that's where we like to put any Astro/React/Vue/Svelte/Preact components.

Any static assets, like images, can be placed in the `public/` directory.

## 🧞 Commands

All commands are run from the root of the project, from a terminal:

| Command                   | Action                                           |
| :------------------------ | :----------------------------------------------- |
| `npm install`             | Installs dependencies                            |
| `npm run dev`             | Starts local dev server at `localhost:4321`      |
| `npm run build`           | Build your production site to `./dist/`          |
| `npm run preview`         | Preview your build locally, before deploying     |
| `npm run astro ...`       | Run CLI commands like `astro add`, `astro check` |
| `npm run astro -- --help` | Get help using the Astro CLI                     |

## 👀 Want to learn more?

Feel free to check [our documentation](https://docs.astro.build) or jump into our [Discord server](https://astro.build/chat).
