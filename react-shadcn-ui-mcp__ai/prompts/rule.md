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

## Planning Rule
When generating or revising UI plans that involve ShadCN:
- Use the MCP server to provide structure and UX flow.
- Prioritize component usage where atomic UI pieces are needed.
  - Prefer full UI blocks (e.g. login, dashboard, calendar) when available.
- Treat MCP output as the source of truth for layout and flow decisions.

Do both of the following:
- tell the user the plan in chat
- write the plan to a local markdown file with an appropriate name summarizing what will be implemented

## Implementation Rule
When implementing ShadCN components in code:
1. Always begin by calling `getComponentDemo` to pull correct usage examples.
2. Mirror the implementation pattern shown in the demo exactly.
   - Use the demo as a context snapshot.
   - Do not improvise unless required.
3. For multi-component flows (e.g. forms, modals, auth flows), check if a **Block** exists before composing manually.
4. Be sure to use import aliases over relative imports