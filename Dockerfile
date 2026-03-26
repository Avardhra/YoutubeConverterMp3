FROM python:3.10-slim

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -U yt-dlp

COPY . .

# 🔥 Gunicorn pakai PORT dari Railway
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120"]