FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    START_SIMULATOR=1 \
    SIM_INTERVAL=2 \
    PORT=8050 \
    DATA_DIR=/app/data

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8050

# One worker is intentional: the in-process simulator and SQLite database
# should have a single owner. Threads allow concurrent Dash requests.
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-8050} --workers 1 --threads 4 --timeout 120 --access-logfile - --error-logfile - app:server"]
