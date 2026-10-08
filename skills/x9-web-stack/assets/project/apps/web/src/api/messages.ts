import type { ErrorCode } from "api/contract";
import { ApiError } from "./client.ts";

// Typecheck fails when the server adds a code without a message here.
const messages: Record<ErrorCode, string> = {
  "common.bad_request": "The request could not be processed.",
  "common.validation": "Check the highlighted fields.",
  "common.unauthorized": "Please sign in.",
  "common.forbidden": "You do not have access to this.",
  "common.forbidden_origin": "This request was blocked.",
  "common.not_found": "Not found.",
  "common.method_not_allowed": "This action is not available.",
  "common.payload_too_large": "The upload is too large.",
  "common.internal": "Something went wrong. Try again later.",
  "orders.not_found": "Order not found.",
};

export function errorMessage(error: unknown) {
  return error instanceof ApiError ? messages[error.problem.code] : messages["common.internal"];
}
