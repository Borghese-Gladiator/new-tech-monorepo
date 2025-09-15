# First RedwoodJS
Redwood is the full-stack web framework designed to help you grow from side project to startup. It comes with lots of pre-installed packages and configuration that makes it easy to build full-stack web applications.

Opinionated libraries that come by default
- GraphQL
- Prisma
- Jest
- Storybook
- vite
- Babel
- Typescript


## Steps
[Official Tutorial](https://docs.redwoodjs.com/docs/tutorial/chapter1/file-structure)
NOTE: stopped here: https://docs.redwoodjs.com/docs/tutorial/chapter2/getting-dynamic

- `yarn create redwood-app js-redwood-first` - old monorepo code made this fail with wrong node version
- `npx -y create-redwood-app@latest js-redwood-first`
- `yarn install`
  - error
    ```
    error This project's package.json defines "packageManager": "yarn@4.6.0". However the current global version of Yarn is 1.22.22.

    Presence of the "packageManager" field indicates that the project is meant to be used with Corepack, a tool included by default with all official Node.js distributions starting from 16.9 and 14.19.
    Corepack must currently be enabled by running corepack enable in your terminal. For more information, check out https://yarnpkg.com/corepack.
    ```
  - `corepack enable`
- `yarn run rw dev`
- `yarn rw generate page home /`
- `yarn rw generate page about`
- `yarn rw generate layout blog`

## Notes

Redwood commands
```
Commands:
  rw build [side..]          Build for production
  rw check                   Get structural diagnostics for a Redwood project
                             (experimental)               [aliases: diagnostics]
  rw console                 Launch an interactive Redwood shell (experimental)
                                                                    [aliases: c]
  rw deploy <target>         Deploy your Redwood project
  rw destroy <type>          Rollback changes made by the generate command
                                                                    [aliases: d]
  rw dev [side..]            Start development servers for api, and web
  rw exec [name]             Run scripts generated with yarn generate script
  rw experimental <command>  Run or setup experimental features   [aliases: exp]
  rw generate <type>         Generate boilerplate code and type definitions
                                                                    [aliases: g]
  rw info                    Print your system environment information
  rw jobs                    Starts the RedwoodJob runner to process background
                             jobs
  rw lint [path..]           Lint your files
  rw prerender               Prerender pages of your Redwood app at build time
                                                               [aliases: render]
  rw prisma [commands..]     Run Prisma CLI with experimental features
  rw record <command>        Setup RedwoodRecord for your project. Caches a JSON
                             version of your data model and adds
                             api/src/models/index.js with some config.
  rw serve [side]            Start a server for serving both the api and web
                             sides
  rw setup <command>         Initialize project config and install packages
  rw studio                  Run the Redwood development studio
  rw test [filter..]         Run Jest tests. Defaults to watch mode
  rw ts-to-js                [DEPRECATED]
                             Convert a TypeScript project to JavaScript
  rw type-check [sides..]    Run a TypeScript compiler check on your project
                                                              [aliases: tsc, tc]
  rw upgrade                 Upgrade all @redwoodjs packages via interactive CLI
  rw storybook               Launch Storybook: a tool for building UI components
                             and pages in isolation                [aliases: sb]
  rw data-migrate <command>  Migrate the data in your database
                                                      [aliases: dataMigrate, dm]

Options:
      --cwd             Working directory to use (where `redwood.toml` is
                        located)
      --load-env-files  Load additional .env files. Values defined in files
                        specified later override earlier ones.           [array]
      --telemetry       Whether to send anonymous usage telemetry to RedwoodJS
                                                                       [boolean]
      --version         Show version number                            [boolean]
  -h, --help            Show help                                      [boolean]

Examples:
  yarn rw exec migrateUsers                 Run a script, also loading env vars
  --load-env-files stripe nakama            from '.env.stripe' and '.env.nakama'
  yarn rw g page home /                     Create a page component named 'Home'
                                            at path '/'

Not enough non-option arguments: got 0, need at least 1
```

RedwoodJS has everything for Day 0. For Day 100, you add the other components yourself

For example:
- Structured logging - `@redwood/logger`
- Error Monitoring - they use Sentry
- Background jobs / cron / queues

#### Missing Features
Redwood is in active development and missing:
- React Server Components and a new transparent, non-GraphQL API
- SSR/Streaming
- Realtime and GraphQL Subscriptions
- Redwood Studio for getting runtime insights into your project
- Mailer

They are also missing:
- OpenTelemetry - only an experiemtanal integration


<details>
<summary>Default README</summary>


# README

Welcome to [RedwoodJS](https://redwoodjs.com)!

> **Prerequisites**
>
> - Redwood requires [Node.js](https://nodejs.org/en/) (=20.x) and [Yarn](https://yarnpkg.com/)
> - Are you on Windows? For best results, follow our [Windows development setup](https://redwoodjs.com/docs/how-to/windows-development-setup) guide

Start by installing dependencies:

```
yarn install
```

Then start the development server:

```
yarn redwood dev
```

Your browser should automatically open to [http://localhost:8910](http://localhost:8910) where you'll see the Welcome Page, which links out to many great resources.

> **The Redwood CLI**
>
> Congratulations on running your first Redwood CLI command! From dev to deploy, the CLI is with you the whole way. And there's quite a few commands at your disposal:
>
> ```
> yarn redwood --help
> ```
>
> For all the details, see the [CLI reference](https://redwoodjs.com/docs/cli-commands).

## Prisma and the database

Redwood wouldn't be a full-stack framework without a database. It all starts with the schema. Open the [`schema.prisma`](api/db/schema.prisma) file in `api/db` and replace the `UserExample` model with the following `Post` model:

```prisma
model Post {
  id        Int      @id @default(autoincrement())
  title     String
  body      String
  createdAt DateTime @default(now())
}
```

Redwood uses [Prisma](https://www.prisma.io/), a next-gen Node.js and TypeScript ORM, to talk to the database. Prisma's schema offers a declarative way of defining your app's data models. And Prisma [Migrate](https://www.prisma.io/migrate) uses that schema to make database migrations hassle-free:

```
yarn rw prisma migrate dev

# ...

? Enter a name for the new migration: › create posts
```

> `rw` is short for `redwood`

You'll be prompted for the name of your migration. `create posts` will do.

Now let's generate everything we need to perform all the CRUD (Create, Retrieve, Update, Delete) actions on our `Post` model:

```
yarn redwood generate scaffold post
```

Navigate to [http://localhost:8910/posts/new](http://localhost:8910/posts/new), fill in the title and body, and click "Save".

Did we just create a post in the database? Yup! With `yarn rw generate scaffold <model>`, Redwood created all the pages, components, and services necessary to perform all CRUD actions on our posts table.

## Frontend first with Storybook

Don't know what your data models look like? That's more than ok—Redwood integrates Storybook so that you can work on design without worrying about data. Mockup, build, and verify your React components, even in complete isolation from the backend:

```
yarn rw storybook
```

Seeing "Couldn't find any stories"? That's because you need a `*.stories.{tsx,jsx}` file. The Redwood CLI makes getting one easy enough—try generating a [Cell](https://redwoodjs.com/docs/cells), Redwood's data-fetching abstraction:

```
yarn rw generate cell examplePosts
```

The Storybook server should hot reload and now you'll have four stories to work with. They'll probably look a little bland since there's no styling. See if the Redwood CLI's `setup ui` command has your favorite styling library:

```
yarn rw setup ui --help
```

## Testing with Jest

It'd be hard to scale from side project to startup without a few tests. Redwood fully integrates Jest with both the front- and back-ends, and makes it easy to keep your whole app covered by generating test files with all your components and services:

```
yarn rw test
```

To make the integration even more seamless, Redwood augments Jest with database [scenarios](https://redwoodjs.com/docs/testing#scenarios) and [GraphQL mocking](https://redwoodjs.com/docs/testing#mocking-graphql-calls).

## Ship it

Redwood is designed for both serverless deploy targets like Netlify and Vercel and serverful deploy targets like Render and AWS:

```
yarn rw setup deploy --help
```

Don't go live without auth! Lock down your app with Redwood's built-in, database-backed authentication system ([dbAuth](https://redwoodjs.com/docs/authentication#self-hosted-auth-installation-and-setup)), or integrate with nearly a dozen third-party auth providers:

```
yarn rw setup auth --help
```

## Next Steps

The best way to learn Redwood is by going through the comprehensive [tutorial](https://redwoodjs.com/docs/tutorial/foreword) and joining the community (via the [Discourse forum](https://community.redwoodjs.com) or the [Discord server](https://discord.gg/redwoodjs)).

## Quick Links

- Stay updated: read [Forum announcements](https://community.redwoodjs.com/c/announcements/5), follow us on [Twitter](https://twitter.com/redwoodjs), and subscribe to the [newsletter](https://redwoodjs.com/newsletter)
- [Learn how to contribute](https://redwoodjs.com/docs/contributing)

</details>