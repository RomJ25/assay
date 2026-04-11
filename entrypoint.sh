#!/bin/bash
set -e

echo "═══ Assay Startup ═══"
echo "$(date '+%Y-%m-%d %H:%M:%S') Starting Assay..."

# ── Run screener if no data exists ──
RESULTS_DIR="${ASSAY_RESULTS:-/app/data/results}"
if ! ls "$RESULTS_DIR"/screen_*.json 1>/dev/null 2>&1; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') No screen data found. Running initial screen..."
    python main.py || echo "Initial screen failed (will retry on schedule)"
    echo "$(date '+%Y-%m-%d %H:%M:%S') Initial screen complete."
else
    LATEST=$(ls -t "$RESULTS_DIR"/screen_*.json 2>/dev/null | head -1)
    echo "$(date '+%Y-%m-%d %H:%M:%S') Found existing data: $(basename $LATEST)"
fi

# ── Start daily scheduler in background ──
SCHEDULE_HOUR="${ASSAY_SCHEDULE_HOUR:-06}"
SCHEDULE_MIN="${ASSAY_SCHEDULE_MIN:-00}"

echo "$(date '+%Y-%m-%d %H:%M:%S') Daily refresh scheduled at ${SCHEDULE_HOUR}:${SCHEDULE_MIN} (container timezone: $TZ)"

(
    while true; do
        # Calculate seconds until next scheduled run
        NOW=$(date +%s)
        TARGET=$(date -d "today ${SCHEDULE_HOUR}:${SCHEDULE_MIN}" +%s 2>/dev/null || \
                 date -j -f "%H:%M" "${SCHEDULE_HOUR}:${SCHEDULE_MIN}" +%s 2>/dev/null)

        if [ "$TARGET" -le "$NOW" ]; then
            # Already past today's time, schedule for tomorrow
            TARGET=$((TARGET + 86400))
        fi

        WAIT=$((TARGET - NOW))
        echo "$(date '+%Y-%m-%d %H:%M:%S') [scheduler] Next refresh in $((WAIT / 3600))h $((WAIT % 3600 / 60))m"
        sleep $WAIT

        echo "$(date '+%Y-%m-%d %H:%M:%S') [scheduler] Running daily screen refresh..."
        python main.py --refresh 2>&1 | tail -5
        echo "$(date '+%Y-%m-%d %H:%M:%S') [scheduler] Refresh complete."
    done
) &

# ── Start web server ──
echo "$(date '+%Y-%m-%d %H:%M:%S') Starting web server on port 8000..."
exec uvicorn server:app --host 0.0.0.0 --port 8000
