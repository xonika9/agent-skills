import { sql } from "drizzle-orm";
import { check, index, integer, pgTable, text, uuid } from "drizzle-orm/pg-core";
import { id, timestamps } from "#api/shared/columns.ts";

export const orders = pgTable(
  "orders",
  {
    id: id(),
    ownerId: uuid("owner_id").notNull(),
    title: text("title").notNull(),
    amountCents: integer("amount_cents").notNull(),
    ...timestamps(),
  },
  (t) => [
    index("orders_owner_id_idx").on(t.ownerId),
    check("orders_amount_cents_nonnegative", sql`${t.amountCents} >= 0`),
  ],
);
