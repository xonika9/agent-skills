import type { Db } from "#api/shared/ctx.ts";
import { insertOrder } from "./queries";

// Test-data factory. Imported only by tests.
export function makeOrder(db: Db, ownerId: string, overrides: { title?: string; amountCents?: number } = {}) {
  return insertOrder(db, { ownerId, title: "Test order", amountCents: 1000, ...overrides });
}
