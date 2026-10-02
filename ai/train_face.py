"""
Script Training Wajah Siswa
Membaca foto wajah siswa yang tersimpan dan memperbarui face embedding di database.
Dapat dijalankan langsung dari terminal:
    python ai/train_face.py
"""

import sys
import os
from pathlib import Path

# Tambahkan root path ke sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from firebase_config import db_manager
from ai.face_recognition_engine import encode_face


def train_all_faces(force=False):
    """
    Melakukan ekstraksi encoding untuk semua siswa yang memiliki foto wajah.
    Jika force=True, perbarui encoding meskipun sudah ada.
    """
    print("=" * 60)
    print("Memulai proses training wajah siswa...")
    print("=" * 60)

    siswa_dict = db_manager.get_data("siswa") or {}
    total = len(siswa_dict)
    success_count = 0
    skipped_count = 0
    fail_count = 0

    if not siswa_dict:
        print("Tidak ada data siswa ditemukan di database.")
        return {"total": 0, "success": 0, "failed": 0, "skipped": 0}

    for id_siswa, siswa in siswa_dict.items():
        nama = siswa.get("nama", "Tanpa Nama")
        foto_path = siswa.get("foto_wajah", "")
        existing_encoding = siswa.get("face_encoding")

        if existing_encoding and not force:
            print(f"[SKIP] Siswa '{nama}' ({id_siswa}) sudah memiliki encoding wajah.")
            skipped_count += 1
            continue

        if not foto_path:
            print(f"[FAIL] Siswa '{nama}' ({id_siswa}) belum memiliki foto wajah.")
            fail_count += 1
            continue

        # Handle relative path
        if foto_path.startswith("/"):
            real_image_path = BASE_DIR / foto_path.lstrip("/")
        else:
            real_image_path = BASE_DIR / foto_path

        if not real_image_path.exists():
            print(f"[FAIL] Berkas foto tidak ditemukan: {real_image_path}")
            fail_count += 1
            continue

        try:
            encoding, box = encode_face(str(real_image_path))
            if encoding:
                db_manager.update_data(f"siswa/{id_siswa}", {
                    "face_encoding": encoding
                })
                print(f"[SUCCESS] Berhasil mengekstrak embedding untuk '{nama}' ({id_siswa}).")
                success_count += 1
            else:
                print(f"[FAIL] Tidak ada wajah terdeteksi pada foto '{nama}'.")
                fail_count += 1
        except Exception as e:
            print(f"[ERROR] Error memproses '{nama}': {e}")
            fail_count += 1

    summary = {
        "total": total,
        "success": success_count,
        "failed": fail_count,
        "skipped": skipped_count
    }

    print("-" * 60)
    print(f"Selesai! Total: {total} | Sukses: {success_count} | Dilewati: {skipped_count} | Gagal: {fail_count}")
    print("=" * 60)
    return summary


if __name__ == "__main__":
    force_run = "--force" in sys.argv
    train_all_faces(force=force_run)
