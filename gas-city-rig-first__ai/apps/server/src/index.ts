import { createServer } from "./server.js";

const PORT = Number.parseInt(process.env.PORT ?? "4000", 10);

const server = createServer({
  ...(process.env.DATABASE_URL ? { databaseUrl: process.env.DATABASE_URL } : {}),
});

server.listen(PORT).then((port) => {
  // eslint-disable-next-line no-console
  console.log(`@gas-city/server listening on http://localhost:${port}`);
});

const shutdown = async (): Promise<void> => {
  // eslint-disable-next-line no-console
  console.log("shutting down");
  await server.close();
  process.exit(0);
};

process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
