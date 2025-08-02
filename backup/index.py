# import os
# import cv2
# import numpy as np
# import base64
# import time
# import json
# import logging
# import datetime
# from flask import Flask, render_template, request, jsonify
# from werkzeug.exceptions import BadRequest
# import threading
# import uuid


# # --- Local Module Imports ---
# import config
# from utils import setup_logging, get_and_map_users_from_api
# # Impor semua layanan yang diperlukan, termasuk db_service
# from services import ftp_service, rmq_service, db_service 
# from analysis import face_analyzer

# from werkzeug.middleware.proxy_fix import ProxyFix

# import sys
# import dlib
# import logging

# # --- Initial Setup ---
# setup_logging() # <-- Panggil ini PERTAMA
# logging.info("Flask application starting...")

# # --- PINDAHKAN KODE DEBUGGING KE SINI ---
# logging.info("================== DEBUG INFO ==================")
# logging.info(f"Flask berjalan dengan interpreter Python: {sys.executable}")
# logging.info(f"Flask menggunakan Dlib versi: {dlib.__version__}")
# logging.info(f"Path model Dlib: {config.DLIB_SHAPE_PREDICTOR}")
# logging.info("==============================================")
# logging.info("Flask application starting...")


# app = Flask(__name__)

# app.wsgi_app = ProxyFix(
#     app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
# )
# # --- Load User Data and Models ---
# user_details_map = get_and_map_users_from_api()
# face_analyzer.load_models()

# # --- State Management ---
# last_detection_timestamps = {}
# training_lock = threading.Lock()

# # --- Flask Routes ---

# @app.route('/')
# def index():
#     """Renders the main page with a list of users."""
#     global user_details_map
#     logging.info(f"Request for main page from {request.remote_addr}")

#     # Jika daftar pengguna kosong, coba ambil lagi
#     if not user_details_map:
#         logging.warning("User map is empty. Attempting to re-fetch from API...")
#         user_details_map = get_and_map_users_from_api()

#     users = list(user_details_map.values())
#     if not users:
#         logging.warning("Still no users found after re-fetch attempt. Rendering with an empty list.")
    
#     return render_template('index.html', users=users)

# @app.route('/capture', methods=['POST'])
# def capture():
#     """
#     Handles the capturing and saving of new face images for training.
#     """
#     try:
#         data = request.get_json()
#         if not data or 'image' not in data or 'name' not in data:
#             raise BadRequest("Missing required fields in request.")

#         user_guid = data.get('guid', 'unknown')
#         user_name = data['name']
#         image_data_b64 = data['image'].split(',')[1]

#         user_folder = os.path.join(config.DATASET_PATH, f"{user_name.replace(' ', '_')}_{user_guid}")
#         if not os.path.exists(user_folder):
#             os.makedirs(user_folder)
#             logging.info(f"Created new dataset folder: {user_folder}")

#         img_bytes = base64.b64decode(image_data_b64)
#         img_np = np.frombuffer(img_bytes, np.uint8)
#         img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

#         if img is None:
#             return jsonify({'status': 'error', 'message': 'Invalid image data received.'}), 400

#         image_path = os.path.join(user_folder, f"image_{len(os.listdir(user_folder)) + 1}.jpg")
#         cv2.imwrite(image_path, img)
#         logging.info(f"Successfully saved new image to {image_path}")

#         return jsonify({'status': 'success', 'message': f'Gambar untuk {user_name} telah disimpan!'})

#     except (BadRequest, KeyError) as e:
#         logging.error(f"Bad request in /capture: {e}")
#         return jsonify({'status': 'error', 'message': str(e)}), 400
#     except Exception as e:
#         logging.error(f"Error processing captured image: {e}")
#         return jsonify({'status': 'error', 'message': 'Gagal menyimpan gambar.'}), 500


