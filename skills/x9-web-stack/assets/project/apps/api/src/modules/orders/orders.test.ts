import { describe, expect, it } from "vitest";
import { app, as, db, publicOrigin } from "../../../test/app";
import { makeOrder } from "./testing";

describe("orders", () => {
  it("creates and reads an own order", async () => {
    const owner = crypto.randomUUID();
    const created = await app.request(
      "/api/orders",
      as(owner, { method: "POST", body: JSON.stringify({ title: "Desk", amountCents: 1500 }) }),
    );
    expect(created.status).toBe(201);
    const order = (await created.json()) as { id: string };

    const read = await app.request(`/api/orders/${order.id}`, as(owner));
    expect(read.status).toBe(200);
    expect(await read.json()).toEqual(order);
  });

  it("answers 404 for another user's order", async () => {
    const order = await makeOrder(db, crypto.randomUUID());
    const res = await app.request(`/api/orders/${order.id}`, as(crypto.randomUUID()));
    expect(res.status).toBe(404);
    expect(res.headers.get("content-type")).toContain("application/problem+json");
    expect(await res.json()).toMatchObject({ code: "orders.not_found", status: 404 });
  });

  it("lists only the current user's orders", async () => {
    const owner = crypto.randomUUID();
    const mine = await makeOrder(db, owner);
    await makeOrder(db, crypto.randomUUID());
    const res = await app.request("/api/orders", as(owner));
    expect(res.status).toBe(200);
    const body = (await res.json()) as { items: { id: string }[] };
    expect(body.items.map((o) => o.id)).toEqual([mine.id]);
  });

  it("answers unknown API paths with a problem", async () => {
    const res = await app.request("/api/nope", as(crypto.randomUUID()));
    expect(res.status).toBe(404);
    expect(await res.json()).toMatchObject({ code: "common.not_found" });
  });

  it("rejects invalid input with field errors", async () => {
    const res = await app.request(
      "/api/orders",
      as(crypto.randomUUID(), { method: "POST", body: JSON.stringify({ title: "", amountCents: -1 }) }),
    );
    expect(res.status).toBe(400);
    const body = (await res.json()) as { code: string; errors: { path: string }[] };
    expect(body.code).toBe("common.validation");
    expect(body.errors.map((e) => e.path).sort()).toEqual(["amountCents", "title"]);
  });

  it("requires sign-in", async () => {
    const res = await app.request("/api/orders");
    expect(res.status).toBe(401);
  });

  it("blocks cross-origin writes", async () => {
    const res = await app.request(
      "/api/orders",
      as(crypto.randomUUID(), {
        method: "POST",
        headers: { origin: "https://evil.test" },
        body: JSON.stringify({ title: "x", amountCents: 1 }),
      }),
    );
    expect(res.status).toBe(403);
    const same = await app.request(
      "/api/orders",
      as(crypto.randomUUID(), {
        method: "POST",
        headers: { origin: publicOrigin },
        body: JSON.stringify({ title: "x", amountCents: 1 }),
      }),
    );
    expect(same.status).toBe(201);
  });
});
