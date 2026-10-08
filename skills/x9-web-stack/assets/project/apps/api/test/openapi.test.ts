import { expect, it } from "vitest";
import { openApiDocument } from "../src/app";
import { app } from "./app";

// Contract changes show up in every diff. Update with `vitest run -u`.
it("matches the committed OpenAPI snapshot", async () => {
  await expect(`${JSON.stringify(openApiDocument(app), null, 2)}\n`).toMatchFileSnapshot("../openapi.json");
});