# @app.route('/train', methods=['GET'])
# def train_model():
#     """
#     Initiates the training process synchronously.
#     Handles concurrent requests by locking the process.
#     """
#     if not training_lock.acquire(blocking=False):
#         logging.warning("Training request received while another training is in progress.")
#         return jsonify({
#             'status': 'error',
#             'message': 'Proses training sedang berjalan. Silakan coba beberapa saat lagi.'
#         }), 409

#     logging.info("Training process initiated by user. Lock acquired.")
#     try:
#         success, message = face_analyzer.train_model()
#         if success:
#             logging.info("Training completed and model reloaded successfully!")
#             return jsonify({'status': 'success', 'message': message})
#         else:
#             logging.warning(f"Training failed: {message}")
#             return jsonify({'status': 'error', 'message': message}), 400
#     except Exception as e:
#         logging.critical(f"An unexpected error occurred during training: {e}", exc_info=True)
#         return jsonify({'status': 'error', 'message': 'Terjadi kesalahan internal saat training.'}), 500
#     finally:
#         training_lock.release()
#         logging.info("Training process finished. Lock released.")


# # @app.route('/recognize_frame', methods=['POST'])
# # def recognize_frame():
# #     """
# #     Receives a video frame, analyzes it for faces, and processes presence if a known user is detected.
# #     """
# #     try:
# #         data = request.get_json()
# #         if not data or 'image' not in data:
# #             return jsonify([])

# #         image_data_b64 = data['image'].split(',')[1]
# #         latitude = data.get('latitude', 0.0)
# #         longitude = data.get('longitude', 0.0)

# #         img_bytes = base64.b64decode(image_data_b64)
# #         img_np = np.frombuffer(img_bytes, np.uint8)
# #         img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

# #         if img is None:
# #             logging.warning("Received an invalid/empty image frame for recognition.")
# #             return jsonify([])

# #     except (IndexError, base64.binascii.Error) as e:
# #         logging.error(f"Could not decode base64 image from request: {e}")
# #         return jsonify([])
# #     except Exception as e:
# #         logging.error(f"Unexpected error processing request for /recognize_frame: {e}")
# #         return jsonify([])

# #     results = face_analyzer.analyze_image_for_faces(img, user_details_map)

# #     if results and results[0].get('guid'):
# #         person = results[0]
# #         user_guid = person['guid']
# #         current_time = time.time()
# #         cooldown_period = config.DETECTION_COOLDOWN_SECONDS

# #         if (current_time - last_detection_timestamps.get(user_guid, 0)) > cooldown_period:
# #             logging.info(f"User '{person.get('name')}' detected. Cooldown passed. Processing...")
# #             last_detection_timestamps[user_guid] = current_time

# #             # --- MODIFICATION START ---
# #             # Draw bounding box and label on the image before uploading
# #             box = person.get('box')
# #             name = person.get('name', 'Unknown')
# #             if box:
# #                 x1, y1, x2, y2 = box
# #                 # Draw the rectangle around the face
# #                 cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
# #                 # Prepare text label
# #                 label = f"{name}"
# #                 # Put the label above the rectangle
# #                 cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
# #                 logging.info(f"Drew bounding box for {name} on the image.")
# #             # --- MODIFICATION END ---

# #             # Encode the modified image (with the box and label) for upload
# #             _, buffer = cv2.imencode('.jpg', img)
# #             image_bytes_for_upload = buffer.tobytes()

# #             timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
# #             remote_filename = f"detection_{user_guid}_{timestamp}.jpg"

# #             logging.info(f"Attempting to upload '{remote_filename}' to FTP...")
# #             if ftp_service.upload_to_ftp(image_bytes_for_upload, remote_filename):
# #                 logging.info(f"FTP STATUS: SUCCESS uploading '{remote_filename}'.")
# #                 image_url = f"{config.FTP_BASE_URL}{config.FTP_FOLDER}/{remote_filename}"
# #                 image_url_db = f"{remote_filename}"
# #                 logging.info(f"Image URL for database: {image_url_db}")
# #                 # Menyimpan hasil deteksi ke MongoDB
# #                 logging.info(f"Saving detection for '{person.get('name')}' to database...")
# #                 db_service.save_detection_history(person, image_url_db)

