FROM python:3.10-slim

# Install FFmpeg versi Linux (WAJIB)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Railway butuh gunicorn agar stabil
RUN pip install gunicorn

CMD gunicorn --bind 0.0.0.0:$PORT app:app