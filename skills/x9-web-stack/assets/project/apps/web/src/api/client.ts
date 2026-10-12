import type { AppType, ErrorCode } from "api/contract";
import { type ClientResponse, DetailedError, hc, parseResponse } from "hono/client";

export type Problem = {
  code: ErrorCode;
  status: number;
  requestId: string;
  errors?: { path: string; message: string }[];
};

export class ApiError extends Error {
  constructor(readonly problem: Problem) {
    super(problem.code);
  }
}

export class NetworkError extends Error {
  constructor(cause: unknown) {
    super("Network request failed", { cause });
  }
}

// Every request goes through this wrapper: shared headers and 401 handling
// live here, not in components.
const appFetch: typeof fetch = async (input, init) => {
  let res: Response;
  try {
    res = await fetch(input, { ...init, credentials: "same-origin" });
  } catch (error) {
    if (error instanceof TypeError) throw new NetworkError(error);
    throw error;
  }
  if (res.status === 401) window.dispatchEvent(new Event("app:unauthorized"));
  return res;
};

export const api = hc<AppType>("/", { fetch: appFetch }).api;

// Returns the typed success body or throws ApiError with the server's code.
export async function call<T extends ClientResponse<unknown>>(request: Promise<T>) {
  try {
    return await parseResponse(request);
  } catch (error) {
    if (error instanceof DetailedError && isProblem(error.detail?.data)) throw new ApiError(error.detail.data);
    throw error;
  }
}

function isProblem(value: unknown): value is Problem {
  return typeof value === "object" && value !== null && "code" in value && "status" in value;
}

// Retry only network failures and server errors; a 4xx will not change.
export function shouldRetry(failureCount: number, error: unknown) {
  if (failureCount >= 2) return false;
  if (error instanceof ApiError) return error.problem.status >= 500 && error.problem.status < 600;
  if (error instanceof DetailedError) return error.statusCode >= 500 && error.statusCode < 600;
  return error instanceof NetworkError;
}