# #                 # Mengirim pesan ke RMQ #1 (Presensi)
# #                 presence_payload = rmq_service.create_presence_payload(
# #                     user_guid=user_guid,
# #                     user_name=person.get('name', 'N/A'),
# #                     image_url=image_url,
# #                     latitude=latitude,
# #                     longitude=longitude
# #                 )
# #                 if rmq_service.publish_to_rmq(presence_payload):
# #                     logging.info("RMQ #1 STATUS: SUCCESS sending presence message.")
# #                     results[0]['presence_sent'] = True
# #                 else:
# #                     logging.error("RMQ #1 STATUS: FAILED to send presence message.")
# #                 # Mengirim pesan ke RMQ #2 (Notifikasi File)
# #                 notification_payload = rmq_service.create_file_notification_payload(
# #                     filename=remote_filename
# #                 )
# #                 if rmq_service.publish_file_notification(notification_payload):
# #                     logging.info("RMQ #2 STATUS: SUCCESS sending file notification.")
# #                 else:
# #                     logging.error("RMQ #2 STATUS: FAILED to send file notification.")
# #             else:
# #                 logging.error(f"FTP STATUS: FAILED. DB and RMQ messages will not be sent.")
# #         else:
# #             logging.info(f"User '{person.get('name')}' detected. Cooldown active. Skipping.")

# #     return jsonify(results)

# @app.route('/recognize_frame', methods=['POST'])
# def recognize_frame():
#     """
#     Menerima frame, menganalisisnya, dan memproses kehadiran jika pengguna dikenal.
#     """
#     try:
#         data = request.get_json()
#         if not data or 'image' not in data:
#             return jsonify([])

#         image_data_b64 = data['image'].split(',')[1]
#         latitude = data.get('latitude', 0.0)
#         longitude = data.get('longitude', 0.0)

#         img_bytes = base64.b64decode(image_data_b64)
#         img_np = np.frombuffer(img_bytes, np.uint8)
#         img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

#         if img is None:
#             logging.warning("Menerima frame gambar yang tidak valid.")
#             return jsonify([])

#     except Exception as e:
#         logging.error(f"Error saat memproses request: {e}")
#         return jsonify([])

#     results = face_analyzer.analyze_image_for_faces(img, user_details_map)

#     if results and results[0].get('guid'):
#         person = results[0]
#         user_guid = person['guid']
#         current_time = time.time()
#         cooldown_period = config.DETECTION_COOLDOWN_SECONDS

#         if (current_time - last_detection_timestamps.get(user_guid, 0)) > cooldown_period:
#             logging.info(f"User '{person.get('nama')}' terdeteksi. Memproses...")
#             last_detection_timestamps[user_guid] = current_time

#             # --- MODIFICATION START (Ganti bagian ini) ---
#             # Gambar kotak pembatas dan label yang lebih detail pada gambar
#             box = person.get('box')
#             if box:
#                 # Ambil semua data hasil analisis
#                 name = person.get('nama', 'Tidak Dikenal')
#                 mood = person.get('mood', 'N/A')
#                 fatigue = person.get('keletihan', 0.0)
                
#                 # Siapkan teks label yang lengkap
#                 label = f"{name} | {mood} | Keletihan: {fatigue:.1f}%"
                
#                 # Tentukan warna kotak berdasarkan mood
#                 color = (0, 255, 0) # Hijau untuk default (Netral, Senang)
#                 if mood == 'Marah': color = (0, 0, 255) # Merah
#                 elif mood == 'Sedih': color = (255, 0, 0) # Biru

#                 (x1, y1, w, h) = box
#                 x2, y2 = x1 + w, y1 + h

#                 # Gambar kotak di sekeliling wajah
#                 cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
#                 cv2.rectangle(img, (x1, y2 - 35), (x2, y2), color, cv2.FILLED)
#                 cv2.putText(img, label, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 255), 1)
                
