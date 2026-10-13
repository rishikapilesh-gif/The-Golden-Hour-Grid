#!/usr/bin/env bash
set -e

echo "=========================================================="
echo " Starting Golden Hour Grid Web Application Service"
echo "=========================================================="

# 1. Seed synthetic hospital data and accounts if in demo mode
if [ "${DEMO_MODE:-true}" = "true" ]; then
    echo "Initializing and seeding synthetic demonstration dataset..."
    python scripts/seed_demo_data.py || true
    python scripts/seed_demo_users.py \
        --ambulance-password "${DEMO_AMBULANCE_PASSWORD:-AmbDemoPass2026!}" \
        --hospital-password "${DEMO_HOSPITAL_PASSWORD:-HospDemoPass2026!}" || true
fi

# 2. Resolve port from environment or fallback to 8000
BIND_PORT="${PORT:-8000}"
BIND_HOST="${HOST:-0.0.0.0}"

echo "Launching Uvicorn production server on ${BIND_HOST}:${BIND_PORT}..."
exec uvicorn backend.app.main:app --host "$BIND_HOST" --port "$BIND_PORT"
