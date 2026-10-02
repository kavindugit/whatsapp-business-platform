# frontend/Dockerfile
# Multi-stage build: development (hot-reload) and production targets.

# ── Base image ────────────────────────────────────────────────────────────────
FROM node:22-alpine AS base

RUN npm install -g pnpm@9

WORKDIR /app

# Copy dependency manifests
COPY package.json pnpm-lock.yaml* ./

# ── Development target ────────────────────────────────────────────────────────
FROM base AS development

# Install all dependencies (including devDependencies)
RUN pnpm install --frozen-lockfile || pnpm install

# Source mounted as volume for hot-reload
EXPOSE 5173

CMD ["pnpm", "dev"]

# ── Production target ─────────────────────────────────────────────────────────
FROM base AS production

# Install production dependencies
RUN pnpm install --frozen-lockfile --prod

COPY . .

# Build the static bundle
RUN pnpm build

# Serve with a lightweight static server
RUN npm install -g serve

EXPOSE 4173

CMD ["serve", "-s", "dist", "-l", "4173"]
