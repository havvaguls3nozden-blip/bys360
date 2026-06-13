(function () {
  if (typeof Chart === 'undefined') return;
  var payload = window.bys360PerformanceReportsData || {};
  var labels = Array.isArray(payload.labels) ? payload.labels : [];
  var avgScores = Array.isArray(payload.avg_scores) ? payload.avg_scores : [];
  var completionRates = Array.isArray(payload.completion_rates) ? payload.completion_rates : [];
  var statusDistribution = Array.isArray(payload.status_distribution) ? payload.status_distribution : [];

  var trendCanvas = document.getElementById('bysReportsTrendChart');
  if (trendCanvas) {
    new Chart(trendCanvas, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          { label: 'Ortalama Puan', data: avgScores, borderColor: '#8B0000', backgroundColor: 'rgba(139,0,0,0.08)', tension: 0.35, fill: false, borderWidth: 2.4, pointRadius: 3 },
          { label: 'Tamamlanma %', data: completionRates, borderColor: '#64748b', backgroundColor: 'rgba(100,116,139,0.08)', tension: 0.35, fill: false, borderWidth: 2.0, pointRadius: 3 }
        ]
      },
      options: { responsive: true, maintainAspectRatio: false, interaction: { mode: 'index', intersect: false }, plugins: { legend: { position: 'bottom' } }, scales: { y: { beginAtZero: true, suggestedMax: 100, grid: { color: 'rgba(0,0,0,0.05)' } }, x: { grid: { display: false } } } }
    });
  }

  var statusCanvas = document.getElementById('bysReportsStatusChart');
  if (statusCanvas) {
    new Chart(statusCanvas, {
      type: 'doughnut',
      data: {
        labels: ['Tamamlanan', 'Kısmi', 'Bekleyen'],
        datasets: [{ data: [statusDistribution[0] || 0, statusDistribution[1] || 0, statusDistribution[2] || 0], backgroundColor: ['#8B0000', '#d4a52d', '#8c97a8'], borderWidth: 0 }]
      },
      options: { responsive: true, maintainAspectRatio: false, cutout: '68%', plugins: { legend: { position: 'bottom' } } }
    });
  }
})();
