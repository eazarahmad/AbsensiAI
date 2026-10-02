"""
Firebase Configuration and Database Client
Mendukung Firebase Realtime Database (Admin SDK & REST API Realtime Sync)
serta Local JSON Cache otomatis.
"""

import os
import json
import logging
from pathlib import Path
import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

logger = logging.getLogger(__name__)

# Konfigurasi Firebase Web dari PRD & Firebase Console (Region Singapore)
FIREBASE_WEB_CONFIG = {
    "apiKey": os.getenv("FIREBASE_API_KEY", "AIzaSyBzGaXWO0XYrs96wMPHChzAvEWywFuRRMk"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", "absensi-ai-a6fe9.firebaseapp.com"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID", "absensi-ai-a6fe9"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET", "absensi-ai-a6fe9.firebasestorage.app"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", "425603956607"),
    "appId": os.getenv("FIREBASE_APP_ID", "1:425603956607:web:8797531e31e2270db6244a"),
    "measurementId": os.getenv("FIREBASE_MEASUREMENT_ID", "G-RHLT31RWQZ"),
    "databaseURL": os.getenv(
        "FIREBASE_DATABASE_URL",
        "https://absensi-ai-a6fe9-default-rtdb.asia-southeast1.firebasedatabase.app"
    )
}

LOCAL_DB_PATH = BASE_DIR / "database" / "local_db.json"
SERVICE_ACCOUNT_PATH = BASE_DIR / "serviceAccountKey.json"

firebase_admin_initialized = False
firebase_rest_active = False

# 1. Coba Inisialisasi Firebase Admin SDK jika serviceAccountKey.json ada
try:
    import firebase_admin
    from firebase_admin import credentials, db

    if SERVICE_ACCOUNT_PATH.exists():
        cred = credentials.Certificate(str(SERVICE_ACCOUNT_PATH))
        firebase_admin.initialize_app(cred, {
            'databaseURL': FIREBASE_WEB_CONFIG["databaseURL"]
        })
        firebase_admin_initialized = True
        logger.info("Firebase Admin SDK aktif menggunakan Service Account.")
except Exception as e:
    logger.warning(f"Firebase Admin SDK tidak aktif: {e}")

# 2. Cek koneksi Firebase Realtime Database via REST API
try:
    _test_url = f"{FIREBASE_WEB_CONFIG['databaseURL'].rstrip('/')}/.json"
    _resp = requests.get(_test_url, timeout=5)
    if _resp.status_code == 200:
        firebase_rest_active = True
        logger.info(f"Firebase Realtime Database REST API aktif terhubung: {FIREBASE_WEB_CONFIG['databaseURL']}")
except Exception as e:
    logger.warning(f"Firebase REST check error: {e}")


