# infra/Dockerfile.app — Frontend Next.js 14 (multi-stage)
# Stage deps: instala dependencias.  builder: build de producción.  runtime: imagen mínima.

# ── Stage 1: Dependencies ─────────────────────────────────────────
FROM node:20-alpine AS deps
WORKDIR /app

COPY package.json package-lock.json* ./
# Si no hay lockfile aún, usa install; si existe, usa ci (reproducible).
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# ── Stage 2: Builder ──────────────────────────────────────────────
FROM node:20-alpine AS builder
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# ── Stage 3: Runtime ──────────────────────────────────────────────
FROM node:20-alpine AS runtime
WORKDIR /app

RUN addgroup -g 1001 appuser && \
    adduser -D -u 1001 -G appuser appuser

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000

# Salida standalone de Next.js (next.config.mjs: output: 'standalone').
COPY --from=builder /app/public ./public
COPY --from=builder --chown=appuser:appuser /app/.next/standalone ./
COPY --from=builder --chown=appuser:appuser /app/.next/static ./.next/static

USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD wget -qO- http://localhost:3000/ >/dev/null 2>&1 || exit 1

EXPOSE 3000

CMD ["node", "server.js"]
