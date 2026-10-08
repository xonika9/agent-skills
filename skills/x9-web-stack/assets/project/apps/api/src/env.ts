import { z } from "zod";

const EnvSchema = z.object({
  DATABASE_URL: z.string().min(1),
  PUBLIC_ORIGIN: z.url(),
  PORT: z.coerce.number().int().positive().default(3000),
});

export type Env = z.infer<typeof EnvSchema>;

// Fails at startup, not on first use.
export function loadEnv(source: Record<string, string | undefined>): Env {
  return EnvSchema.parse(source);
}
