/**
 * camera.js - Absensi AI Face Recognition Controller
 * Mengelola stream kamera browser, pengiriman frame ke backend AI, dan feedback visual.
 */

let videoElement = null;
let overlayCanvas = null;
let scanLine = null;
let stream = null;
let isScanning = false;
let scanInterval = null;
let lastRecognizedTime = 0;

// Web Audio API Audio Chime (Synthetic chime tanpa file eksternal)
function playAttendanceTone(type = 'success') {
  try {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return;
    const ctx = new AudioContext();
    
    if (type === 'success') {
      // Dua nada naik (ding-dong)
      const osc1 = ctx.createOscillator();
      const osc2 = ctx.createOscillator();
      const gain = ctx.createGain();

      osc1.type = 'sine';
      osc1.frequency.setValueAtTime(587.33, ctx.currentTime); // D5
      osc1.frequency.setValueAtTime(880.00, ctx.currentTime + 0.15); // A5

      gain.gain.setValueAtTime(0.2, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.6);

      osc1.connect(gain);
      gain.connect(ctx.destination);
      osc1.start();
      osc1.stop(ctx.currentTime + 0.6);
    } else if (type === 'warning') {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(440, ctx.currentTime);
      osc.frequency.setValueAtTime(349, ctx.currentTime + 0.12);
      gain.gain.setValueAtTime(0.2, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.4);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.4);
    }
  } catch (e) {
    console.warn("Audio Context tidak didukung atau diblokir browser:", e);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  videoElement = document.getElementById("camera-stream");
  overlayCanvas = document.getElementById("overlay-canvas");
  scanLine = document.getElementById("scan-line");

  const startBtn = document.getElementById("btn-start-camera");
  const stopBtn = document.getElementById("btn-stop-camera");
  const manualScanBtn = document.getElementById("btn-scan-face");

  if (startBtn) {
    startBtn.addEventListener("click", startCamera);
  }
  if (stopBtn) {
    stopBtn.addEventListener("click", stopCamera);
  }
  if (manualScanBtn) {
    manualScanBtn.addEventListener("click", () => scanFrame(true));
  }

  // Otomatis nyalakan kamera saat masuk ke halaman absensi
  if (videoElement) {
    startCamera();
  }
});

async function startCamera() {
  const cameraStatusBadge = document.getElementById("camera-status");
  const statusCard = document.getElementById("status-result-card");

  try {
    const constraints = {
      video: {
        width: { ideal: 1280 },
        height: { ideal: 720 },
        facingMode: "user"
      },
      audio: false
    };

    stream = await navigator.mediaDevices.getUserMedia(constraints);
    videoElement.srcObject = stream;
    await videoElement.play();

    if (cameraStatusBadge) {
      cameraStatusBadge.innerHTML = '<span class="pulse-dot"></span> Kamera Aktif';
      cameraStatusBadge.classList.remove("d-none");
    }

    if (scanLine) {
      scanLine.classList.add("active");
    }

    // Ubah status tombol
    document.getElementById("btn-start-camera")?.classList.add("d-none");
    document.getElementById("btn-stop-camera")?.classList.remove("d-none");

    isScanning = true;
    startScanningLoop();
  } catch (err) {
    console.error("Gagal membuka kamera:", err);
    if (statusCard) {
      statusCard.className = "card border-danger shadow-sm mt-3";
      statusCard.innerHTML = `
        <div class="card-body text-danger text-center">
          <i class="bi bi-camera-video-off fs-1"></i>
          <h5 class="mt-2">Kamera Tidak Dapat Diakses</h5>
          <p class="mb-0 text-muted small">${err.message || 'Pastikan izin kamera telah diberikan di browser Anda.'}</p>
        </div>
      `;
    }
  }
}

function stopCamera() {
  if (stream) {
    stream.getTracks().forEach(track => track.stop());
    stream = null;
  }
  if (videoElement) {
    videoElement.srcObject = null;
  }
  isScanning = false;
  if (scanInterval) {
    clearInterval(scanInterval);
    scanInterval = null;
  }

  const cameraStatusBadge = document.getElementById("camera-status");
  if (cameraStatusBadge) {
    cameraStatusBadge.classList.add("d-none");
  }
  if (scanLine) {
    scanLine.classList.remove("active");
  }

  document.getElementById("btn-start-camera")?.classList.remove("d-none");
  document.getElementById("btn-stop-camera")?.classList.add("d-none");
}

function startScanningLoop() {
  if (scanInterval) clearInterval(scanInterval);
  // Scan frame setiap 1.5 detik
  scanInterval = setInterval(() => {
    // Jangan scan jika baru saja berhasil absen (tunggu 4 detik jeda)
    if (Date.now() - lastRecognizedTime > 4000) {
      scanFrame(false);
    }
  }, 1500);
}

