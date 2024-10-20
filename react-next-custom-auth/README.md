## Created on May 11 2023

# Next Custom Auth in TypeScript
This project was a quick PoC for me to write some clean authentication code so I could easily add it to my other project.
- Next.js
- TypeScript
- React Query (v4) `@tanstack/react-query` 

## Usage
1. open Home page
2. navigate to User profile
3. if logged in, open page
4. if not logged in, open signin page

## Notes
- `_app.tsx` is for adding Global Layout or Meta Tags
- `_document.tsx` is for editing the basic structure of your HTML code
- getStaticProps - build time initialization
- getServerisdeProps - per request server side initialized page

### Steps
- Run `yarn create next-app next-custom-auth-ts --ts --eslint --no-tailwind`
- Save MONGODB_URI after creating database and collection in MongoDB Atlas
- Write backend Next.js serverless functions
  - Add libraries: `yarn add axios cookies-next jsonwebtoken @types/jsonwebtoken mongoose` 
  - `utils.ts` - connect to database and user modal
  - `pages/api/auth/signin.ts`
  - `pages/api/auth/signup.ts`
- Created import alises in tsconfig.json - hooks, components, features
- Write hooks to fetch Next.js serverless functions - [https://dev.to/this-is-learning/react-query-usequery-36i](https://dev.to/this-is-learning/react-query-usequery-36i)
  - `yarn add @tanstack/react-query`
  - `hooks/useSignin.ts`
  - `hooks/useSignup.ts`
  - `hooks/useCurrentUser.ts`
- Write frontend pages
  - `yarn add react-toastify`
  - `yarn add @mui/material @emotion/react @emotion/styled`
  - `pages/_app.tsx`
  - `components/Layout.tsx`
  - `components/ErrorBoundary.tsx`
  - `features/SigninPage.tsx`
  - `features/SignupPage.tsx`
  - `features/HomePage.tsx`
  - `features/UserPage.tsx`
  - `pages/index.tsx`
  - `pages/signin.tsx`
  - `pages/signup.tsx`
  - `pages/user/[id].tsx`
  - Preload data serverside with Next.js `getStaticProps` and React Query useQuery's `initialData`
- Validate build - `npm run build`
- Check bundle size
  - `yarn add -D @next/bundle-analyzer cross-env`
  - add analyze command to package.json - `"analyze": "cross-env ANALYZE=true next build"`
  - `npm run analyze`

### VSCode Shortcuts
- Alt+Shift+F - format
- Alt+Shift+O - optimize imports
- Ctrl+Z and Ctrl+Y (I've spent too much time with that Mac and am clicking Ctrl+Shift+Z now)
- Ctrl+Shift+E - change context to directory structure
- F2 - rename stuff
- Ctrl+. - editor actions
- Ctrl+Shift+P
  - search files
  - run command when `>` is prepended
- Commands
  - TypeScript
    - Remove unused imports
    - Sort Imports
      - note: Sort Imports just sorts alphabetically and not as it should (system, package, and then custom imports)
  - GitLens
    - Toogle Line Blame

### Retro
TypeScript is a pain in the ass with all the request types and refactoring other people's code. The correct way is prob write everything in JS and then add types to working MVP code so I'm not stuck with editing random people's tutorial code while adding types.


# Next.js README
This is a [Next.js](https://nextjs.org/) project bootstrapped with [`create-next-app`](https://github.com/vercel/next.js/tree/canary/packages/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `pages/index.tsx`. The page auto-updates as you edit the file.

[API routes](https://nextjs.org/docs/api-routes/introduction) can be accessed on [http://localhost:3000/api/hello](http://localhost:3000/api/hello). This endpoint can be edited in `pages/api/hello.ts`.

The `pages/api` directory is mapped to `/api/*`. Files in this directory are treated as [API routes](https://nextjs.org/docs/api-routes/introduction) instead of React pages.

This project uses [`next/font`](https://nextjs.org/docs/basic-features/font-optimization) to automatically optimize and load Inter, a custom Google Font.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js/) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/deployment) for more details.
