/* BYS360_MOBILE_APP_EXPERIENCE_V3
   Ayarlar, rol matrisi ve personel ekranları için mobil app davranış katmanı.
*/
(function(){
  'use strict';
  var MOBILE_LIMIT = 900;
  var V3_RE = /settings|ayar|role|rol|permission|yetki|matrix|matris|personnel|personel|users|kullanici|org-units|organization|birim|leave|izin|delegation|vekalet|attendance|devamsizlik/i;
  var SETTINGS_RE = /settings|ayar|role|rol|permission|yetki|matrix|matris/i;
  var PERSONNEL_RE = /personnel|personel|users|kullanici|org-units|organization|birim|leave|izin|delegation|vekalet|attendance|devamsizlik/i;
  function isMobile(){ return window.innerWidth <= MOBILE_LIMIT; }
  function txt(el){ return (el && el.textContent || '').replace(/\s+/g,' ').trim(); }
  function path(){ return location.pathname.toLowerCase(); }
  function kind(){
    var p = path();
    return { v3: V3_RE.test(p), settings: SETTINGS_RE.test(p), personnel: PERSONNEL_RE.test(p) };
  }
  function setBodyClasses(){
    var k = kind();
    document.body.classList.toggle('bys360-mobile-v3', isMobile() && k.v3);
    document.body.classList.toggle('bys360-settings-mobile-v3', isMobile() && k.settings);
    document.body.classList.toggle('bys360-personnel-mobile-v3', isMobile() && k.personnel);
  }
  function shouldCardTable(table){
    var text = (txt(table)+' '+table.className+' '+(table.id||'')).toLowerCase();
    return /rol|role|yetki|permission|matris|matrix|menü|menu|personel|sicil|unvan|birim|izin|vekalet|vekâlet|devamsizlik|devamsızlık|kullanici|kullanıcı|modül|module|ayar|settings|görünürlük|gorunurluk/.test(text);
  }
  function labelTables(){
    if(!kind().v3) return;
    document.querySelectorAll('table:not([data-bys360-mobile-v3])').forEach(function(table){
      var headers = Array.prototype.map.call(table.querySelectorAll('thead th'), txt);
      if(shouldCardTable(table)) table.classList.add('bys360-mobile-v3-card-table');
      if(headers.length){
        table.querySelectorAll('tbody tr').forEach(function(row){
          Array.prototype.forEach.call(row.children, function(cell, i){
            if(headers[i] && !cell.getAttribute('data-label')) cell.setAttribute('data-label', headers[i]);
          });
        });
      }
      table.setAttribute('data-bys360-mobile-v3','1');
    });
  }
  function markMatrix(){
    if(!kind().settings) return;
    document.querySelectorAll('table').forEach(function(table){
      var t = (txt(table)+' '+table.className+' '+(table.id||'')).toLowerCase();
      if(/rol|role|matris|matrix|yetki|permission|menü|menu|modül|module/.test(t)){
        table.classList.add('bys360-role-matrix-mobile-v3','bys360-mobile-v3-card-table');
        table.querySelectorAll('input[type="checkbox"], input[type="radio"]').forEach(function(input){
          input.classList.add('bys360-mobile-toggle-v3');
          var cell = input.closest('td,th,div,label');
          if(cell) cell.classList.add('bys360-mobile-toggle-cell-v3');
        });
      }
    });
  }
  function markPersonnelCards(){
    if(!kind().personnel) return;
    document.querySelectorAll('.card,.panel,.box,.info-card,.user-card,.personnel-card,.profile-card,.summary-card,.metric-card').forEach(function(card){
      if(!card.classList.contains('bys360-mobile-v3-card')) card.classList.add('bys360-mobile-v3-card');
    });
  }
  function markFiltersAndForms(){
    if(!kind().v3) return;
    document.querySelectorAll('form:not([data-bys360-mobile-v3])').forEach(function(form){
      form.classList.add('bys360-mobile-v3-form');
      form.setAttribute('data-bys360-mobile-v3','1');
      var text = txt(form).toLowerCase();
      if(/ara|filtre|search|filter|birim|rol|durum|kategori/.test(text)) form.classList.add('bys360-mobile-v3-filter-form');
      var buttons = form.querySelectorAll('button[type="submit"], input[type="submit"], .btn-primary, .btn-success, .btn-danger, .btn-warning');
      if(buttons.length){
        var last = buttons[buttons.length-1];
        var host = last.closest('.form-actions,.button-row,.text-end,.text-center,.d-flex,.btn-group,.row') || last.parentElement;
        if(host) host.classList.add('bys360-mobile-v3-actionbar');
      }
    });
  }
  function buildQuickTabs(){
    if(!kind().v3 || document.querySelector('.bys360-mobile-quicktabs-v3')) return;
    var links = Array.prototype.slice.call(document.querySelectorAll('.nav-tabs a,.nav-pills a,.submenu a,.tabs a,.settings-tabs a,.personnel-tabs a'))
      .filter(function(a){ var s=txt(a); return s.length>1 && s.length<42; })
      .slice(0,10);
    if(links.length < 2) return;
    var nav=document.createElement('nav'); nav.className='bys360-mobile-quicktabs-v3';
    links.forEach(function(a,i){
      var clone=document.createElement('a'); clone.href=a.href; clone.textContent=txt(a); if(a.classList.contains('active')||a.closest('.active')||i===0) clone.classList.add('is-active'); nav.appendChild(clone);
    });
    var anchor=document.querySelector('.content-wrap main,.content-wrap,.container-fluid,.container,main') || document.body;
    anchor.insertBefore(nav, anchor.firstChild);
  }
  function addHint(){
    if(!kind().v3 || document.querySelector('.bys360-mobile-v3-hint')) return;
    var table=document.querySelector('table.bys360-mobile-v3-card-table');
    if(!table) return;
    var hint=document.createElement('div');
    hint.className='bys360-mobile-v3-hint';
    hint.textContent='Mobil görünümde satırlar kart olarak gösterilir. İşlemler ve yetkiler kart içinden yönetilir.';
    table.parentNode.insertBefore(hint, table);
  }
  function init(){
    if(!document.body) return;
    setBodyClasses();
    if(!isMobile()) return;
    labelTables();
    markMatrix();
    markPersonnelCards();
    markFiltersAndForms();
    buildQuickTabs();
    addHint();
  }
  if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
  window.addEventListener('resize', function(){ window.clearTimeout(window.__bys360MobileV3Timer); window.__bys360MobileV3Timer=setTimeout(init,150); }, {passive:true});
})();
