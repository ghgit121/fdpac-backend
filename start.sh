#!/bin/sh
set -e

echo "========== FDPAC Backend Container Starting =========="

echo "[INFO] Python version:"
python --version

echo ""
echo "[INFO] Current working directory:"
pwd

echo ""
echo "[INFO] Environment check:"

# Check DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo "[ERROR] DATABASE_URL is not set!"
    exit 1
fi
echo "[INFO] DATABASE_URL is set"

# Accept either JWT_SECRET or SECRET_KEY
if [ -z "$JWT_SECRET" ] && [ -z "$SECRET_KEY" ]; then
    echo "[ERROR] JWT_SECRET (or SECRET_KEY) is not set!"
    exit 1
fi
echo "[INFO] JWT secret is set"

echo ""

# ---------- Migrations ----------
if [ "$SKIP_MIGRATIONS" = "true" ]; then
    echo "[MIGRATIONS] SKIP_MIGRATIONS=true — skipping migrations."
    echo "[MIGRATIONS] Run 'alembic upgrade head' manually."

elif [ -n "$MIGRATION_DATABASE_URL" ]; then
    echo "[MIGRATIONS] Starting DDL migrations using MIGRATION_DATABASE_URL..."
    
    if timeout 60 alembic upgrade head; then
        echo "[MIGRATIONS] Success: Database schema is up to date."
    else
        echo "[ERROR] Migrations failed or timed out (60s limit)."
        echo "[HINT] Ensure MIGRATION_DATABASE_URL is a 'Direct' connection (e.g. port 5432, not 6543)."
        exit 1
    fi

else
    echo "[MIGRATIONS] MIGRATION_DATABASE_URL not set; trying DATABASE_URL..."
    
    # Check if DATABASE_URL looks like a pooler (common in Neon/Supabase)
    case "$DATABASE_URL" in 
        *pooler*|*:6543*)
            echo "[WARNING] DATABASE_URL appears to be a pooler. DDL might fail."
            echo "[WARNING] Set MIGRATION_DATABASE_URL to a direct connection URL for stability."
            ;;
    esac

    if timeout 60 alembic upgrade head; then
        echo "[MIGRATIONS] Success: Database schema is up to date."
    else
        echo "[ERROR] Migrations failed or timed out (60s limit)."
        echo "[HINT] If using Neon/Supabase, set MIGRATION_DATABASE_URL to the direct connection URL."
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
