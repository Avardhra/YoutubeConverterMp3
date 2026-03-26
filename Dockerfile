FROM python:3.10-slim

# Install FFmpeg DAN Node.js
RUN apt-get update && apt-get install -y \
    ffmpeg \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY requirements.txt .

# Pastikan yt-dlp selalu versi terbaru
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -U yt-dlp

COPY . .

CMD ["python", "app.py"]