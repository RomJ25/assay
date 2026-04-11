# ══════════════════════════════════════════════════════════════
# Assay — Multi-stage Docker build
# Stage 1: Build React frontend with Node
# Stage 2: Production Python image serving API + static frontend
# ══════════════════════════════════════════════════════════════

# ── Stage 1: Frontend build ──────────────────────────────────
FROM node:22-slim AS frontend

WORKDIR /app/web

# Install pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Install dependencies (cached layer)
COPY web/package.json web/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# Copy source and build
COPY web/index.html web/tsconfig.json web/vite.config.ts ./
COPY web/public/ ./public/
COPY web/src/ ./src/
RUN pnpm build


# ── Stage 2: Python production image ────────────────────────
FROM python:3.13-slim AS production

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Environment
ENV TZ=America/New_York
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV ASSAY_RESULTS=/app/data/results
ENV ASSAY_CACHE_DB=/app/data/cache.db

# Python dependencies (cached layer)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py server.py config.py ./
COPY api/ ./api/
COPY backtest/ ./backtest/
COPY data/ ./data/
COPY models/ ./models/
COPY output/ ./output/
COPY quality/ ./quality/
COPY scoring/ ./scoring/
COPY docs/ ./docs/

# Copy built frontend from Stage 1
COPY --from=frontend /app/web/dist ./web/dist

# Copy entrypoint
COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh

# Create data directories
RUN mkdir -p /app/data/results /app/storage/logos

# Health check (longer start period for initial screen run ~90s)
HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# Entrypoint: initial screen → daily scheduler → web server
CMD ["./entrypoint.sh"]
