
// BYS360_CIC_V4_4_PERFORMANCE_STYLE_RESET
(function(){
  "use strict";
  var ROOT = "/dashboard/kurumsal-bilgilendirme";
  var CELEBRATIONS = ROOT + "/kutlamalar";
  function pathOf(x){
    try { return new URL(x || window.location.href, window.location.origin).pathname.replace(/\/+$/, "") || "/"; }
    catch(e){ return String(x || "").replace(/\/+$/, "") || "/"; }
  }
  function isCic(){ return pathOf(window.location.href).indexOf(ROOT) === 0; }
  function cleanLegacyInjected(){
    document.querySelectorAll('.cic-v41b-topbar,.cic-v41b-tabs').forEach(function(el){ el.remove(); });
  }
  function syncActive(){
    if(!isCic()) return;
    document.body.classList.add('bys360-cic-v44');
    cleanLegacyInjected();
    var current = pathOf(window.location.href);
    document.querySelectorAll('a[href*="/dashboard/kurumsal-bilgilendirme"]').forEach(function(a){
      var href = pathOf(a.getAttribute('href'));
      var active = false;
      if (current === ROOT) active = (href === ROOT);
      else if (current.indexOf(CELEBRATIONS) === 0) active = (href === CELEBRATIONS);
      else active = (href !== ROOT && href !== CELEBRATIONS && (current === href || current.indexOf(href + "/") === 0));
      ['active','is-active','current','selected','router-link-active'].forEach(function(c){ a.classList.remove(c); });
      a.removeAttribute('aria-current');
      if(active){ a.classList.add('active'); a.setAttribute('aria-current','page'); }
    });
    document.querySelectorAll('.cicp-metric strong').forEach(function(el){
      var t=(el.textContent||'').trim().toLowerCase();
      if(t === 'önce' || t === 'pilot önce' || t === 'pilot') el.textContent='Aktif / Pasif';
    });
  }
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', syncActive); else syncActive();
  setTimeout(syncActive, 200); setTimeout(syncActive, 800); setTimeout(syncActive, 1600);
})();
