// BYS360_DASHBOARD_REBUILD_JS_OK
(function(){
  const payloadNode = document.getElementById('dashboard-rebuild-payload');
  if(!payloadNode){ return; }
  try{
    const payload = JSON.parse(payloadNode.textContent || '{}');
    document.querySelectorAll('[data-chart-key]').forEach((card)=>{
      const key = card.getAttribute('data-chart-key');
      const chart = payload && payload.charts ? payload.charts[key] : null;
      if(!chart){ return; }
      card.setAttribute('data-chart-empty', chart.empty ? '1' : '0');
      card.setAttribute('data-chart-total', String(chart.total || 0));
    });
  }catch(err){
    console.warn('BYS360 dashboard verisi okunamadı', err);
  }
})();
