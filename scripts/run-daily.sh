#!/usr/bin/env bash
# Run Assay — S&P 500 value + quality screener. Use from cron:
#   crontab -e
#   30 18 * * 1-5 /path/to/assay/scripts/run-daily.sh >> /tmp/assay.log 2>&1
#
# Runs weekdays at 6:30 PM ET (30 min after market close)

set -euo pipefail
cd "$(dirname "$0")/.."

if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
    docker compose run --rm assay
else
    python main.py --top 30
fi
