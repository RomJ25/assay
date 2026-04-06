FROM python:3.13-slim

WORKDIR /app

ENV TZ=America/New_York
ENV PYTHONUNBUFFERED=1
ENV SCREENER_RESULTS=/app/data/results
ENV SCREENER_CACHE_DB=/app/data/cache.db

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/data/results

CMD ["python", "main.py", "--top", "30"]
