import type { z } from "@hono/zod-openapi";
import type { Actor, Ctx } from "./ctx";

// The single registry of error codes. A code never changes meaning; add a new
// one instead. Module codes are namespaced: "<module>.<reason>".
export const errorStatus = {
  "common.bad_request": 400,
  "common.validation": 400,
  "common.unauthorized": 401,
  "common.forbidden": 403,
  "common.forbidden_origin": 403,
  "common.not_found": 404,
  "common.method_not_allowed": 405,
  "common.payload_too_large": 413,
  "common.internal": 500,
  "orders.not_found": 404,
} as const;

export type ErrorCode = keyof typeof errorStatus;

export type FieldError = { path: string; message: string };

export class AppError extends Error {
  constructor(
    readonly code: ErrorCode,
    readonly errors?: FieldError[],
  ) {
    super(code);
  }

  get status() {
    return errorStatus[this.code];
  }
}

// RFC 9457 problem details body.
export function toProblem(error: AppError, requestId: string) {
  return {
    type: "about:blank",
    title: error.code,
    status: error.status,
    code: error.code,
    requestId,
    ...(error.errors ? { errors: error.errors } : {}),
  };
}

// Used as the OpenAPIHono defaultHook: invalid input becomes a validation problem.
export function rejectInvalid(result: { success: boolean; error?: z.ZodError }) {
  if (!result.success && result.error) {
    throw new AppError(
      "common.validation",
      result.error.issues.map((issue) => ({ path: issue.path.join("."), message: issue.message })),
    );
  }
}

export function requireActor(ctx: Ctx): Actor {
  if (!ctx.actor) throw new AppError("common.unauthorized");
  return ctx.actor;
}
