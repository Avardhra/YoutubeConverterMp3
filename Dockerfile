FROM python:3.10-slim

# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /code

# Copy requirements
COPY requirements.txt .

# Paksa update yt-dlp ke versi terbaru
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -U yt-dlp

# Pastikan satu baris dan tidak ada teks [cite]
COPY . .

CMD ["python", "app.py"]