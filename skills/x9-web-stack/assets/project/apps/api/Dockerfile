# The Bun version must equal packageManager in the root package.json.
FROM oven/bun:__BUN_VERSION__ AS deps
WORKDIR /app
COPY package.json bun.lock bunfig.toml ./
COPY apps/api/package.json apps/api/
COPY apps/web/package.json apps/web/
RUN bun install --frozen-lockfile --production --filter api

FROM oven/bun:__BUN_VERSION__
WORKDIR /app
ENV NODE_ENV=production
COPY --from=deps /app/node_modules node_modules
COPY --from=deps /app/apps/api/node_modules apps/api/node_modules
COPY tsconfig.base.json ./
COPY apps/api apps/api
WORKDIR /app/apps/api
USER bun
EXPOSE 3000
# Exec form so SIGTERM reaches Bun directly.
CMD ["bun", "src/index.ts"]
