import { OpenAPIHono } from "@hono/zod-openapi";
import { bodyLimit } from "hono/body-limit";
import { HTTPException } from "hono/http-exception";
import { requestId } from "hono/request-id";
import { secureHeaders } from "hono/secure-headers";
import { ordersRoutes } from "#api/modules/orders/routes.ts";
import type { Actor, AppEnv, Db } from "#api/shared/ctx.ts";
import { AppError, type ErrorCode, toProblem } from "#api/shared/errors.ts";
import type { Logger } from "#api/shared/log.ts";

export type Deps = {
  db: Db;
  log: Logger;
  now: () => Date;
  // Establishes identity only; permissions are checked by module functions.
  authenticate: (request: Request) => Promise<Actor | null>;
  // Exact public origin, for example https://app.example.com.
  publicOrigin: string;
};

const SAFE_METHODS = new Set(["GET", "HEAD", "OPTIONS"]);

const httpCodes: Record<number, ErrorCode> = {
  400: "common.bad_request",
  401: "common.unauthorized",
  403: "common.forbidden",
  404: "common.not_found",
  405: "common.method_not_allowed",
  413: "common.payload_too_large",
};

export function createApp(deps: Deps) {
  const app = new OpenAPIHono<AppEnv>();

  app.use(requestId());
  app.use(
    secureHeaders({
      contentSecurityPolicy: { defaultSrc: ["'self'"], frameAncestors: ["'none'"], objectSrc: ["'none'"] },
    }),
  );
  app.use(
    bodyLimit({
      maxSize: 1024 * 1024,
      onError: () => {
        throw new AppError("common.payload_too_large");
      },
    }),
  );

  // Cross-origin protection for every state-changing method. Hono's csrf
  // middleware checks form and text/plain bodies only, not JSON.
  app.use(async (c, next) => {
    if (!SAFE_METHODS.has(c.req.method)) {
      const site = c.req.header("sec-fetch-site");
      const origin = c.req.header("origin");
      const allowed = site ? site === "same-origin" : origin === undefined || origin === deps.publicOrigin;
      if (!allowed) throw new AppError("common.forbidden_origin");
    }
    await next();
  });

  app.use(async (c, next) => {
    c.set("ctx", {
      db: deps.db,
      actor: await deps.authenticate(c.req.raw),
      log: deps.log.child({ requestId: c.var.requestId }),
      now: deps.now,
    });
    await next();
  });

  app.onError((err, c) => {
    const error =
      err instanceof AppError
        ? err
        : new AppError(err instanceof HTTPException ? (httpCodes[err.status] ?? "common.internal") : "common.internal");
    if (error.status >= 500) {
      deps.log.error("request failed", {
        requestId: c.var.requestId,
        error: err instanceof Error ? err.stack : String(err),
      });
    }
    return c.json(toProblem(error, c.var.requestId), error.status, {
      "Content-Type": "application/problem+json",
    });
  });

  app.notFound(() => {
    throw new AppError("common.not_found");
  });

  app.get("/health", (c) => c.json({ status: "ok" }));

  return app.route("/api/orders", ordersRoutes);
}

export type App = ReturnType<typeof createApp>;

export function openApiDocument(app: App) {
  return app.getOpenAPI31Document({ openapi: "3.1.0", info: { title: "API", version: "1" } });
}
