"""Assay web server — FastAPI serving the API and React frontend."""

from __future__ import annotations

import logging
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("assay.server")

app = FastAPI(title="Assay", description="S&P 500 Value + Quality Screener")

# Gzip compression for large JSON responses (~1MB → ~100KB)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS for Vite dev server (port 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check (must be before static mount)
@app.get("/health")
async def health():
    return {"status": "ok"}

# API routes
app.include_router(router)

# Serve built React frontend with SPA fallback
FRONTEND_DIR = Path(__file__).parent / "web" / "dist"
if FRONTEND_DIR.exists():
    from fastapi.responses import FileResponse

    # Serve static assets (JS, CSS, fonts)
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")

    # SPA fallback: any non-API route returns index.html for React Router
    @app.get("/{path:path}")
    async def spa_fallback(path: str):
        file_path = (FRONTEND_DIR / path).resolve()
        # Prevent path traversal — file must be within FRONTEND_DIR
        if file_path.is_file() and str(file_path).startswith(str(FRONTEND_DIR.resolve())):
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIR / "index.html")

    logger.info(f"Serving frontend from {FRONTEND_DIR}")
else:
    logger.info("No frontend build found at web/dist/. Run 'cd web && pnpm build' to build.")


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
