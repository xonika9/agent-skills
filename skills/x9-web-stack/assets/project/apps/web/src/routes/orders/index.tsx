import { createFileRoute } from "@tanstack/react-router";
import { NewOrderForm, OrderList, ordersQuery } from "#web/modules/orders/index.ts";

// Thin route: load data, render the module's components.
export const Route = createFileRoute("/orders/")({
  loader: ({ context }) => context.queryClient.query({ ...ordersQuery(), staleTime: "static" }),
  component: () => (
    <main>
      <h1>Orders</h1>
      <NewOrderForm />
      <OrderList />
    </main>
  ),
});
