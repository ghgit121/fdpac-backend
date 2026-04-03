FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONWARNINGS=ignore

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Start with migrations and timeout; if migrations fail, the startup fails immediately (better than hanging)
CMD sh -c "echo 'Starting database migrations...' && alembic upgrade head && echo 'Migrations complete. Starting Uvicorn...' && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000} --timeout-keep-alive 75"