FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONWARNINGS=ignore

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Start with comprehensive logging for debugging
CMD sh -c "\
    echo '========== FDPAC Backend Container Starting =========='; \
    echo '[INFO] Python version:'; \
    python --version; \
    echo '[INFO] Current working directory:'; \
    pwd; \
    echo '[INFO] Environment check:'; \
    if [ -z \"\$DATABASE_URL\" ]; then echo '[ERROR] DATABASE_URL not set!'; exit 1; fi; \
    echo '[INFO] DATABASE_URL is set'; \
    if [ -z \"\$SECRET_KEY\" ]; then echo '[ERROR] SECRET_KEY not set!'; exit 1; fi; \
    echo '[INFO] SECRET_KEY is set'; \
    echo ''; \
    echo '[MIGRATIONS] Starting database migrations with 60s timeout...'; \
    if timeout 60 alembic upgrade head; then echo '[MIGRATIONS] ✓ Migrations completed successfully!'; else echo '[ERROR] Migrations failed or timed out!'; exit 1; fi; \
    echo ''; \
    echo '[STARTUP] Starting Uvicorn server...'; \
    echo \"[STARTUP] Binding to 0.0.0.0:\${PORT:-10000}\"; \
    exec uvicorn app.main:app --host 0.0.0.0 --port \${PORT:-10000} --timeout-keep-alive 75\
"
