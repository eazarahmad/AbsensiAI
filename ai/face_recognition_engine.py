"""
Modul Face Recognition Engine
Mendukung face_recognition library dengan OpenCV Haar Cascade & DNN fallback.
"""

import os
import io
import base64
import logging
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOADS_DIR = BASE_DIR / "uploads" / "faces"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Haar cascade classifier path
HAAR_CASCADE_PATH = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
face_cascade = cv2.CascadeClassifier(HAAR_CASCADE_PATH)

# Cek ketersediaan face_recognition library & models
FACE_REC_AVAILABLE = False
try:
    import face_recognition_models
    import face_recognition
    FACE_REC_AVAILABLE = True
    logger.info("Library 'face_recognition' (dlib) aktif.")
except (ImportError, SystemExit, Exception, BaseException) as e:
    FACE_REC_AVAILABLE = False
    logger.warning(f"face_recognition belum lengkap ({e}). Menggunakan OpenCV AI feature engine sebagai fallback.")


def decode_image(image_input):
    """
    Mengonversi input (path file, base64 data-url, bytes, atau numpy array)
    menjadi gambar OpenCV (BGR) dan RGB.
    """
    if isinstance(image_input, np.ndarray):
        bgr = image_input.copy()
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        return bgr, rgb

    if isinstance(image_input, str):
        # Cek jika base64
        if "base64," in image_input:
            image_input = image_input.split("base64,")[1]
        
        # Coba decode base64
        try:
            image_bytes = base64.b64decode(image_input)
            nparr = np.frombuffer(image_bytes, np.uint8)
            bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if bgr is not None:
                rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
                return bgr, rgb
        except Exception:
            pass

        # Coba baca dari file path
        if os.path.exists(image_input):
            bgr = cv2.imread(image_input)
            if bgr is not None:
                rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
                return bgr, rgb

    if isinstance(image_input, bytes):
        nparr = np.frombuffer(image_input, np.uint8)
        bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if bgr is not None:
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            return bgr, rgb

    raise ValueError("Format gambar tidak didukung atau gambar rusak.")


def _opencv_extract_embedding(face_roi):
    """
    Feature extractor berbasis OpenCV (Multi-region Block Histogram 128-dimensi)
    jika dlib/face_recognition models belum terpasang.
    """
    gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY) if len(face_roi.shape) == 3 else face_roi
    resized = cv2.resize(gray, (64, 64))
    equalized = cv2.equalizeHist(resized)
    
    # 4x4 Grid = 16 patch x 8 bins = 128 dimensi embedding
    h, w = equalized.shape
    grid_h, grid_w = h // 4, w // 4
    features = []
    for r in range(4):
        for c in range(4):
            cell = equalized[r * grid_h:(r + 1) * grid_h, c * grid_w:(c + 1) * grid_w]
            hist = cv2.calcHist([cell], [0], None, [8], [0, 256]).flatten()
            features.extend(hist)
            
    feat_arr = np.array(features, dtype=np.float32)
    norm = np.linalg.norm(feat_arr)
    if norm > 0:
        feat_arr = feat_arr / norm
    return feat_arr.tolist()


def detect_faces_opencv(bgr_image):
    """Deteksi posisi wajah menggunakan OpenCV Haar Cascade."""
    gray = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(60, 60)
    )
    # Konversi format (x, y, w, h) ke (top, right, bottom, left)
    boxes = []
    for (x, y, w, h) in faces:
        boxes.append((y, x + w, y + h, x))
    return boxes


