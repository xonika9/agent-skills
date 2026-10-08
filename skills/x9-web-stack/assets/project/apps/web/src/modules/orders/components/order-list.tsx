import { useSuspenseQuery } from "@tanstack/react-query";
import { ordersQuery } from "../queries.ts";

export function OrderList() {
  const { data } = useSuspenseQuery(ordersQuery());
  if (data.items.length === 0) return <p>No orders yet.</p>;
  return (
    <ul>
      {data.items.map((order) => (
        <li key={order.id}>
          {order.title} — {(order.amountCents / 100).toFixed(2)}
        </li>
      ))}
    </ul>
  );
}
