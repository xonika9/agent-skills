import { and, desc, eq } from "drizzle-orm";
import type { Db } from "#api/shared/ctx.ts";
import type { Page } from "#api/shared/pagination.ts";
import { orders } from "./schema";

// Every query carries the access condition, so another owner's order and a
// missing order are indistinguishable.
export async function findOwnedOrder(db: Db, ownerId: string, id: string) {
  const [row] = await db
    .select()
    .from(orders)
    .where(and(eq(orders.id, id), eq(orders.ownerId, ownerId)));
  return row ?? null;
}

export function listOwnedOrders(db: Db, ownerId: string, page: Page) {
  return db
    .select()
    .from(orders)
    .where(eq(orders.ownerId, ownerId))
    .orderBy(desc(orders.createdAt), desc(orders.id))
    .limit(page.limit)
    .offset(page.offset);
}

export async function insertOrder(db: Db, values: typeof orders.$inferInsert) {
  const [row] = await db.insert(orders).values(values).returning();
  if (!row) throw new Error("insert returned no row");
  return row;
}
