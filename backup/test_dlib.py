# test_dlib.py
import dlib
import os

# Ganti dengan path absolut yang SAMA PERSIS seperti di config.py Anda
path_model = r"E:\Asep Trisna Setiawan\RISET\proyek_presensi_ai\app_training\shape_predictor_68_face_landmarks.dat"

print(f"Mencoba memuat model dari: {path_model}")

# Cek apakah file ada di path tersebut
if os.path.exists(path_model):
    print("File ditemukan. Mencoba memuat...")
    try:
        predictor = dlib.shape_predictor(path_model)
        print(">>> SUKSES! Model Dlib berhasil dimuat dari path ini.")
    except Exception as e:
        print(f">>> GAGAL! File ada tapi tidak bisa dimuat. Error: {e}")
else:
    print(">>> GAGAL! File tidak ditemukan di path yang diberikan.")