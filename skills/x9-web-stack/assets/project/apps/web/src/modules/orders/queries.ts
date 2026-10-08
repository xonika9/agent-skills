import { queryOptions, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, call } from "#web/api/client.ts";

export const orderKeys = {
  all: ["orders"] as const,
  list: () => [...orderKeys.all, "list"] as const,
  detail: (id: string) => [...orderKeys.all, "detail", id] as const,
};

// One definition per query, shared by loaders and components.
export const ordersQuery = () =>
  queryOptions({
    queryKey: orderKeys.list(),
    queryFn: () => call(api.orders.$get({ query: {} })),
  });

export const orderQuery = (id: string) =>
  queryOptions({
    queryKey: orderKeys.detail(id),
    queryFn: () => call(api.orders[":id"].$get({ param: { id } })),
  });

export function useCreateOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: { title: string; amountCents: number }) => call(api.orders.$post({ json: input })),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: orderKeys.all }),
  });
}
