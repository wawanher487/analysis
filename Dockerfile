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
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements.txt
COPY requirements.txt .

# Upgrade pip dan install dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Install gdown untuk download file dari Google Drive
RUN pip install gdown

# Download model & dataset dari Google Drive
# Gunakan --folder untuk mendownload semua isi folder Google Drive
RUN gdown --folder https://drive.google.com/drive/folders/1sTfLdQ-mp-00rg2mKayRScKSKh0cvZD- -O /app

# Extract dataset jika dalam format zip (opsional, jika dataset berbentuk zip)
# RUN unzip /app/dataset.zip -d /app/dataset && rm /app/dataset.zip

# Salin semua file project ke container
COPY . .

# Expose port aplikasi
EXPOSE 6734

# Jalankan aplikasi
CMD ["python", "app.py"]
