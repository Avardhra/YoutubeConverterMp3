FROM python:3.10-slim

# Instal FFmpeg DAN Node.js sebagai runtime JavaScript
RUN apt-get update && apt-get install -y \
    ffmpeg \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY requirements.txt .

# Paksa update yt-dlp untuk mendapatkan patch bypass terbaru
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -U yt-dlp

COPY . .

CMD ["python", "app.py"]