import { defineConfig } from "drizzle-kit";

const url = process.env.DATABASE_URL ?? "file:./.data/poker.db";
const path = url.startsWith("file:") ? url.slice("file:".length) : url;

export default defineConfig({
  dialect: "sqlite",
  schema: "./src/schema.ts",
  out: "./drizzle",
  dbCredentials: { url: path },
});
