#!/bin/bash
# ══════════════════════════════════════════════════════════════════════
# Assay container entrypoint
#
# server mode (default):
#   1. start web server IMMEDIATELY (port 8000 responds within seconds)
#   2. run initial screen in the background if no data exists yet
#      (UI shows a "no data" state until it finishes, ~5–15 min on fresh cache)
#   3. start the daily refresh scheduler in the background
#
# scan mode:
#   run one screen and exit.
# ══════════════════════════════════════════════════════════════════════
set -e

echo "═══ Assay Startup ═══"
echo "$(date '+%Y-%m-%d %H:%M:%S') Starting Assay..."

# ── Configuration from environment ──
UNIVERSE="${ASSAY_UNIVERSE:-sp500}"
TOP_N="${ASSAY_TOP_N:-30}"
MODE="${ASSAY_MODE:-server}"
RESULTS_DIR="${ASSAY_RESULTS:-/app/state/results}"

mkdir -p "$RESULTS_DIR"

# Build scan command from env
SCAN_CMD="python main.py --universe ${UNIVERSE} --top ${TOP_N}"
[ -n "${ASSAY_INCLUDE_FINANCIALS}" ] && SCAN_CMD="${SCAN_CMD} --include-financials"
[ -n "${ASSAY_SECTOR_RELATIVE}" ] && SCAN_CMD="${SCAN_CMD} --sector-relative"

echo "$(date '+%Y-%m-%d %H:%M:%S') Universe: $UNIVERSE | Mode: $MODE"

# ── Scan-only mode: run and exit ────────────────────────────────────
if [ "$MODE" = "scan" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') Running scan: $SCAN_CMD"
    exec $SCAN_CMD
fi

# ── Server mode ─────────────────────────────────────────────────────
# Track background PIDs so we can clean them up on shutdown
SCAN_PID=""
SCHEDULER_PID=""
SERVER_PID=""

cleanup() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') Received shutdown signal, stopping..."
    for pid in "$SCAN_PID" "$SCHEDULER_PID" "$SERVER_PID"; do
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            kill -TERM "$pid" 2>/dev/null || true
        fi
    done
    # Give them a moment to exit cleanly
    sleep 1
    exit 0
}
trap cleanup SIGTERM SIGINT

# ── 1. Initial scan (background) if no data exists ──────────────────
if ! ls "$RESULTS_DIR"/screen_*.json 1>/dev/null 2>&1; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') No screen data found. Kicking off initial screen in background."
    echo "$(date '+%Y-%m-%d %H:%M:%S')   UI will be reachable immediately at :8000 — data appears once scan finishes."

    (
        ATTEMPT=1
        MAX_ATTEMPTS=3
        while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
            echo "$(date '+%Y-%m-%d %H:%M:%S') [initial-scan] attempt $ATTEMPT/$MAX_ATTEMPTS..."
            if $SCAN_CMD; then
                if ls "$RESULTS_DIR"/screen_*.json 1>/dev/null 2>&1; then
                    echo "$(date '+%Y-%m-%d %H:%M:%S') [initial-scan] complete — data saved."
                    break
                else
                    echo "$(date '+%Y-%m-%d %H:%M:%S') [initial-scan] exited OK but no JSON saved."
                fi
            else
                echo "$(date '+%Y-%m-%d %H:%M:%S') [initial-scan] attempt $ATTEMPT failed."
            fi

            if [ $ATTEMPT -lt $MAX_ATTEMPTS ]; then
                DELAY=$((ATTEMPT * 30))
                echo "$(date '+%Y-%m-%d %H:%M:%S') [initial-scan] retrying in ${DELAY}s..."
                sleep $DELAY
            fi
            ATTEMPT=$((ATTEMPT + 1))
        done

        if ! ls "$RESULTS_DIR"/screen_*.json 1>/dev/null 2>&1; then
            echo "$(date '+%Y-%m-%d %H:%M:%S') [initial-scan] WARNING: all attempts failed."
            echo "$(date '+%Y-%m-%d %H:%M:%S') [initial-scan] Use the 'Run Scan' button in the UI or wait for the daily scheduler."
        fi
    ) &
    SCAN_PID=$!
else
    LATEST=$(ls -t "$RESULTS_DIR"/screen_*.json 2>/dev/null | head -1)
    echo "$(date '+%Y-%m-%d %H:%M:%S') Found existing data: $(basename "$LATEST")"
fi

# ── 2. Daily refresh scheduler (background) ─────────────────────────
SCHEDULE_HOUR="${ASSAY_SCHEDULE_HOUR:-06}"
SCHEDULE_MIN="${ASSAY_SCHEDULE_MIN:-00}"
echo "$(date '+%Y-%m-%d %H:%M:%S') Daily refresh scheduled at ${SCHEDULE_HOUR}:${SCHEDULE_MIN} (TZ: $TZ)"

(
    while true; do
        NOW=$(date +%s)
        TARGET=$(date -d "today ${SCHEDULE_HOUR}:${SCHEDULE_MIN}" +%s 2>/dev/null || \
                 date -j -f "%H:%M" "${SCHEDULE_HOUR}:${SCHEDULE_MIN}" +%s 2>/dev/null)

        if [ "$TARGET" -le "$NOW" ]; then
            TARGET=$((TARGET + 86400))
        fi

        WAIT=$((TARGET - NOW))
        echo "$(date '+%Y-%m-%d %H:%M:%S') [scheduler] Next refresh in $((WAIT / 3600))h $((WAIT % 3600 / 60))m"
        sleep $WAIT

        echo "$(date '+%Y-%m-%d %H:%M:%S') [scheduler] Running daily refresh..."
        $SCAN_CMD --refresh 2>&1 | tail -5
        echo "$(date '+%Y-%m-%d %H:%M:%S') [scheduler] Refresh complete."
    done
) &
SCHEDULER_PID=$!

# ── 3. Web server (foreground — keeps container alive) ──────────────
# Single worker is required: the in-memory "scan in progress" state
# is held in the uvicorn process.
echo "$(date '+%Y-%m-%d %H:%M:%S') Starting web server on port 8000..."
uvicorn server:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!
wait "$SERVER_PID"
