FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY backend /app/backend
COPY worker /app/worker

RUN pip install --no-cache-dir -r /app/worker/requirements.txt

ENV PYTHONPATH=/app/backend:/app/worker
ENV PYTHONUNBUFFERED=1

WORKDIR /app/worker
CMD ["python", "worker_run.py"]