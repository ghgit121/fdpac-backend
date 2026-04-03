#!/bin/sh
set -e

echo "========== FDPAC Backend Container Starting =========="

echo "[INFO] Python version:"
python --version

echo "[INFO] Current working directory:"
pwd

echo "[INFO] Environment check:"

if [ -z "$DATABASE_URL" ]; then
    echo "[ERROR] DATABASE_URL is not set!"
    exit 1
fi
echo "[INFO] DATABASE_URL is set"

# Accept either JWT_SECRET or SECRET_KEY (both are mapped by the Python config)
if [ -z "$JWT_SECRET" ] && [ -z "$SECRET_KEY" ]; then
    echo "[ERROR] JWT_SECRET (or SECRET_KEY) is not set!"
    exit 1
fi
echo "[INFO] JWT secret is set"

echo ""
if [ "$SKIP_MIGRATIONS" = "true" ]; then
    echo "[MIGRATIONS] SKIP_MIGRATIONS=true — skipping migrations."
    echo "[MIGRATIONS] Run 'alembic upgrade head' manually against the direct connection URL."
elif [ -n "$MIGRATION_DATABASE_URL" ]; then
    echo "[MIGRATIONS] Using MIGRATION_DATABASE_URL for DDL (session/direct pooler)."
    echo "[MIGRATIONS] Starting database migrations with 60s timeout..."
    if timeout 60 alembic upgrade head; then
        echo "[MIGRATIONS] Migrations completed successfully!"
    else
        echo "[ERROR] Migrations failed or timed out after 60s!"
        echo "[HINT] Verify MIGRATION_DATABASE_URL is reachable (direct connection, not pooler)."
        exit 1
    fi
else
    echo "[MIGRATIONS] MIGRATION_DATABASE_URL not set; using DATABASE_URL for migrations."
    echo "[MIGRATIONS] WARNING: if DATABASE_URL uses Supabase transaction pooler (port 6543)"
    echo "[MIGRATIONS]          set MIGRATION_DATABASE_URL to the direct connection URL"
    echo "[MIGRATIONS]          or set SKIP_MIGRATIONS=true and run migrations manually."
    echo "[MIGRATIONS] Starting database migrations with 60s timeout..."
    if timeout 60 alembic upgrade head; then
        echo "[MIGRATIONS] Migrations completed successfully!"
    else
        echo "[ERROR] Migrations failed or timed out after 60s!"
        echo "[HINT] Verify DATABASE_URL is reachable and uses sslmode=require for Supabase."
        exit 1
    fi
fi

echo ""
echo "[STARTUP] Starting Uvicorn server..."
echo "[STARTUP] Binding to 0.0.0.0:${PORT:-10000}"
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-10000}" \
    --timeout-keep-alive 75
