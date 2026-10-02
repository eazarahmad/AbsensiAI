/**
 * report.js - Laporan Absensi Filtering and Instant Search
 */

document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.getElementById("search-input");
  const reportTable = document.getElementById("report-table");

  if (searchInput && reportTable) {
    searchInput.addEventListener("input", function() {
      const keyword = this.value.toLowerCase();
      const rows = reportTable.querySelectorAll("tbody tr");

      rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        if (text.includes(keyword)) {
          row.style.display = "";
        } else {
          row.style.display = "none";
        }
      });
    });
  }

  // Reset filter form button
  const btnReset = document.getElementById("btn-reset-filter");
  if (btnReset) {
    btnReset.addEventListener("click", () => {
      window.location.href = window.location.pathname;
    });
  }
});
