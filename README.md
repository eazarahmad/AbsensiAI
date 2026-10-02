# 🎓 Absensi-AI: Sistem Presensi Siswa Cerdas Berbasis Face Recognition & Firebase

Aplikasi web presensi siswa modern berbasis kecerdasan buatan (Artificial Intelligence) dengan fitur **Face Recognition (Pengenalan Wajah)** secara *realtime* melalui kamera peramban (browser) yang terintegrasi dengan **Firebase Realtime Database** dan backend **Python Flask**.

---

## 🚀 Fitur Utama

### 1. 🤖 Presensi Wajah AI (*Realtime Face Recognition*)
* **Deteksi & Encoding Otomatis**: Membaca frame wajah langsung dari kamera peramban menggunakan kombinasi OpenCV Haar Cascade dan model Face Recognition embedding (128-dimensi).
* **Pencocokan Cerdas & Skor Keyakinan (*Confidence Score*)**: Menampilkan persentase akurasi pencocokan wajah secara langsung.
* **Pencegahan Absensi Ganda (*Anti-Duplicate Check*)**: Mencegah siswa melakukan absensi lebih dari satu kali pada tanggal yang sama.
* **Umpan Balik Visual & Audio**: Indikator status kamera berkedip, animasi pemindaian, audio nada lonceng (*chime*), dan peringatan status responsif.

### 2. 👨‍💼 Panel Administrator
* **Dashboard Statistik Modern**: Menampilkan total siswa, jumlah kehadiran hari ini, persentase kehadiran, dan grafik tren kehadiran 7 hari terakhir (Chart.js).
* **Manajemen Data Siswa (CRUD)**: Menambah siswa baru, mengubah data, menghapus data siswa, serta mengunggah foto wajah untuk proses kalibrasi AI.
* **Fitur Training AI Sekali Klik**: Tombol *Retrain Model AI* di dashboard untuk memperbarui embedding seluruh foto wajah siswa sekaligus.
* **Laporan Absensi & Filter Lengkap**: Filter pencarian berdasarkan nama, kelas, tanggal, dan status kehadiran.
* **Ekspor Laporan Multiformat**: Unduh rekapan absensi ke format **Excel (.xlsx)** dan **PDF**.

### 3. 👨‍🎓 Portal Siswa
* **Profil Biometrik & Kehadiran**: Status foto wajah AI dan status kehadiran hari ini.
* **Statistik & Riwayat Presensi Pribadi**: Meninjau tanggal, jam kedatangan, dan tingkat akurasi pencocokan AI.
* **Akses Cepat Kamera Absensi**: Akses langsung ke modul kamera pemindaian wajah.

---

## 📂 Struktur Direktori Proyek

```text
AbsensiAI/
├── app.py                      # Aplikasi utama Flask (Routing, API, Auth, Export)
├── firebase_config.py          # Modul koneksi Firebase Realtime Database & Sinkronisasi
├── requirements.txt            # Daftar pustaka & dependensi Python
├── .env                        # Konfigurasi environment & Firebase Web
├── prd.txt                     # Dokumen PRD acuan spesifikasi
├── README.md                   # Dokumentasi instalasi, panduan penggunaan, & deployment
│
├── ai/
│   ├── face_recognition_engine.py  # Engine pengenal wajah, ekstraksi encoding & matching
│   └── train_face.py               # Skrip batch training foto wajah siswa (CLI)
│
├── database/
│   └── local_db.json           # Database lokal realtime (sinkron otomatis jika offline/fallback)
│
├── static/
│   ├── css/
│   │   └── style.css           # Desain antarmuka modern (Biru Profesional, Abu & Putih)
│   ├── js/
│   │   ├── camera.js           # Kontroler kamera browser, stream snapshot & audio chime
│   │   ├── main.js             # Skrip interaksi UI, toast alert, dan trigger training
│   │   └── report.js           # Filter dinamis tabel laporan absensi
│   └── images/                 # Aset grafis aplikasi
│
├── templates/
│   ├── base.html               # Template induk Bootstrap 5, sidebar, & topbar
│   ├── login.html              # Halaman login otentikasi role Admin & Siswa
│   ├── dashboard_admin.html    # Dashboard metrik & grafik kehadiran admin
│   ├── dashboard_siswa.html    # Dashboard profil siswa & riwayat presensi
│   ├── data_siswa.html         # Manajemen CRUD data siswa & upload foto wajah
│   ├── absensi.html            # Halaman kamera absensi AI
│   └── laporan.html            # Laporan rekap absensi dengan tombol ekspor Excel/PDF
│
└── uploads/
    └── faces/                  # Direktori penyimpanan foto wajah siswa terdaftar
```

---

## 🛠️ Persyaratan Sistem (*Prerequisites*)

1. **Python 3.10 atau 3.11** (Sangat disarankan untuk stabilitas paket machine learning pada Windows/Linux).
2. Peramban web modern (*Google Chrome*, *Microsoft Edge*, atau *Mozilla Firefox*) dengan izin akses webcam aktif.
3. Koneksi internet (untuk mengunduh CDN aset Bootstrap, Chart.js, dan sinkronisasi Firebase).

---

## ⚙️ Panduan Instalasi Langkah-demi-Langkah

### 1. Masuk ke Direktori Proyek
Buka terminal (PowerShell atau Command Prompt) di folder proyek:
```powershell
cd C:\Users\user\Documents\AbsensiAI
```

### 2. (Opsional) Membuat Lingkungan Virtual (*Virtual Environment*)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Memasang Dependensi Pustaka
Jalankan perintah instalasi menggunakan file `requirements.txt`:
```powershell
pip install -r requirements.txt
```

