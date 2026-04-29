# Architecture

Use a TypeScript monorepo.

apps/web:
- Next.js client
- Socket.IO client
- lobby and table UI

apps/server:
- Node.js server
- Socket.IO gateway
- authoritative game-session manager

packages/poker-core:
- pure TypeScript poker engine
- no database or socket imports

packages/db:
- Drizzle schema
- migrations
- repository functions

packages/shared:
- shared event contracts and DTOs
