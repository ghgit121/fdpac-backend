FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONWARNINGS=ignore

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Start with comprehensive logging for debugging
CMD sh -c "echo '========== FDPAC Backend Container Starting ==========' && \
    echo '[INFO] Python version:' && python --version && \
    echo '[INFO] Current working directory:' && pwd && \
    echo '[INFO] Environment variables (DATABASE_URL first 50 chars):' && \
    echo \"[INFO] DATABASE_URL: \${DATABASE_URL:0:50}...\" && \
    echo '[INFO] SECRET_KEY set:' && [ -n \"\$SECRET_KEY\" ] && echo 'YES' || echo 'NO (ERROR!)' && \
    echo '' && \
    echo '[MIGRATIONS] Starting database migrations with 60s timeout...' && \
    timeout 60 alembic upgrade head && echo '[MIGRATIONS] ✓ Migrations completed successfully!' || (echo '[ERROR] Migrations failed or timed out!' && exit 1) && \
    echo '' && \
    echo '[STARTUP] Starting Uvicorn server...' && \
    echo \"[STARTUP] Binding to 0.0.0.0:\${PORT:-10000}\" && \
    exec uvicorn app.main:app --host 0.0.0.0 --port \${PORT:-10000} --timeout-keep-alive 75"