def encode_face(image_input):
    """
    Mengekstrak face embedding dari gambar input.
    Mengembalikan list 128 float embedding dan bounding box wajah, atau (None, None).
    """
    try:
        bgr, rgb = decode_image(image_input)
    except Exception as e:
        logger.error(f"Error membaca gambar: {e}")
        return None, None

    if FACE_REC_AVAILABLE:
        try:
            boxes = face_recognition.face_locations(rgb, model="hog")
            if not boxes:
                # Coba deteksi dengan OpenCV jika HOG luput
                boxes = detect_faces_opencv(bgr)
            
            if boxes:
                encodings = face_recognition.face_encodings(rgb, known_face_locations=boxes)
                if encodings:
                    return encodings[0].tolist(), boxes[0]
            
            # Fallback jika gambar sudah berupa crop pasfoto/portrait
            h, w = rgb.shape[:2]
            full_box = (0, w, h, 0)
            encodings = face_recognition.face_encodings(rgb, known_face_locations=[full_box])
            if encodings:
                return encodings[0].tolist(), full_box
        except Exception as e:
            logger.error(f"Error face_recognition encode: {e}")

    # Fallback OpenCV
    boxes = detect_faces_opencv(bgr)
    if boxes:
        top, right, bottom, left = boxes[0]
        face_roi = bgr[max(0, top):bottom, max(0, left):right]
        if face_roi.size > 0:
            embedding = _opencv_extract_embedding(face_roi)
            return embedding, (top, right, bottom, left)
    elif bgr is not None and bgr.size > 0:
        h, w = bgr.shape[:2]
        embedding = _opencv_extract_embedding(bgr)
        return embedding, (0, w, h, 0)

    return None, None


def register_face(id_siswa, image_input, filename_prefix="face"):
    """
    Menyimpan foto wajah siswa ke storage dan menghasilkan face encoding.
    Mengembalikan (relative_file_path, face_encoding).
    """
    bgr, rgb = decode_image(image_input)
    encoding, box = encode_face(bgr)

    filename = f"{filename_prefix}_{id_siswa}.jpg"
    target_path = UPLOADS_DIR / filename

    # Simpan gambar
    cv2.imwrite(str(target_path), bgr)
    relative_path = f"/uploads/faces/{filename}"

    return relative_path, encoding


def _calculate_similarity(enc1, enc2):
    """
    Menghitung jarak dan confidence similarity antara dua vektor embedding.
    """
    arr1 = np.array(enc1, dtype=np.float32)
    arr2 = np.array(enc2, dtype=np.float32)

    dist = float(np.linalg.norm(arr1 - arr2))

    if FACE_REC_AVAILABLE:
        tolerance = 0.6
        if dist > tolerance:
            confidence = max(0.0, (1.0 - dist) * 100)
            is_match = False
        else:
            confidence = (1.0 - (dist / (2.0 * tolerance))) * 100
            is_match = True
    else:
        # Multi-block histogram threshold: 0.28
        tolerance = 0.28
        if dist < tolerance:
            is_match = True
            confidence = max(60.0, (1.0 - (dist / tolerance)) * 40.0 + 60.0)
        else:
            is_match = False
            confidence = max(0.0, (1.0 - (dist / 2.0)) * 60.0)

    return bool(is_match), round(float(confidence), 2), dist


def recognize_face(frame_input, known_siswa_dict, tolerance=0.55):
    """
    Mencocokan frame kamera dengan database wajah siswa.
    
    known_siswa_dict: {
        'id_siswa': {
            'nama': '...',
            'kelas': '...',
            'nis': '...',
            'face_encoding': [...]
        }
    }
    
    Returns: dict hasil matching
    """
    try:
        bgr, rgb = decode_image(frame_input)
    except Exception as e:
        return {
            "success": False,
            "message": f"Gagal memproses frame kamera: {str(e)}",
            "match": False
        }

    # Cari encoding dari frame
    query_encoding, box = encode_face(bgr)
    if query_encoding is None:
        return {
            "success": False,
            "message": "Tidak ada wajah terdeteksi pada kamera.",
            "match": False,
            "face_detected": False
        }

    best_match_id = None
    highest_confidence = 0.0
    best_dist = float("inf")

    for id_siswa, siswa_info in known_siswa_dict.items():
        stored_enc = siswa_info.get("face_encoding")
        if not stored_enc:
            continue

        is_match, conf, dist = _calculate_similarity(query_encoding, stored_enc)
        if conf > highest_confidence:
            highest_confidence = conf
            best_dist = dist
            if is_match:
                best_match_id = id_siswa

    if best_match_id:
        siswa_data = known_siswa_dict[best_match_id]
        return {
            "success": True,
            "match": True,
            "message": f"Wajah dikenali: {siswa_data.get('nama')}",
            "id_siswa": best_match_id,
            "nama": siswa_data.get("nama"),
            "kelas": siswa_data.get("kelas"),
            "nis": siswa_data.get("nis"),
            "confidence": highest_confidence,
            "box": box
        }
    else:
        return {
            "success": True,
            "match": False,
            "message": "Wajah tidak terdaftar",
            "confidence": highest_confidence,
            "box": box
        }
