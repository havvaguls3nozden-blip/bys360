(function () {
  function readPayload() {
    const node = document.getElementById('analysisCenterData');
    if (!node) return {};
    try { return JSON.parse(node.textContent || '{}'); } catch (err) { return {}; }
  }

  function baseOptions() {
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { boxWidth: 12, usePointStyle: true } },
        tooltip: { intersect: false, mode: 'index' }
      },
      scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
    };
  }

  function renderCharts(payload) {
    if (!window.Chart) return;
    const distCanvas = document.getElementById('scoreDistributionChart');
    if (distCanvas && Array.isArray(payload.score_distribution)) {
      new Chart(distCanvas, {
        type: 'bar',
        data: {
          labels: payload.score_distribution.map(item => item.label),
          datasets: [{ label: 'Kayıt', data: payload.score_distribution.map(item => item.value), borderWidth: 1, borderRadius: 12 }]
        },
        options: Object.assign(baseOptions(), { plugins: { legend: { display: false } } })
      });
    }

    const trendCanvas = document.getElementById('periodTrendChart');
    if (trendCanvas && Array.isArray(payload.period_trend) && payload.period_trend.length) {
      new Chart(trendCanvas, {
        type: 'line',
        data: {
          labels: payload.period_trend.map(item => item.label),
          datasets: [
            { label: 'Ortalama puan', data: payload.period_trend.map(item => item.avg_score), tension: 0.35, borderWidth: 2 },
            { label: 'Tamamlanma %', data: payload.period_trend.map(item => item.completion), tension: 0.35, borderWidth: 2 }
          ]
        },
        options: baseOptions()
      });
    }
  }

  function esc(value) {
    return String(value == null ? '' : value).replace(/[&<>'"]/g, function (ch) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' })[ch];
    });
  }

  function renderDecisionPack(pack) {
    const target = document.getElementById('decisionPack');
    if (!target) return;
    if (!pack || !pack.ok) {
      target.innerHTML = '<div class="acu-empty compact">Karar destek paketi şu anda üretilemedi.</div>';
      return;
    }
    const actions = (pack.recommended_actions || []).map(function (item) {
      return '<div class="acu-action-row">' +
        '<span class="acu-priority">' + esc(item.priority) + '</span>' +
        '<div><b>' + esc(item.title) + '</b>' +
        '<small>Sorumlu: ' + esc(item.owner) + ' · Kontrol: ' + esc(item.control) + '</small></div>' +
        '</div>';
    }).join('');
    target.innerHTML = '<div class="acu-readiness">' +
      '<strong>' + esc(pack.readiness_score) + '</strong>' +
      '<span><b>' + esc(pack.title) + '</b><br>' + esc(pack.executive_summary) + '</span>' +
      '</div>' +
      '<div class="acu-action-list">' + actions + '</div>';
  }

  function loadDecisionPack(payload) {
    const btn = document.querySelector('[data-load-decision-pack-url]');
    const url = btn ? btn.getAttribute('data-load-decision-pack-url') : payload.decision_pack_url;
    if (!url) return;
    fetch(url, { headers: { 'Accept': 'application/json' }, credentials: 'same-origin' })
      .then(resp => resp.json())
      .then(renderDecisionPack)
      .catch(function () { renderDecisionPack(null); });
    if (btn) {
      btn.addEventListener('click', function () {
        target = document.getElementById('decisionPack');
        if (target) target.innerHTML = '<div class="acu-empty compact">Karar destek paketi yenileniyor.</div>';
        loadDecisionPack(payload);
      }, { once: true });
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    const payload = readPayload();
    renderCharts(payload);
    loadDecisionPack(payload);
  });
})();
