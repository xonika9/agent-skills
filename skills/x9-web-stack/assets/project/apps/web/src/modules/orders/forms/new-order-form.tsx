import { useForm } from "@tanstack/react-form";
import { z } from "zod";
import { ApiError } from "#web/api/client.ts";
import { errorMessage } from "#web/api/messages.ts";
import { useCreateOrder } from "../queries.ts";

const NewOrder = z.object({
  title: z.string().trim().min(1, "Required"),
  amount: z.number().nonnegative("Must not be negative"),
});

export function NewOrderForm() {
  const createOrder = useCreateOrder();
  const form = useForm({
    defaultValues: { title: "", amount: 0 },
    validators: { onSubmit: NewOrder },
    onSubmit: async ({ value, formApi }) => {
      try {
        await createOrder.mutateAsync({ title: value.title, amountCents: Math.round(value.amount * 100) });
        formApi.reset();
      } catch (error) {
        // Server field errors are shown on the form, not as a generic toast.
        if (error instanceof ApiError && error.problem.errors) {
          formApi.setErrorMap({ onSubmit: { fields: fieldErrors(error.problem.errors) } });
        } else {
          formApi.setErrorMap({ onSubmit: { form: errorMessage(error), fields: {} } });
        }
      }
    },
  });

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        void form.handleSubmit();
      }}
    >
      <form.Field name="title">
        {(field) => (
          <label>
            Title
            <input value={field.state.value} onChange={(e) => field.handleChange(e.target.value)} />
            {field.state.meta.errors.map((e) => (
              <span key={String(e?.message ?? e)}>{String(e?.message ?? e)}</span>
            ))}
          </label>
        )}
      </form.Field>
      <form.Field name="amount">
        {(field) => (
          <label>
            Amount
            <input
              type="number"
              value={field.state.value}
              onChange={(e) => field.handleChange(e.target.valueAsNumber)}
            />
            {field.state.meta.errors.map((e) => (
              <span key={String(e?.message ?? e)}>{String(e?.message ?? e)}</span>
            ))}
          </label>
        )}
      </form.Field>
      <form.Subscribe selector={(state) => state.errorMap.onSubmit}>
        {(error) => (typeof error === "string" ? <p role="alert">{error}</p> : null)}
      </form.Subscribe>
      <button type="submit">Create</button>
    </form>
  );
}

function fieldErrors(errors: { path: string; message: string }[]) {
  const map: Record<string, string> = {};
  for (const e of errors) map[e.path === "amountCents" ? "amount" : e.path] = e.message;
  return map;
}
