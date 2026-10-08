import { z } from "@hono/zod-openapi";

export const PageQuery = z.object({
  limit: z.coerce.number().int().min(1).max(100).default(20),
  offset: z.coerce.number().int().min(0).default(0),
});

export type Page = z.infer<typeof PageQuery>;