#                 logging.info(f"Label lengkap digambar untuk {name} pada gambar.")
#             # --- MODIFICATION END ---

#             # Encode gambar yang telah dimodifikasi untuk diunggah
#             _, buffer = cv2.imencode('.jpg', img)
#             image_bytes_for_upload = buffer.tobytes()

#             timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
#             remote_filename = f"detection_{user_guid}_{timestamp}.jpg"

#             logging.info(f"Mencoba mengunggah '{remote_filename}' ke FTP...")
#             if ftp_service.upload_to_ftp(image_bytes_for_upload, remote_filename):
#                 logging.info(f"FTP STATUS: BERHASIL mengunggah '{remote_filename}'.")
#                 image_url = f"{config.FTP_BASE_URL}{config.FTP_FOLDER}/{remote_filename}"
#                 image_url_db = f"{remote_filename}"
#                 logging.info(f"URL gambar untuk database: {image_url_db}")
                
#                 # Menyimpan hasil deteksi (yang sekarang lebih kaya) ke MongoDB
#                 logging.info(f"Menyimpan deteksi untuk '{person.get('nama')}' ke database...")
#                 db_service.save_detection_history(person, image_url_db)

#                 # Mengirim pesan ke RMQ #1 (Presensi)
#                 presence_payload = rmq_service.create_presence_payload(
#                     user_guid=user_guid,
#                     user_name=person.get('nama', 'N/A'),
#                     image_url=image_url,
#                     latitude=latitude,
#                     longitude=longitude
#                 )
#                 if rmq_service.publish_to_rmq(presence_payload):
#                     logging.info("RMQ #1 STATUS: BERHASIL mengirim pesan presensi.")
#                     results[0]['presence_sent'] = True
#                 else:
#                     logging.error("RMQ #1 STATUS: GAGAL mengirim pesan presensi.")
                
#                 # Mengirim pesan ke RMQ #2 (Notifikasi File untuk Consumer)
#                 notification_payload = rmq_service.create_file_notification_payload(
#                     filename=remote_filename
#                 )
#                 if rmq_service.publish_file_notification(notification_payload):
#                     logging.info("RMQ #2 STATUS: BERHASIL mengirim notifikasi file.")
#                 else:
#                     logging.error("RMQ #2 STATUS: GAGAL mengirim notifikasi file.")
#             else:
#                 logging.error(f"FTP STATUS: GAGAL. Pesan DB dan RMQ tidak akan dikirim.")
#         else:
#             logging.info(f"User '{person.get('nama')}' terdeteksi. Cooldown aktif. Lewati.")

#     return jsonify(results)

# @app.route('/get_training_stats')
# def get_training_stats():
#     """Endpoint to get statistics about the training dataset, such as image count."""
#     logging.info("Request received for training stats.")
#     try:
#         image_count = 0
#         if os.path.exists(config.DATASET_PATH):
#             for user_folder in os.listdir(config.DATASET_PATH):
#                 user_path = os.path.join(config.DATASET_PATH, user_folder)
#                 if os.path.isdir(user_path):
#                     image_count += len([
#                         name for name in os.listdir(user_path)
#                         if name.lower().endswith(('.png', '.jpg', '.jpeg'))
#                     ])
#         logging.info(f"Calculated image count: {image_count}")
#         return jsonify({'image_count': image_count})
#     except Exception as e:
#         logging.error(f"Error calculating training stats: {e}", exc_info=True)
#         return jsonify({'error': str(e)}), 500

# # --- Main Execution ---
# if __name__ == '__main__':
#     # Pastikan untuk menggunakan server produksi seperti Gunicorn atau Waitress saat deploy
#     app.run(host='0.0.0.0', port=config.APP_PORT, debug=False, threaded=True)

# index.py (Versi Final Gabungan)

# --- Python Standard Library Imports ---
import os
import base64
import time
import json
import logging
import datetime
import threading
import uuid
import sys