class DatabaseManager:
    """Manager sinkronisasi Firebase Realtime Database dan Local Cache."""

    def __init__(self):
        self.local_path = LOCAL_DB_PATH
        self.base_url = FIREBASE_WEB_CONFIG["databaseURL"].rstrip("/")
        self._ensure_local_db()

    def _ensure_local_db(self):
        self.local_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.local_path.exists():
            default_data = {
                "users": {},
                "siswa": {},
                "absensi": {},
                "admin": {}
            }
            with open(self.local_path, "w", encoding="utf-8") as f:
                json.dump(default_data, f, indent=4)

    def _read_local(self):
        self._ensure_local_db()
        try:
            with open(self.local_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"users": {}, "siswa": {}, "absensi": {}, "admin": {}}

    def _write_local(self, data):
        with open(self.local_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def is_firebase_active(self):
        return firebase_admin_initialized or firebase_rest_active

    def sync_all_to_firebase(self):
        """Mengunggah seluruh data local_db.json ke Firebase Realtime Database."""
        local_data = self._read_local()
        if not local_data:
            return False

        if firebase_admin_initialized:
            try:
                db.reference("/").set(local_data)
                return True
            except Exception as e:
                logger.error(f"Error sync Admin SDK: {e}")

        # Sync via REST API
        try:
            url = f"{self.base_url}/.json"
            res = requests.put(url, json=local_data, timeout=10)
            return res.status_code == 200
        except Exception as e:
            logger.error(f"Error sync REST: {e}")
            return False

    def sync_from_firebase(self):
        """Mengunduh seluruh data dari Firebase Realtime Database ke local_db.json."""
        remote_data = None
        if firebase_admin_initialized:
            try:
                remote_data = db.reference("/").get()
            except Exception as e:
                logger.error(f"Error read Admin SDK: {e}")

        if not remote_data and firebase_rest_active:
            try:
                url = f"{self.base_url}/.json"
                res = requests.get(url, timeout=10)
                if res.status_code == 200 and res.json() is not None:
                    remote_data = res.json()
            except Exception as e:
                logger.error(f"Error read REST: {e}")

        if remote_data and isinstance(remote_data, dict):
            self._write_local(remote_data)
            return True
        return False

    def get_data(self, path=""):
        """Mengambil data dari path."""
        # 1. Coba dari Firebase Admin SDK
        if firebase_admin_initialized:
            try:
                data = db.reference(path).get()
                if data is not None:
                    return data
            except Exception as e:
                logger.error(f"Error Firebase Admin get({path}): {e}")

        # 2. Coba dari Firebase REST API
        if firebase_rest_active:
            clean_path = path.strip("/")
            url = f"{self.base_url}/{clean_path}.json" if clean_path else f"{self.base_url}/.json"
            try:
                res = requests.get(url, timeout=5)
                if res.status_code == 200 and res.json() is not None:
                    return res.json()
            except Exception as e:
                logger.warning(f"Error Firebase REST get({path}): {e}")

        # 3. Fallback ke local cache
        data = self._read_local()
        if not path:
            return data
        keys = path.strip("/").split("/")
        curr = data
        for k in keys:
            if isinstance(curr, dict) and k in curr:
                curr = curr[k]
            else:
                return None
        return curr

    def set_data(self, path, value):
        """Menyimpan data di path tertentu ke Firebase dan local cache."""
        # Update local cache
        data = self._read_local()
        keys = path.strip("/").split("/")
        curr = data
        for k in keys[:-1]:
            if k not in curr or not isinstance(curr[k], dict):
                curr[k] = {}
            curr = curr[k]
        curr[keys[-1]] = value
        self._write_local(data)

        # Update Firebase Admin
        if firebase_admin_initialized:
            try:
                db.reference(path).set(value)
                return True
            except Exception as e:
                logger.error(f"Error Firebase Admin set({path}): {e}")

        # Update Firebase REST
        if firebase_rest_active:
            clean_path = path.strip("/")
            url = f"{self.base_url}/{clean_path}.json"
            try:
                res = requests.put(url, json=value, timeout=5)
                return res.status_code == 200
            except Exception as e:
                logger.error(f"Error Firebase REST set({path}): {e}")

        return True

    def update_data(self, path, value):
        """Memperbarui dict data di path tertentu."""
        data = self._read_local()
        keys = path.strip("/").split("/")
        curr = data
        for k in keys:
            if k not in curr or not isinstance(curr[k], dict):
                curr[k] = {}
            curr = curr[k]
        if isinstance(curr, dict) and isinstance(value, dict):
            curr.update(value)
        self._write_local(data)

        if firebase_admin_initialized:
            try:
                db.reference(path).update(value)
                return True
            except Exception as e:
                logger.error(f"Error Firebase Admin update({path}): {e}")

        if firebase_rest_active:
            clean_path = path.strip("/")
            url = f"{self.base_url}/{clean_path}.json"
            try:
                res = requests.patch(url, json=value, timeout=5)
                return res.status_code == 200
            except Exception as e:
                logger.error(f"Error Firebase REST update({path}): {e}")

        return True

    def push_data(self, path, value):
        """Menambahkan entri baru dengan ID unik (seperti push di Firebase)."""
        import uuid
        key = None

        if firebase_admin_initialized:
            try:
                new_ref = db.reference(path).push(value)
                key = new_ref.key
            except Exception as e:
                logger.error(f"Error Firebase Admin push({path}): {e}")

        if not key and firebase_rest_active:
            clean_path = path.strip("/")
            url = f"{self.base_url}/{clean_path}.json"
            try:
                res = requests.post(url, json=value, timeout=5)
                if res.status_code == 200:
                    key = res.json().get("name")
            except Exception as e:
                logger.error(f"Error Firebase REST push({path}): {e}")

        if not key:
            key = f"-{uuid.uuid4().hex[:19]}"

        full_path = f"{path.strip('/')}/{key}"
        self.set_data(full_path, value)
        return key

    def delete_data(self, path):
        """Menghapus entri pada path tertentu."""
        data = self._read_local()
        keys = path.strip("/").split("/")
        curr = data
        for k in keys[:-1]:
            if k in curr and isinstance(curr[k], dict):
                curr = curr[k]
            else:
                return False
        if keys[-1] in curr:
            del curr[keys[-1]]
            self._write_local(data)

        if firebase_admin_initialized:
            try:
                db.reference(path).delete()
            except Exception as e:
                logger.error(f"Error Firebase Admin delete({path}): {e}")

        if firebase_rest_active:
            clean_path = path.strip("/")
            url = f"{self.base_url}/{clean_path}.json"
            try:
                requests.delete(url, timeout=5)
            except Exception as e:
                logger.error(f"Error Firebase REST delete({path}): {e}")

        return True


# Singleton instance
db_manager = DatabaseManager()
