(function(){
  function initManage(){
    const root = document.querySelector('[data-survey-manage="1"]');
    const mount = document.getElementById('surveySmartFilterMount');
    if (!root || !mount) return;
    const rows = Array.from(document.querySelectorAll('.survey-data-row'));
    if (!rows.length) return;
    const visibleRows = rows.filter((row) => !row.classList.contains('row-hidden'));
    const total = visibleRows.length;
    const published = visibleRows.filter((row) => row.dataset.status === 'published').length;
    const drafts = visibleRows.filter((row) => row.dataset.status === 'draft').length;
    const archived = visibleRows.filter((row) => row.dataset.status === 'archived').length;
    const avgRate = visibleRows.reduce((acc, row) => acc + Number(row.dataset.rate || 0), 0) / (total || 1);
    const noResponse = visibleRows.filter((row) => Number(row.dataset.responseCount || 0) === 0).length;
    const lowCoverage = visibleRows.filter((row) => Number(row.dataset.rate || 0) < 50).length;
    mount.innerHTML = `
      <div class="phase1-manage-board">
        <div class="phase1-manage-card">
          <span class="kicker"><i class="fa-solid fa-table-cells-large"></i> Özet</span>
          <h4>Anket özeti</h4>
          <p>Görünen kayıtların özet durumu.</p>
        </div>
        <div class="phase1-manage-card">
          <span class="kicker"><i class="fa-solid fa-bullhorn"></i> Yayımlanan</span>
          <h4>${published} yayımlanan anket</h4>
          <p>Yanıt kabul eden kayıt sayısı.</p>
        </div>
        <div class="phase1-manage-card">
          <span class="kicker"><i class="fa-solid fa-pen-ruler"></i> Taslak</span>
          <h4>${drafts} taslak anket</h4>
          <p>Hazırlık aşamasındaki kayıt sayısı.</p>
        </div>
        <div class="phase1-manage-card">
          <span class="kicker"><i class="fa-solid fa-box-archive"></i> Arşiv</span>
          <h4>${archived} arşiv kaydı</h4>
          <p>Arşivde tutulan kayıt sayısı.</p>
        </div>
      </div>
      <div class="phase1-manage-metrics">
        <div class="item"><span class="label">Görünen kayıt</span><span class="value">${total}</span></div>
        <div class="item"><span class="label">Ortalama oran</span><span class="value">%${avgRate.toFixed(1)}</span></div>
        <div class="item"><span class="label">Sıfır yanıt</span><span class="value">${noResponse}</span></div>
        <div class="item"><span class="label">%50 altı</span><span class="value">${lowCoverage}</span></div>
      </div>`;
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initManage);
  else initManage();
})();
