import { createRoute, OpenAPIHono } from "@hono/zod-openapi";
import type { AppEnv } from "#api/shared/ctx.ts";
import { rejectInvalid } from "#api/shared/errors.ts";
import { PageQuery } from "#api/shared/pagination.ts";
import { ProblemResponses } from "#api/shared/problem-schema.ts";
import { NewOrderSchema, OrderListSchema, OrderParams, OrderSchema } from "./schemas";
import { createOrder, getOrder, listOrders, type Order } from "./service";

// An explicit field set: new columns never leak into responses by accident.
const toDto = (order: Order) => ({
  id: order.id,
  title: order.title,
  amountCents: order.amountCents,
  createdAt: order.createdAt.toISOString(),
});

const json = <T>(schema: T, description: string) => ({
  content: { "application/json": { schema } },
  description,
});

const list = createRoute({
  method: "get",
  path: "/",
  request: { query: PageQuery },
  responses: { 200: json(OrderListSchema, "Orders of the current user"), ...ProblemResponses },
});

const get = createRoute({
  method: "get",
  path: "/{id}",
  request: { params: OrderParams },
  responses: { 200: json(OrderSchema, "The order"), ...ProblemResponses },
});

const create = createRoute({
  method: "post",
  path: "/",
  request: { body: { content: { "application/json": { schema: NewOrderSchema } }, required: true } },
  responses: { 201: json(OrderSchema, "The created order"), ...ProblemResponses },
});

// Chained so the full route type reaches AppType and the hc client.
export const ordersRoutes = new OpenAPIHono<AppEnv>({ defaultHook: rejectInvalid })
  .openapi(list, async (c) => {
    const items = await listOrders(c.var.ctx, c.req.valid("query"));
    return c.json({ items: items.map(toDto) }, 200);
  })
  .openapi(get, async (c) => {
    const order = await getOrder(c.var.ctx, c.req.valid("param").id);
    return c.json(toDto(order), 200);
  })
  .openapi(create, async (c) => {
    const order = await createOrder(c.var.ctx, c.req.valid("json"));
    return c.json(toDto(order), 201);
  });
