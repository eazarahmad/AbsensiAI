/**
 * main.js - Core UI and interaction scripts for Absensi-AI
 */

document.addEventListener("DOMContentLoaded", () => {
  // Mobile sidebar toggle
  const sidebarToggle = document.getElementById("sidebar-toggle");
  const sidebar = document.querySelector(".sidebar");
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener("click", () => {
      sidebar.classList.toggle("show");
    });
  }

  // Auto dismiss flash alerts after 5 seconds
  const alerts = document.querySelectorAll(".alert-dismissible");
  alerts.forEach(alert => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 5000);
  });

  // Retrain AI button handler
  const btnTrainAI = document.getElementById("btn-train-ai");
  if (btnTrainAI) {
    btnTrainAI.addEventListener("click", async () => {
      if (!confirm("Mulai proses training ulang model AI untuk semua wajah siswa?")) {
        return;
      }

      const originalHtml = btnTrainAI.innerHTML;
      btnTrainAI.disabled = true;
      btnTrainAI.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status"></span> Training AI...`;

      try {
        const res = await fetch("/admin/train-ai", {
          method: "POST",
          headers: { "Content-Type": "application/json" }
        });
        const data = await res.json();
        if (data.success) {
          alert(`Training Selesai!\nTotal: ${data.result.total}\nBerhasil: ${data.result.success}\nDilewati: ${data.result.skipped}\nGagal: ${data.result.failed}`);
          location.reload();
        } else {
          alert("Gagal melakukan training AI: " + (data.message || "Error tidak diketahui"));
        }
      } catch (err) {
        alert("Terjadi kesalahan jaringan saat training AI: " + err.message);
      } finally {
        btnTrainAI.disabled = false;
        btnTrainAI.innerHTML = originalHtml;
      }
    });
  }
});
