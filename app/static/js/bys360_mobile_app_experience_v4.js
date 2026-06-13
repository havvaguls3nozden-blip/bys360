/* BYS360_MOBILE_APP_EXPERIENCE_V4_FINAL_GATE */
(function(){
  'use strict';
  var doc = document;
  var root = doc.documentElement;
  var body = doc.body;
  if(!body) return;
  root.classList.add('bys360-mobile-v4-html');
  body.classList.add('bys360-mobile-v4-final');

  var path = (window.location.pathname || '').toLowerCase();
  var isPerformance = path.indexOf('/performance') === 0 || path.indexOf('/performans') === 0;
  var isSettings = path.indexOf('/settings') === 0 || path.indexOf('/ayar') >= 0 || path.indexOf('/admin') === 0;
  var isPersonnel = path.indexOf('/personnel') === 0 || path.indexOf('/personel') === 0 || path.indexOf('/users') >= 0;
  var isPresidentApproval = path.indexOf('president') >= 0 || path.indexOf('baskan') >= 0 || path.indexOf('başkan') >= 0 || path.indexOf('onay') >= 0;
  if(isPerformance) body.classList.add('bys360-performance-mobile-v4');
  if(isSettings) body.classList.add('bys360-settings-mobile-v4');
  if(isPersonnel) body.classList.add('bys360-personnel-mobile-v4');
  if(isPresidentApproval) body.classList.add('bys360-president-approval-mobile-v4');

  function norm(s){ return (s || '').replace(/\s+/g,' ').trim(); }
  function labelTables(scope){
    var tables = (scope || doc).querySelectorAll('table');
    tables.forEach(function(table){
      if(table.classList.contains('bys360-mobile-v4-ignore')) return;
      table.classList.add('bys360-mobile-v4-card-table');
      var headers = Array.prototype.map.call(table.querySelectorAll('thead th'), function(th){ return norm(th.textContent); });
      if(!headers.length){
        var first = table.querySelector('tr');
        if(first){
          headers = Array.prototype.map.call(first.children, function(cell){ return norm(cell.textContent); });
        }
      }
      table.querySelectorAll('tbody tr').forEach(function(row){
        Array.prototype.forEach.call(row.children, function(cell, i){
          if(!cell.getAttribute('data-label')) cell.setAttribute('data-label', headers[i] || 'Bilgi');
        });
      });
    });
  }

  function markPerformanceShells(){
    if(!isPerformance) return;
    var candidates = doc.querySelectorAll('form, .card, .panel, .scorecard, .evaluation, .performance, .president-approval, .process-history');
    candidates.forEach(function(el){
      var t = (el.className || '') + ' ' + (el.id || '') + ' ' + norm(el.textContent).slice(0,220).toLowerCase();
      if(/puan|karne|değerlendirme|degerlendirme|kriter|başkan|baskan|onay|süreç|surec/.test(t)){
        el.classList.add('bys360-mobile-v4-score-shell');
      }
    });
  }

  function markStickyActions(){
    var selectors = ['.form-actions','.action-buttons','.actions','.btn-toolbar','.submit-row'];
    selectors.forEach(function(sel){
      doc.querySelectorAll(sel).forEach(function(el){
        var text = norm(el.textContent).toLowerCase();
        if(/kaydet|onayla|yayınla|yayinla|gönder|gonder|puanla|tamamla|reddet|iade/.test(text)){
          el.classList.add('bys360-mobile-v4-sticky-actions');
        }
      });
    });
  }

  function markTabs(){
    doc.querySelectorAll('.nav-tabs,.tabs,.submenu,.module-tabs,.tab-list').forEach(function(el){
      el.classList.add('bys360-mobile-v4-tabs');
    });
  }

  function finalAudit(){
    var bad = [];
    doc.querySelectorAll('body *').forEach(function(el){
      var r = el.getBoundingClientRect && el.getBoundingClientRect();
      if(!r) return;
      if(r.width > window.innerWidth + 3 && !/SCRIPT|STYLE|HTML|BODY/.test(el.tagName)) bad.push(el);
    });
    body.setAttribute('data-bys360-mobile-v4-overflow-count', String(bad.length));
    if(bad.length){ bad.slice(0,20).forEach(function(el){ el.classList.add('bys360-mobile-v4-overflow-guard'); }); }
  }

  function run(){
    labelTables(doc);
    markPerformanceShells();
    markStickyActions();
    markTabs();
    finalAudit();
  }
  if(doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', run); else run();
  window.addEventListener('resize', function(){ window.clearTimeout(window.__bys360MobileV4Resize); window.__bys360MobileV4Resize = window.setTimeout(finalAudit, 160); });

  if(window.MutationObserver){
    new MutationObserver(function(mutations){
      var should=false;
      mutations.forEach(function(m){ if(m.addedNodes && m.addedNodes.length) should=true; });
      if(should) window.setTimeout(run, 80);
    }).observe(doc.body, {childList:true, subtree:true});
  }
})();
