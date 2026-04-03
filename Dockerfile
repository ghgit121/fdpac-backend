FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONWARNINGS=ignore

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Strip Windows CRLF line endings from the startup script so sh can parse it
# correctly when the file was committed from a Windows machine.
RUN sed -i 's/\r$//' /app/start.sh && chmod +x /app/start.sh

CMD ["sh", "/app/start.sh"]
