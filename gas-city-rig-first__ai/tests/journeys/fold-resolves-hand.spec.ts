import { expect, test } from "@playwright/test";
import {
  createGame,
  findActionSeat,
  joinGame,
  readLocalSeat,
  readStack,
  waitForBothSeats,
} from "./helpers";

test("when A folds, B wins the pot and the hand resolves", async ({
  browser,
}) => {
  const ctxA = await browser.newContext();
  const ctxB = await browser.newContext();

  try {
    const { page: pageA, gameId } = await createGame(ctxA, "alice");
    const pageB = await joinGame(ctxB, gameId, "bob");

    await waitForBothSeats(pageA);
    await waitForBothSeats(pageB);

    // Wait until A is the actor (the action ring lands on A's seat).
    const aSeat = await readLocalSeat(pageA);
    const bSeat = await readLocalSeat(pageB);
    expect(aSeat).not.toBe(bSeat);

    await expect
      .poll(() => findActionSeat(pageA), {
        timeout: 15_000,
        message: "expected the action ring to appear on A",
      })
      .toBe(aSeat);

    // Snapshot B's stack just before the fold so we can verify a positive
    // delta. (A's stack was already debited by the SB before A acted, so A
    // doesn't lose more on the fold itself — B picks up the pot.)
    const bStackBefore = await readStack(pageA, bSeat);

    // Fold from A.
    await pageA
      .getByRole("button", { name: "Fold", exact: true })
      .click();

    // A's seat should show "folded" status.
    await expect(
      pageA.locator(`[data-seat="${aSeat}"]`).getByText("folded"),
    ).toBeVisible({ timeout: 5_000 });

    // Hand-resolved post-state: B's stack is bigger than before (won the pot).
    await expect
      .poll(() => readStack(pageB, bSeat), { timeout: 10_000 })
      .toBeGreaterThan(bStackBefore);

    // The hand-resolved event should appear in A's event log.
    await expect(pageA.getByText(/Resolved · winners:/)).toBeVisible({
      timeout: 5_000,
    });
  } finally {
    await ctxA.close();
    await ctxB.close();
  }
});
