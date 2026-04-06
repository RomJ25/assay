#!/usr/bin/env bash
# Run the S&P 500 screener. Use from cron:
#   crontab -e
#   30 18 * * 1-5 /path/to/StockScreener/scripts/run-daily.sh >> /tmp/screener.log 2>&1
#
# Runs weekdays at 6:30 PM ET (30 min after market close)

set -euo pipefail
cd "$(dirname "$0")/.."

if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
    docker compose run --rm screener
else
    python main.py --top 30
fi
