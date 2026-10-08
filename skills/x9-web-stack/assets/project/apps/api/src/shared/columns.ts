import { timestamp, uuid } from "drizzle-orm/pg-core";

// gen_random_uuid() works on every supported PostgreSQL; switch the default
// to uuidv7() once all databases run PostgreSQL 18.
export const id = () => uuid("id").primaryKey().defaultRandom();

export const timestamps = () => ({
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
  updatedAt: timestamp("updated_at", { withTimezone: true })
    .notNull()
    .defaultNow()
    .$onUpdate(() => new Date()),
});
