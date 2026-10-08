import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { NewOrderForm } from "./new-order-form.tsx";

afterEach(() => vi.unstubAllGlobals());

function renderForm() {
  render(
    <QueryClientProvider client={new QueryClient()}>
      <NewOrderForm />
    </QueryClientProvider>,
  );
}

it("shows a field error instead of submitting an empty title", async () => {
  renderForm();
  fireEvent.click(screen.getByRole("button", { name: "Create" }));
  expect(await screen.findByText("Required")).toBeInTheDocument();
});

it("shows a server error that belongs to no field", async () => {
  const problem = { code: "common.forbidden_origin", status: 403, requestId: "r1" };
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => Response.json(problem, { status: 403, headers: { "content-type": "application/problem+json" } })),
  );
  renderForm();
  fireEvent.change(screen.getByLabelText("Title"), { target: { value: "Desk" } });
  fireEvent.click(screen.getByRole("button", { name: "Create" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("This request was blocked.");
});
