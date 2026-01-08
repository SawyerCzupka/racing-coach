# Development stage - wrangler dev with D1 emulation
# NOTE: Must use Debian-based image (not Alpine) because workerd requires glibc
FROM node:lts-slim AS development
WORKDIR /app

# Disable wrangler telemetry in Docker (prevents interactive prompt freeze)
ENV WRANGLER_SEND_METRICS=false

COPY package*.json ./
RUN npm ci
COPY . .

# Create wrangler state directory for local D1
RUN mkdir -p .wrangler/state/v3/d1

EXPOSE 4321
# Use astro dev with platformProxy for D1 bindings locally
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# Build stage
FROM node:lts-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage - for local testing only (production uses Cloudflare Pages)
FROM node:lts-slim AS production
WORKDIR /app

# Disable wrangler telemetry
ENV WRANGLER_SEND_METRICS=false

COPY --from=builder /app/dist ./dist
COPY --from=builder /app/wrangler.toml ./
COPY --from=builder /app/package*.json ./
RUN npm ci --omit=dev && npm install wrangler

EXPOSE 8788
CMD ["npx", "wrangler", "pages", "dev", "dist", "--port", "8788", "--ip", "0.0.0.0"]
