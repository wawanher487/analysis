# Gunakan Python 3.10 slim
FROM python:3.10-slim

# Install dependencies sistem untuk build dlib dan unzip
RUN apt-get update && apt-get install -y \
    cmake \
    build-essential \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    unzip \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements.txt
COPY requirements.txt .

# Upgrade pip dan install dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Install gdown versi terbaru untuk mendukung download folder
RUN pip install --no-cache-dir --upgrade gdown

# Copy semua file project ke container
COPY . .

# Buat entrypoint script untuk handle download dataset
RUN chmod +x entrypoint.sh

# Expose port aplikasi
EXPOSE 6734

# Jalankan aplikasi melalui entrypoint
CMD ["./entrypoint.sh"]
