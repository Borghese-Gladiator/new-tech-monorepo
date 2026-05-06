import { expect, type BrowserContext, type Page } from "@playwright/test";

/**
 * Open the lobby page on a fresh browser context, type a display name, and
 * click "Create". Returns the new page (already navigated to /game/<id>)
 * along with the parsed game id.
 */
export async function createGame(
  context: BrowserContext,
  displayName: string,
): Promise<{ page: Page; gameId: string }> {
  const page = await context.newPage();
  await page.goto("/");
  await page
    .getByRole("textbox", { name: "display name" })
    .fill(displayName);
  await page.getByRole("button", { name: "Create" }).click();
  await page.waitForURL(/\/game\/[^/?]+/, { timeout: 15_000 });
  const match = page.url().match(/\/game\/([^/?]+)/);
  if (!match) throw new Error(`unable to parse game id from ${page.url()}`);
  await expect(page.getByRole("status")).toHaveText(/Connected/, {
    timeout: 10_000,
  });
  return { page, gameId: decodeURIComponent(match[1]!) };
}

/**
 * Open the lobby on a fresh context, fill name + game id, click Join, and
 * land on /game/<gameId>.
 */
export async function joinGame(
  context: BrowserContext,
  gameId: string,
  displayName: string,
): Promise<Page> {
  const page = await context.newPage();
  await page.goto("/");
  await page
    .getByRole("textbox", { name: "display name" })
    .fill(displayName);
  await page.getByRole("textbox", { name: "game id" }).fill(gameId);
  await page.getByRole("button", { name: "Join", exact: true }).click();
  await page.waitForURL(new RegExp(`/game/${gameId}(?:\\?|$)`), {
    timeout: 15_000,
  });
  await expect(page.getByRole("status")).toHaveText(/Connected/, {
    timeout: 10_000,
  });
  return page;
}

/** Wait until both seats are populated (hand has started). */
export async function waitForBothSeats(page: Page): Promise<void> {
  await expect(page.locator("[data-seat]")).toHaveCount(2, {
    timeout: 15_000,
  });
}

/** Read the integer stack value displayed in a seat tile. */
export async function readStack(page: Page, seat: number): Promise<number> {
  const text = await page
    .locator(`[data-seat="${seat}"]`)
    .locator("text=stack:")
    .innerText();
  const match = text.match(/(\d+)/);
  if (!match) throw new Error(`could not parse stack for seat ${seat}: "${text}"`);
  return Number(match[1]);
}

/**
 * Find the seat number whose tile carries the amber action ring.
 * Tailwind class names are stable in dev mode (no JIT minification of
 * class strings), so we can match `ring-2`. Returns null if no seat
 * currently has the action.
 */
export async function findActionSeat(page: Page): Promise<number | null> {
  const seats = await page.locator("[data-seat]").all();
  for (const tile of seats) {
    const cls = (await tile.getAttribute("class")) ?? "";
    if (cls.includes("ring-2")) {
      const seatAttr = await tile.getAttribute("data-seat");
      if (seatAttr !== null) return Number(seatAttr);
    }
  }
  return null;
}

/** Locator for the "(you)" seat tile on a given page. */
export function localSeatTile(page: Page) {
  return page.locator("[data-seat]", { hasText: "(you)" });
}

/** Read the `(you)` seat number on a given page. */
export async function readLocalSeat(page: Page): Promise<number> {
  const seatAttr = await localSeatTile(page).getAttribute("data-seat");
  if (seatAttr === null) {
    throw new Error("no local seat tile found");
  }
  return Number(seatAttr);
}
