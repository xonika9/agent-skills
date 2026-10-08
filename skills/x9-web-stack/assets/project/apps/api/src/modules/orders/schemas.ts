import { z } from "@hono/zod-openapi";

export const OrderSchema = z
  .object({
    id: z.uuid(),
    title: z.string(),
    amountCents: z.int().nonnegative(),
    createdAt: z.iso.datetime(),
  })
  .openapi("Order");

export const OrderListSchema = z.object({ items: z.array(OrderSchema) }).openapi("OrderList");

export const NewOrderSchema = z
  .object({
    title: z.string().trim().min(1).max(200),
    amountCents: z.int().nonnegative(),
  })
  .openapi("NewOrder");

export const OrderParams = z.object({
  id: z.uuid().openapi({ param: { name: "id", in: "path" } }),
});
