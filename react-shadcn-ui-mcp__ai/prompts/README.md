
# React ShadCN AI First
This is to test generating UIs with ShadCN UI MCP.

Summary:
- generated Next.js app with TailwindCSS
- initialized ShadCN
- set up MCP Server with shadcn-ui
  - generate GitHub API token
  - add MCP Server via command: `@jpisnice/shadcn-ui-mcp-server --github-api-key <api-key> --framework react`
- generated random app with login/signup/dashboard pages

## Bootstrap Steps
- initialize Next.js app (WITH TailwindCSS and Page Router)
  ```
  npx create-next-app@latest react-shadcn-ai-first
  ```
- initialize ShadCN
  ```
  npx shadcn@latest init
  ```
- add components
  ```
  npx shadcn@latest add button card input label textarea
  npx shadcn@latest add select badge dialog dropdown-menu calendar
  npx shadcn@latest add table form progress skeleton
  npx shadcn@latest add sonner  # replaced toast
  ```
- set up provider
  ```
  // pages/_app.tsx
  import type { AppProps } from "next/app";
  import "@/styles/globals.css";
  import { Toaster } from "@/components/ui/sonner"; // new sonner toaster

  export default function App({ Component, pageProps }: AppProps) {
    return (
      <>
        <Component {...pageProps} />
        <Toaster />
      </>
    );
  }

  ```
- set up PWA (service worker generation, registration, manifest wiring)
  ```
  npm install @serwist/next  # successor to next-pwa
  npm install -D serwist
  ```
  - update next.config
    ```
    // next.config.js
    const { withSerwist } = require("@serwist/next");

    module.exports = withSerwist({
      // your normal Next config here
      serwist: {
        swSrc: "public/sw.js",   // we'll create this
        // register: true by default (auto SW register)
      },
    });

    ```
    -
  - update manifest
    ```
    {
      "name": "Diet Tracker",
      "short_name": "Diet",
      "start_url": "/",
      "display": "standalone",
      "background_color": "#0B0B0B",
      "theme_color": "#0B0B0B",
      "description": "Track meals, calories, and macros—fast.",
      "icons": [
        { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
        { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png" }
      ]
    }

    ```
  - add to `<Head>` in `_app.tsx`
    ```
    import Head from "next/head";
    // ...
    <>
      <Head>
        <link rel="manifest" href="/manifest.webmanifest" />
        <meta name="theme-color" content="#0B0B0B" />
      </Head>
      {/* ... */}
    </>

    ```
  - https://serwist.pages.dev/docs/next/getting-started?utm_source=chatgpt.com
- Created `impl-plan-shadcn-mcp.md`
  ```
  ## ShadCN + MCP Ruleset

  description: >
    Smart ruleset for planning and building with ShadCN UI, powered by the MCP server.
    Ensures clean UI architecture, consistent usage, and error-free implementation with full context.

  globs:
    - "**/*.tsx"

  alwaysApply: false

  ---

  ## Component Usage Rule
  - Whenever a ShadCN component is requested, route through the MCP server first.
  - This ensures:
    - Context-aware patterns
    - Consistent styling
    - Prevention of broken implementations

  ---

  ## Planning Rule
  When generating or revising UI plans that involve ShadCN:
  - Use the MCP server to provide structure and UX flow.
  - Prioritize component usage where atomic UI pieces are needed.
    - Prefer full UI blocks (e.g. login, dashboard, calendar) when available.
  - Treat MCP output as the source of truth for layout and flow decisions.

  ---

  ## Implementation Rule
  When implementing ShadCN components in code:
  1. Always begin by calling `getComponentDemo` to pull correct usage examples.
  2. Mirror the implementation pattern shown in the demo exactly.
     - Use the demo as a context snapshot.
     - Do not improvise unless required.
  3. For multi-component flows (e.g. forms, modals, auth flows), check if a **Block** exists before composing manually.

  ```
- Ran prompt in VSCode Agent mode while `impl-plan-shadcn-mcp.md` was the actively selected tab (so it'd be included in context)
  ```
  I want to build a modern web interface using ShadCN components.
  Goal:
  - A login page with standard email/password authentication.
  - After login, a dashboard displays a grid of cards — each representing an MCP server.
  - Clicking a card opens a detailed view with:
    - A header image
    - Metadata (name, status, region, version)
    - Installation steps shown as bubble cards or collapsible UI
  Please generate an implementation plan:
  - List the key components and pages to build
  - Suggest how to structure the project modularly
  - Recommend the tools/hooks/layout strategies to use for optimal UX
  
  Create a UI implementation outline using ShadCN UI. Save this implementation outline to a markdown file. 
  ```
- Run prompt to implement:
  ```
  implement the included plan called "Implementation Plan"
  ```
- Run prompt to connect home to frontend
  ```
  I want to build a home page that connects to the other pages. 
  
  Ensure it's connected to:
  - login page
  - dashboard page
  - server detail page
  
  Write the results to a local markdown file
  ```
- Run prompt to implement:
  ```
  implement the included plan called "Home Page UI Plan"
  ```
- Run prompt to style:
  ```
  use TweakCN to theme all the components with aquamarine. I want the typography to be different for each type of text (eg: header vs paragraph)
  ```

## Findings
Cons
- As you prompt more and more, the results get worse and worse (lol) -> 3 times is the limit imo
- ENSURE the VSCode (or other) Agent uses the MCP Tools and does not try to just generate its own version. 
- Short phrase words do NOT work for theming (eg: make a aquamarine theme OR make a theme for "Futuristic / Techy – gradients, geometric shapes, neon." and apply it on all pages)

Pros
- very cool to use it generate so many shadcn components so quickly

<details>

<summary>Next.js README</summary>

This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/pages/api-reference/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `pages/index.tsx`. The page auto-updates as you edit the file.

[API routes](https://nextjs.org/docs/pages/building-your-application/routing/api-routes) can be accessed on [http://localhost:3000/api/hello](http://localhost:3000/api/hello). This endpoint can be edited in `pages/api/hello.ts`.

The `pages/api` directory is mapped to `/api/*`. Files in this directory are treated as [API routes](https://nextjs.org/docs/pages/building-your-application/routing/api-routes) instead of React pages.

This project uses [`next/font`](https://nextjs.org/docs/pages/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn-pages-router) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/pages/building-your-application/deploying) for more details.

</details>