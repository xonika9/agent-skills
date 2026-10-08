import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createRouter, RouterProvider } from "@tanstack/react-router";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { shouldRetry } from "./api/client.ts";
import { routeTree } from "./routeTree.gen.ts";
import "./styles.css";

// After a release the old chunks are gone; reload once to get the new build.
window.addEventListener("vite:preloadError", () => {
  const last = Number(sessionStorage.getItem("preload-reload") ?? 0);
  if (Date.now() - last < 10_000) return;
  sessionStorage.setItem("preload-reload", String(Date.now()));
  window.location.reload();
});

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: shouldRetry } } });

const router = createRouter({
  routeTree,
  context: { queryClient },
  defaultPreload: "intent",
  // Query owns freshness.
  defaultPreloadStaleTime: 0,
});

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

const root = document.getElementById("root");
if (!root) throw new Error("#root is missing");

createRoot(root).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </StrictMode>,
);
