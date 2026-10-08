import { z } from "@hono/zod-openapi";

export const ProblemSchema = z
  .object({
    type: z.string(),
    title: z.string(),
    status: z.int(),
    code: z.string(),
    requestId: z.string(),
    errors: z.array(z.object({ path: z.string(), message: z.string() })).optional(),
  })
  .openapi("Problem");

const problem = (description: string) => ({
  content: { "application/problem+json": { schema: ProblemSchema } },
  description,
});

export const ProblemResponses = {
  400: problem("Invalid request"),
  401: problem("Not signed in"),
  404: problem("Not found"),
};
