# The Bun version must equal packageManager in the root package.json.
FROM oven/bun:__BUN_VERSION__ AS build
WORKDIR /app
COPY package.json bun.lock bunfig.toml tsconfig.base.json ./
COPY apps/api/package.json apps/api/
COPY apps/web/package.json apps/web/
RUN bun install --frozen-lockfile --filter web --filter api
COPY apps/api apps/api
COPY apps/web apps/web
RUN bun run --filter web build

FROM caddy:2
COPY Caddyfile /etc/caddy/Caddyfile
COPY --from=build /app/apps/web/dist /srv
