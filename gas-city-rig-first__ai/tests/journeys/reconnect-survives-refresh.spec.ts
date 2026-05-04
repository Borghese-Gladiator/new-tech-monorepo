import { expect, test, type Page } from "@playwright/test";
import {
  createGame,
  joinGame,
  localSeatTile,
  readLocalSeat,
  readStack,
  waitForBothSeats,
} from "./helpers";

async function readHoleCardLabels(page: Page): Promise<string[]> {
  const labels = await localSeatTile(page)
    .locator("[aria-label]")
    .evaluateAll((nodes) =>
      nodes
        .map((n) => n.getAttribute("aria-label") ?? "")
        .filter((l) => l && l !== "hidden card"),
    );
  return labels;
}

test("A's seat and hole cards survive a page reload", async ({ browser }) => {
  const ctxA = await browser.newContext();
  const ctxB = await browser.newContext();

  try {
    const { page: pageA, gameId } = await createGame(ctxA, "alice");
    const pageB = await joinGame(ctxB, gameId, "bob");

    await waitForBothSeats(pageA);
    await waitForBothSeats(pageB);

    const seatBefore = await readLocalSeat(pageA);
    const stackBefore = await readStack(pageA, seatBefore);
    const holeBefore = await readHoleCardLabels(pageA);
    expect(holeBefore.length, "two hole cards visible before reload").toBe(2);

    // Reload context A.
    await pageA.reload();

    // Within 5s the connection pill returns to Connected on A.
    await expect(pageA.getByRole("status")).toHaveText(/Connected/, {
      timeout: 5_000,
    });

    // Same seat is re-bound (the "(you)" tile is still on the same seat).
    const seatAfter = await readLocalSeat(pageA);
    expect(seatAfter).toBe(seatBefore);

    // Stack is unchanged (no hand ended in between).
    const stackAfter = await readStack(pageA, seatAfter);
    expect(stackAfter).toBe(stackBefore);

    // Hole cards are restored (same two card labels) — order is stable
    // since the server replays the same per-seat snapshot.
    const holeAfter = await readHoleCardLabels(pageA);
    expect(holeAfter.length).toBe(2);
    expect([...holeAfter].sort()).toEqual([...holeBefore].sort());
  } finally {
    await ctxA.close();
    await ctxB.close();
  }
});