async function scanFrame(isManual = false) {
  if (!videoElement || !stream || videoElement.videoWidth === 0) return;

  const statusCard = document.getElementById("status-result-card");
  const loadingIndicator = document.getElementById("recognition-loading");

  if (loadingIndicator && isManual) {
    loadingIndicator.classList.remove("d-none");
  }

  // Buat canvas snapshot
  const canvas = document.createElement("canvas");
  canvas.width = videoElement.videoWidth;
  canvas.height = videoElement.videoHeight;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);

  const base64Image = canvas.toDataURL("image/jpeg", 0.85);

  try {
    const res = await fetch("/api/recognize_face", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ image: base64Image })
    });

    const data = await res.json();
    if (loadingIndicator) loadingIndicator.classList.add("d-none");

    handleRecognitionResult(data);
  } catch (error) {
    console.error("Error recognizing face:", error);
    if (loadingIndicator) loadingIndicator.classList.add("d-none");
  }
}

function handleRecognitionResult(res) {
  const statusCard = document.getElementById("status-result-card");
  if (!statusCard) return;

  if (!res.success) {
    // Tidak ada wajah atau error
    statusCard.className = "card border-secondary bg-light shadow-sm mt-3";
    statusCard.innerHTML = `
      <div class="card-body text-center py-3">
        <i class="bi bi-person-bounding-box fs-2 text-muted"></i>
        <h6 class="mt-2 mb-0 text-muted">${res.message || 'Mencari wajah di kamera...'}</h6>
      </div>
    `;
    return;
  }

  if (res.match) {
    lastRecognizedTime = Date.now();
    const conf = res.data?.confidence || res.confidence || 95;

    if (res.already_recorded) {
      playAttendanceTone('warning');
      statusCard.className = "card border-warning shadow-sm mt-3";
      statusCard.innerHTML = `
        <div class="card-body text-center py-3">
          <i class="bi bi-info-circle-fill text-warning fs-1"></i>
          <h5 class="mt-2 text-warning fw-bold">Sudah Hadir Hari Ini</h5>
          <h4 class="fw-bold mb-1 text-dark">${res.nama}</h4>
          <p class="text-muted mb-2">Kelas: <strong>${res.kelas}</strong> | Jam Masuk: <strong>${res.waktu}</strong></p>
          <div class="badge bg-warning text-dark px-3 py-2 rounded-pill">
            <i class="bi bi-shield-check me-1"></i> Confidence: ${conf}%
          </div>
        </div>
      `;
    } else {
      playAttendanceTone('success');
      statusCard.className = "card border-success shadow-sm mt-3 animate__animated animate__fadeIn";
      statusCard.innerHTML = `
        <div class="card-body text-center py-3">
          <i class="bi bi-check-circle-fill text-success fs-1"></i>
          <h5 class="mt-2 text-success fw-bold">Absensi Berhasil Dicatat!</h5>
          <h4 class="fw-bold mb-1 text-dark">${res.data.nama_siswa}</h4>
          <p class="text-muted mb-2">Kelas: <strong>${res.data.kelas}</strong> | Waktu: <strong>${res.data.waktu}</strong></p>
          <div class="badge bg-success px-3 py-2 rounded-pill">
            <i class="bi bi-cpu me-1"></i> AI Confidence: ${conf}%
          </div>
        </div>
      `;

      // Jika ada tabel riwayat di halaman yang sama, reload data secara halus
      const historyTable = document.getElementById("personal-history-tbody");
      if (historyTable) {
        const newRow = `
          <tr class="table-success">
            <td>${res.data.tanggal}</td>
            <td>${res.data.waktu}</td>
            <td><span class="badge bg-success">Hadir</span></td>
            <td>${conf}%</td>
          </tr>
        `;
        historyTable.insertAdjacentHTML('afterbegin', newRow);
      }
    }
  } else {
    // Wajah tidak terdaftar
    statusCard.className = "card border-danger shadow-sm mt-3";
    statusCard.innerHTML = `
      <div class="card-body text-center py-3">
        <i class="bi bi-exclamation-triangle-fill text-danger fs-1"></i>
        <h5 class="mt-2 text-danger fw-bold">Wajah Tidak Terdaftar</h5>
        <p class="text-muted mb-2">Wajah Anda belum terdaftar dalam sistem absensi sekolah.</p>
        <span class="badge bg-light text-secondary border">Confidence: ${res.confidence || 0}%</span>
      </div>
    `;
  }
}
