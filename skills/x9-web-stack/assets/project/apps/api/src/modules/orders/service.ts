import type { Ctx } from "#api/shared/ctx.ts";
import { AppError, requireActor } from "#api/shared/errors.ts";
import type { Page } from "#api/shared/pagination.ts";
import { findOwnedOrder, insertOrder, listOwnedOrders } from "./queries";
import type { orders } from "./schema";

export type Order = typeof orders.$inferSelect;

export type NewOrder = { title: string; amountCents: number };

export async function getOrder(ctx: Ctx, id: string): Promise<Order> {
  const actor = requireActor(ctx);
  const order = await findOwnedOrder(ctx.db, actor.userId, id);
  if (!order) throw new AppError("orders.not_found");
  return order;
}

export function listOrders(ctx: Ctx, page: Page): Promise<Order[]> {
  const actor = requireActor(ctx);
  return listOwnedOrders(ctx.db, actor.userId, page);
}

export function createOrder(ctx: Ctx, input: NewOrder): Promise<Order> {
  const actor = requireActor(ctx);
  const now = ctx.now();
  return insertOrder(ctx.db, { ...input, ownerId: actor.userId, createdAt: now, updatedAt: now });
}
