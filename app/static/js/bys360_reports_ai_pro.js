(function(){
  function ready(fn){
    if(document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }
  function clamp(v){ v = Number(v || 0); return Math.max(0, Math.min(100, v)); }
  function initProgress(){
    document.querySelectorAll('[data-bys-progress]').forEach(function(el){
      var value = clamp(el.getAttribute('data-bys-progress'));
      requestAnimationFrame(function(){ el.style.width = value + '%'; });
    });
  }
  function countUp(){
    document.querySelectorAll('[data-bys-count]').forEach(function(el){
      var target = Number(String(el.textContent || '0').replace(',', '.')) || 0;
      var isFloat = Math.abs(target - Math.round(target)) > 0.001;
      var start = performance.now();
      function tick(now){
        var p = Math.min((now - start) / 650, 1);
        var eased = 1 - Math.pow(1 - p, 3);
        var val = target * eased;
        el.textContent = isFloat ? val.toFixed(1) : String(Math.round(val));
        if(p < 1) requestAnimationFrame(tick);
        else el.textContent = isFloat ? target.toFixed(1) : String(Math.round(target));
      }
      requestAnimationFrame(tick);
    });
  }
  function loadHeavyPanels(){
    var holder = document.querySelector('[data-bys-heavy-panels]');
    if(!holder) return;
    var url = holder.getAttribute('data-bys-heavy-panels');
    if(!url) return;
    fetch(url, {credentials:'same-origin', headers:{'X-Requested-With':'fetch'}})
      .then(function(r){ if(!r.ok) throw new Error('HTTP '+r.status); return r.text(); })
      .then(function(html){ holder.innerHTML = html; initProgress(); countUp(); initCharts(); })
      .catch(function(){
        holder.setAttribute('data-bys-heavy-panels-status', 'fallback');
        if(!holder.querySelector('[data-bys-heavy-panels-inline="1"]') && !holder.querySelector('[data-bys-heavy-panels-error="1"]')){
          holder.insertAdjacentHTML('beforeend', '<div data-bys-heavy-panels-error="1" class="bys-pro-card bys-pro-card-pad"><div class="bys-pro-empty">Ağır dashboard panelleri şu anda yüklenemedi. Ana göstergeler çalışmaya devam ediyor.</div></div>');
        }
      });
  }
  function chartDefaults(){
    if(!window.Chart) return;
    Chart.defaults.font.family = "Inter, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
    Chart.defaults.color = '#64748b';
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(17,24,39,.94)';
    Chart.defaults.plugins.tooltip.padding = 12;
    Chart.defaults.plugins.tooltip.cornerRadius = 12;
  }
  function initCharts(){
    if(!window.Chart) return;
    chartDefaults();
    document.querySelectorAll('canvas[data-bys-chart]').forEach(function(canvas){
      if(canvas.dataset.chartReady === '1') return;
      var type = canvas.getAttribute('data-bys-chart') || 'line';
      var labels = [];
      var datasets = [];
      try { labels = JSON.parse(canvas.getAttribute('data-labels') || '[]'); } catch(e) {}
      try { datasets = JSON.parse(canvas.getAttribute('data-datasets') || '[]'); } catch(e) {}
      if(!labels.length && !datasets.length) return;
      var prepared = datasets.map(function(ds, i){
        var base = i === 0 ? '#8B0000' : (i === 1 ? '#111827' : '#64748b');
        return Object.assign({
          borderColor: ds.borderColor || base,
          backgroundColor: ds.backgroundColor || (type === 'line' ? 'rgba(139,0,0,.10)' : base),
          borderWidth: 2,
          tension: .35,
          fill: type === 'line' ? true : false,
          borderRadius: type === 'bar' ? 10 : 0,
          pointRadius: type === 'line' ? 3 : 0,
          pointHoverRadius: 5
        }, ds);
      });
      new Chart(canvas, {
        type: type,
        data: { labels: labels, datasets: prepared },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { position: 'bottom' } },
          scales: type === 'doughnut' ? {} : {
            x: { grid: { display: false } },
            y: { beginAtZero: true, grid: { color: 'rgba(15,23,42,.07)' } }
          }
        }
      });
      canvas.dataset.chartReady = '1';
    });
  }
  ready(function(){ initProgress(); countUp(); initCharts(); loadHeavyPanels(); });
})();
