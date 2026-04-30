#!/usr/bin/env bash
# deploy.sh - runs ON the VPS after rsync delivers new code
# Called by GitHub Actions via SSH
set -euo pipefail

APP_DIR="/opt/prata-sys/backend"
HEALTH_URL="http://localhost:8000/api/v1/utils/health-check/"
MAX_RETRIES=3
RETRY_INTERVAL=3

echo "=== prata-sys deploy started at $(date -Iseconds) ==="

# 1. Install/update Python dependencies
echo "--- Installing dependencies ---"
cd "$APP_DIR"
uv sync --frozen

# 2. Run database migrations
echo "--- Running migrations ---"
uv run alembic upgrade head

# 3. Restart backend service
echo "--- Restarting prata-backend ---"
sudo systemctl restart prata-backend

# 4. Health check with retries
echo "--- Health check ---"
for i in $(seq 1 $MAX_RETRIES); do
    sleep $RETRY_INTERVAL
    if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
        echo "Health check passed (attempt $i/$MAX_RETRIES)"
        echo "=== Deploy successful at $(date -Iseconds) ==="
        exit 0
    fi
    echo "Health check failed (attempt $i/$MAX_RETRIES)"
done

echo "=== Deploy FAILED - health check did not pass after $MAX_RETRIES attempts ==="
echo "Check logs: sudo journalctl -u prata-backend -n 50 --no-pager"
exit 1