# --- Third-party Library Imports ---
import cv2
import numpy as np
import dlib
from flask import Flask, render_template, request, jsonify
from werkzeug.exceptions import BadRequest
from werkzeug.middleware.proxy_fix import ProxyFix

# --- Local Module Imports ---
import config
# Asumsi Anda punya file-file ini
from utils import setup_logging, get_and_map_users_from_api
from services import ftp_service, rmq_service, db_service 
# --- PERBAIKAN 1: Impor KELAS, bukan modul ---
from analysis.analysis import FaceAnalyzer

# --- Initial Setup ---
setup_logging()
logging.info("Flask application starting...")

# --- Debug Info ---
logging.info("================== DEBUG INFO ==================")
logging.info(f"Flask berjalan dengan interpreter Python: {sys.executable}")
logging.info(f"Flask menggunakan Dlib versi: {dlib.__version__}")
logging.info(f"Path model Dlib dari config: {config.DLIB_SHAPE_PREDICTOR}")
logging.info("==============================================")

# --- PERBAIKAN 2: Buat objek analyzer dan muat model ---
face_analyzer = FaceAnalyzer()
face_analyzer.load_models()

# Inisialisasi Aplikasi Flask
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Muat data user dari API
user_details_map = get_and_map_users_from_api()

# --- State Management ---
last_detection_timestamps = {}
training_lock = threading.Lock()

# --- Flask Routes ---

@app.route('/')
def index():
    """Menampilkan halaman utama dengan daftar pengguna."""
    global user_details_map
    if not user_details_map:
        logging.warning("User map kosong, mencoba mengambil ulang dari API...")
        user_details_map = get_and_map_users_from_api()
    return render_template('index.html', users=list(user_details_map.values()))

