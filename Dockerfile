FROM python:3.10-slim

# WAJIB: Install FFmpeg agar konversi MP3 bisa jalan
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY requirements.txt .

# Paksa update yt-dlp untuk bypass proteksi YouTube terbaru
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -U yt-dlp

COPY . .

CMD ["python", "app.py"]