> **Catatan Windows untuk `dlib` & `face_recognition`:**
> Sistem telah dilengkapi dengan modul dual-engine cerdas (`face_recognition` & OpenCV AI Feature Engine). Jika instalasi `dlib` dari source membutuhkan C++ Build Tools pada Windows, Anda dapat menginstal roda pre-compiled berikut dengan mudah:
> ```powershell
> pip install dlib-bin
> pip install face_recognition --no-deps
> ```

---

## 🔑 Konfigurasi Firebase Realtime Database

Proyek ini telah dikonfigurasi dengan Project ID: `absensi-ai-a6fe9`.

### Cara Mengaktifkan Firebase Admin SDK (Produksi):
1. Buka [Firebase Console](https://console.firebase.google.com/).
2. Pilih proyek **Absensi-AI** (`absensi-ai-a6fe9`).
3. Buka **Project Settings** > tab **Service accounts**.
4. Klik **Generate new private key** (akan terunduh file `.json`).
5. Ubah nama file tersebut menjadi `serviceAccountKey.json` dan letakkan di folder utama `AbsensiAI/`.
6. Aplikasi akan otomatis mendeteksi file kunci dan langsung tersinkronisasi ke Firebase Cloud!
7. *Catatan:* Jika file kunci belum ditaruh, aplikasi secara otomatis menggunakan `database/local_db.json` dengan struktur skema Firebase yang identik, sehingga aplikasi dapat langsung diuji coba tanpa hambatan.

---

## ▶️ Cara Menjalankan Aplikasi

Jalankan perintah berikut di terminal:
```powershell
python app.py
```

Aplikasi web akan berjalan pada alamat:
👉 **`http://localhost:5000`** atau **`http://127.0.0.1:5000`**

### 👤 Akun Default untuk Masuk (*Login*):
* **Administrator:**
  * Email / Username: `admin@absensi.ai`
  * Password: `admin123`
* **Siswa Demo:**
  * NIS: `10201` atau Email: `fauzi@siswa.ai`
  * Password: `siswa123`

---

## 🧠 Cara Melatih Wajah Siswa (*Training AI*)

### Metode 1: Melalui Dashboard Web Admin (Rekomendasi)
1. Masuk sebagai **Admin**.
2. Masuk ke menu **Data Siswa**.
3. Klik tombol **Tambah Siswa Baru** dan unggah foto wajah siswa (format JPG/PNG dengan wajah menghadap depan).
4. Klik **Simpan & Training AI**. Sistem akan otomatis mengekstrak face embedding dan menyimpannya.
5. Anda juga dapat menekan tombol **Retrain Model AI** di halaman utama dashboard untuk melatih ulang seluruh data wajah sekaligus.

### Metode 2: Melalui Terminal (CLI)
Jalankan skrip training berikut:
```powershell
python ai/train_face.py --force
```

---

## 🌐 Panduan Deployment

### 1. Deployment ke VPS (Ubuntu / Debian dengan Gunicorn & Nginx)
1. Salin kode ke server VPS:
   ```bash
   git clone <repo_url> /var/www/absensi-ai
   cd /var/www/absensi-ai
   ```
2. Buat virtual environment dan instal paket:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt gunicorn
   ```
3. Buat service systemd (`/etc/systemd/system/absensi.service`):
   ```ini
   [Unit]
   Description=Gunicorn instance to serve Absensi-AI
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/var/www/absensi-ai
   Environment="PATH=/var/www/absensi-ai/venv/bin"
   ExecStart=/var/www/absensi-ai/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 app:app

   [Install]
   WantedBy=multi-user.target
   ```
4. Aktifkan SSL HTTPS pada Nginx menggunakan Let's Encrypt (karena browser mewajibkan HTTPS untuk mengakses Webcam).

### 2. Deployment ke Google Cloud Run
1. Buat `Dockerfile`:
   ```dockerfile
   FROM python:3.11-slim
   RUN apt-get update && apt-get install -y libgl1-mesa-glx libglib2.0-0 cmake build-essential && rm -rf /var/lib/apt/lists/*
   WORKDIR /app
   COPY . /app
   RUN pip install --no-cache-dir -r requirements.txt gunicorn
   EXPOSE 8080
   CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "app:app"]
   ```
2. Deploy container ke Google Cloud Run:
   ```bash
   gcloud run deploy absensi-ai --source . --platform managed --allow-unauthenticated
   ```

---

## 🛡️ Skema Database Firebase Realtime

```json
{
  "users": {
    "user_id": {
      "nama": "String",
      "email": "String",
      "password": "Hashed_Password_String",
      "role": "admin | siswa",
      "nis": "String (optional)"
    }
  },
  "siswa": {
    "id_siswa": {
      "nama": "String",
      "nis": "String",
      "kelas": "String",
      "alamat": "String",
      "foto_wajah": "/uploads/faces/face_id.jpg",
      "face_encoding": [0.123, -0.456, 0.789, "... 128 float values"]
    }
  },
  "absensi": {
    "id_absensi": {
      "id_siswa": "String",
      "nama": "String",
      "kelas": "String",
      "tanggal": "YYYY-MM-DD",
      "waktu": "HH:MM:SS",
      "status": "Hadir",
      "confidence": 98.5
    }
  },
  "admin": {
    "admin_id": {
      "nama": "String",
      "email": "String",
      "role": "admin"
    }
  }
}
```

---

## 📜 Lisensi & Pengembang
Dikembangkan untuk sistem manajemen absensi sekolah cerdas berbasis kecerdasan buatan. Bebas dikustomisasi dan dikembangkan lebih lanjut.