@app.route('/capture', methods=['POST'])
def capture():
    """Menangani penyimpanan gambar baru untuk training."""
    try:
        data = request.get_json()
        if not data or 'image' not in data or 'name' not in data or 'guid' not in data:
            raise BadRequest("Data tidak lengkap: 'image', 'name', 'guid' diperlukan.")

        user_guid = data['guid']
        user_name = data['name']
        image_data_b64 = data['image'].split(',')[1]

        user_folder = os.path.join(config.DATASET_PATH, f"{user_name.replace(' ', '_')}_{user_guid}")
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)
            logging.info(f"Membuat folder dataset baru: {user_folder}")

        img_bytes = base64.b64decode(image_data_b64)
        img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)

        if img is None:
            return jsonify({'status': 'error', 'message': 'Data gambar tidak valid.'}), 400

        image_path = os.path.join(user_folder, f"capture_{int(time.time())}.jpg")
        cv2.imwrite(image_path, img)
        logging.info(f"Berhasil menyimpan gambar baru ke {image_path}")

        return jsonify({'status': 'success', 'message': f'Gambar untuk {user_name} telah disimpan!'})
    except (BadRequest, KeyError) as e:
        logging.error(f"Request buruk di /capture: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except Exception as e:
        logging.error(f"Error saat memproses gambar tangkapan: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Gagal menyimpan gambar.'}), 500

@app.route('/train', methods=['GET'])
def train_model():
    """Memicu proses training model AI."""
    if not training_lock.acquire(blocking=False):
        return jsonify({'status': 'error', 'message': 'Proses training sedang berjalan.'}), 409
    
    logging.info("Proses training dipicu oleh pengguna...")
    try:
        success, message = face_analyzer.train_model()
        status_code = 200 if success else 400
        return jsonify({'status': 'success' if success else 'error', 'message': message}), status_code
    except Exception as e:
        logging.critical(f"Terjadi error tak terduga saat training: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Terjadi kesalahan internal saat training.'}), 500
    finally:
        training_lock.release()
        logging.info("Proses training selesai, lock dilepaskan.")

@app.route('/recognize_frame', methods=['POST'])
def recognize_frame():
    """Menerima frame, menganalisis, dan memproses kehadiran."""
    try:
        data = request.get_json()
        image_data_b64 = data['image'].split(',')[1]
        latitude = data.get('latitude', 0.0)
        longitude = data.get('longitude', 0.0)
        img_bytes = base64.b64decode(image_data_b64)
        img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            return jsonify([])
    except Exception as e:
        logging.error(f"Error memproses request frame: {e}")
        return jsonify([])

    # Memanggil analysis.py yang sudah disempurnakan
    results = face_analyzer.recognize_fast(img, user_details_map)

    if results and results[0].get('guid'):
        person = results[0]
        user_guid = person['guid']
        current_time = time.time()
        
        if (current_time - last_detection_timestamps.get(user_guid, 0)) > config.DETECTION_COOLDOWN_SECONDS:
            last_detection_timestamps[user_guid] = current_time
            logging.info(f"User '{person.get('nama')}' terdeteksi. Memproses...")

            # Menggambar label yang lebih kaya dari hasil analisis baru
            box = person.get('box')
            if box:
                name = person.get('nama', 'Tidak Dikenal')
                mood = person.get('mood', 'N/A')
                fatigue = person.get('keletihan', 0.0)
                label = f"{name} | {mood} | Keletihan: {fatigue:.1f}%"
                color = (0, 255, 0)
                if mood == 'Marah': color = (0, 0, 255)
                elif mood == 'Sedih': color = (255, 0, 0)

                (x1, y1, w, h) = box
                x2, y2 = x1 + w, y1 + h
                cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                cv2.rectangle(img, (x1, y2 - 35), (x2, y2), color, cv2.FILLED)
                cv2.putText(img, label, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 255), 1)

            # Encode gambar yang telah dimodifikasi untuk diunggah
            _, buffer = cv2.imencode('.jpg', img)
            image_bytes_for_upload = buffer.tobytes()
            remote_filename = f"detection_{user_guid}_{int(current_time)}.jpg"

            if ftp_service.upload_to_ftp(image_bytes_for_upload, remote_filename):
                image_url = f"{config.FTP_BASE_URL}{config.FTP_FOLDER}/{remote_filename}"
                
                # Menyimpan hasil deteksi (yang sekarang lebih kaya) ke MongoDB
                db_service.save_detection_history(person, remote_filename)

                # Mengirim pesan ke RMQ #1 (Presensi)
                presence_payload = rmq_service.create_presence_payload(
                    user_guid=user_guid, user_name=person.get('nama', 'N/A'),
                    image_url=image_url, latitude=latitude, longitude=longitude
                )
                if rmq_service.publish_to_rmq(presence_payload):
                    results[0]['presence_sent'] = True
                
                # Mengirim pesan ke RMQ #2 (Notifikasi File)
                notification_payload = rmq_service.create_file_notification_payload(
                    filename=remote_filename
                )
                rmq_service.publish_file_notification(notification_payload)
            else:
                logging.error(f"FTP GAGAL. Pesan DB dan RMQ tidak akan dikirim.")
        else:
            logging.info(f"User '{person.get('nama')}' terdeteksi. Cooldown aktif.")

    return jsonify(results)

@app.route('/get_training_stats')
def get_training_stats():
    """Mendapatkan statistik jumlah gambar di dataset."""
    try:
        image_count = 0
        if os.path.exists(config.DATASET_PATH):
            for user_folder in os.listdir(config.DATASET_PATH):
                user_path = os.path.join(config.DATASET_PATH, user_folder)
                if os.path.isdir(user_path):
                    image_count += len([f for f in os.listdir(user_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))])
        return jsonify({'image_count': image_count})
    except Exception as e:
        logging.error(f"Error menghitung statistik training: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

# --- Main Execution ---
if __name__ == '__main__':
    # Untuk production, gunakan server seperti Gunicorn atau Waitress
    app.run(host='0.0.0.0', port=config.APP_PORT, debug=False, threaded=True)
