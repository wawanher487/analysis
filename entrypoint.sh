#!/bin/bash
set -e

# Download dataset dari Google Drive jika folder kosong
if [ ! -d "/app/dataset" ] || [ -z "$(ls -A /app/dataset)" ]; then
    echo "Dataset belum ada, mencoba download dari Google Drive..."
    if ! gdown --folder https://drive.google.com/drive/folders/1sTfLdQ-mp-00rg2mKayRScKSKh0cvZD-; then
        echo "Gagal download dataset dari Google Drive! Menggunakan dataset lokal jika tersedia..."
    fi
else
    echo "Dataset sudah ada, skip download."
fi

# Jalankan aplikasi Python
exec python app.py
