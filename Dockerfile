FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data/videos /app/data/audio /app/data/thumbnails /app/data/downloads /app/data/db /app/data/temp

RUN wget -O /app/app/assets/fonts/Roboto-Bold.ttf \
    "https://github.com/google/fonts/raw/main/ofl/roboto/Roboto-Bold.ttf" \
    || true

ENV PYTHONPATH=/app
ENV DATA_DIR=/app/data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
