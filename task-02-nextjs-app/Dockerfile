# build time
FROM oven/bun:canary-alpine AS build
WORKDIR /src

COPY package.json bun.lock* ./
RUN bun install

COPY . .

RUN bun run next build

# runtime
FROM oven/bun:canary-alpine AS runner
WORKDIR /app
COPY package.json bun.lock* ./
RUN bun install --production

ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

COPY --from=build /src/.next ./.next
COPY --from=build /src/public ./public

USER bun

EXPOSE 3000
CMD ["bun", "run", "next", "start"]

