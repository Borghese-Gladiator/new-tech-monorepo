import { expect, test } from "@playwright/test";
import { createGame, joinGame, waitForBothSeats } from "./helpers";

test("two contexts can create and join the same game", async ({ browser }) => {
  const ctxA = await browser.newContext();
  const ctxB = await browser.newContext();

  try {
    const { page: pageA, gameId } = await createGame(ctxA, "alice");
    const pageB = await joinGame(ctxB, gameId, "bob");

    // Both contexts must show 2 seats filled.
    await waitForBothSeats(pageA);
    await waitForBothSeats(pageB);

    // Connection pill says "Connected" on both.
    await expect(pageA.getByRole("status")).toHaveText(/Connected/);
    await expect(pageB.getByRole("status")).toHaveText(/Connected/);

    // No error toast on either side.
    await expect(pageA.getByText(/Join failed/)).toHaveCount(0);
    await expect(pageB.getByText(/Join failed/)).toHaveCount(0);
  } finally {
    await ctxA.close();
    await ctxB.close();
  }
});
