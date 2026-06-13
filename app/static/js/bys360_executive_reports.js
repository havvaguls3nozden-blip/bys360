(function () {
  function ready(fn) {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fn);
    else fn();
  }
  function byId(id) { return document.getElementById(id); }
  function safeData(id) {
    var el = byId(id);
    if (!el) return null;
    try { return JSON.parse(el.textContent || '{}'); } catch (err) { return null; }
  }
  function chartAvailable() { return typeof window.Chart !== 'undefined'; }
  function makeLineChart(canvasId, payload) {
    var el = byId(canvasId);
    if (!el || !chartAvailable() || !payload) return;
    var labels = payload.labels || [];
    if (!labels.length) return;
    new window.Chart(el, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          { label: 'Ortalama puan', data: payload.avg_scores || [], tension: .35, borderWidth: 3, fill: false },
          { label: 'Tamamlanma %', data: payload.completion_rates || [], tension: .35, borderWidth: 3, fill: false }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom' } },
        scales: { y: { beginAtZero: true, suggestedMax: 100 } }
      }
    });
  }
  function makeDoughnutChart(canvasId, payload) {
    var el = byId(canvasId);
    if (!el || !chartAvailable() || !payload) return;
    var data = payload.status_distribution || [];
    if (!data.some(function (x) { return Number(x) > 0; })) return;
    new window.Chart(el, {
      type: 'doughnut',
      data: { labels: ['Tamamlandı', 'Kısmi', 'Bekliyor'], datasets: [{ data: data, borderWidth: 2 }] },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } }, cutout: '62%' }
    });
  }
  function makeDashboardChart(canvasId, payload) {
    var el = byId(canvasId);
    if (!el || !chartAvailable() || !payload) return;
    new window.Chart(el, {
      type: 'bar',
      data: {
        labels: ['Toplam', 'Tamamlanan', 'Bekleyen', 'Geciken'],
        datasets: [{ label: 'Görev akışı', data: [payload.total || 0, payload.completed || 0, payload.pending || 0, payload.overdue || 0], borderWidth: 1 }]
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
    });
  }
  function makeScoreBands(canvasId, payload) {
    var el = byId(canvasId);
    if (!el || !chartAvailable() || !payload) return;
    var data = [payload.low || 0, payload.normal || 0, payload.high || 0];
    if (!data.some(function (x) { return Number(x) > 0; })) return;
    new window.Chart(el, {
      type: 'bar',
      data: { labels: ['70 altı', '70–90', '90 üstü'], datasets: [{ label: 'Puan bantları', data: data, borderWidth: 1 }] },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
    });
  }
  ready(function () {
    makeDashboardChart('execDashboardFlowChart', safeData('exec-dashboard-flow-data'));
    makeLineChart('execReportsTrendChart', safeData('exec-reports-chart-data'));
    makeDoughnutChart('execReportsStatusChart', safeData('exec-reports-chart-data'));
    makeScoreBands('execScoreBandsChart', safeData('exec-score-bands-data'));
  });
}());
