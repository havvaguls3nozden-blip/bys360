/* BYS360_MOBILE_UYUM_FAZ1_V1_JS
   Mobil uyum davranışları: menü düğmesi, tablo etiketleme, güvenli kart/scroll modu,
   mobil aksiyon alanı, taşma kontrolü ve dinamik içerik gözlemleme.
*/
(function(){
  'use strict';

  var doc = document;
  var root = doc.documentElement;
  var body = doc.body;
  if(!body) return;

  var BREAKPOINT = 1100;
  var CARD_TABLE_MAX_COLUMNS = 6;
  var PATH = (window.location.pathname || '').toLowerCase();
  var isPerformance = PATH.indexOf('/performance') === 0 || PATH.indexOf('/performans') === 0;
  var isCommunication = PATH.indexOf('/messages') === 0 || PATH.indexOf('/surveys') === 0 || PATH.indexOf('/survey') === 0 || PATH.indexOf('/support') === 0 || PATH.indexOf('/feedback') === 0;
  var isAdminHeavy = PATH.indexOf('/admin') === 0 || PATH.indexOf('/settings') === 0 || PATH.indexOf('/ayar') >= 0;

  root.classList.add('bys360-mobile-faz1-v1');
  body.classList.add('bys360-mobile-faz1-v1');
  if(isPerformance) body.classList.add('bys360-mobile-performance');
  if(isCommunication) body.classList.add('bys360-mobile-communication');
  if(isAdminHeavy) body.classList.add('bys360-mobile-admin-heavy');

  function isMobile(){ return window.innerWidth <= BREAKPOINT; }
  function norm(text){ return (text || '').replace(/\s+/g, ' ').trim(); }
  function safeClosest(el, selector){ try { return el && el.closest(selector); } catch(e){ return null; } }

  function ensureBackdrop(){
    var backdrop = doc.querySelector('[data-bys360-mobile-menu-backdrop="true"]');
    if(backdrop) return backdrop;
    backdrop = doc.createElement('button');
    backdrop.type = 'button';
    backdrop.className = 'bys360-mobile-menu-backdrop';
    backdrop.setAttribute('aria-label', 'Menüyü kapat');
    backdrop.setAttribute('data-bys360-mobile-menu-backdrop', 'true');
    backdrop.addEventListener('click', closeMenu);
    body.appendChild(backdrop);
    return backdrop;
  }

  function openMenu(){
    ensureBackdrop();
    body.classList.add('bys360-mobile-menu-open');
    var btn = doc.querySelector('[data-bys360-mobile-menu-toggle="true"]');
    if(btn) btn.setAttribute('aria-expanded', 'true');
  }

  function closeMenu(){
    body.classList.remove('bys360-mobile-menu-open');
    var btn = doc.querySelector('[data-bys360-mobile-menu-toggle="true"]');
    if(btn) btn.setAttribute('aria-expanded', 'false');
  }

  function toggleMenu(){
    if(body.classList.contains('bys360-mobile-menu-open')) closeMenu();
    else openMenu();
  }

  function createMenuButton(){
    if(doc.querySelector('[data-bys360-mobile-menu-toggle="true"]')) return;
    var sidebar = doc.querySelector('.app-sidebar');
    if(!sidebar) return;

    var btn = doc.createElement('button');
    btn.type = 'button';
    btn.className = 'bys360-mobile-menu-toggle';
    btn.setAttribute('data-bys360-mobile-menu-toggle', 'true');
    btn.setAttribute('aria-label', 'Menüyü aç veya kapat');
    btn.setAttribute('aria-expanded', 'false');
    btn.innerHTML = '<span aria-hidden="true">☰</span>';
    btn.addEventListener('click', toggleMenu);

    var target = doc.querySelector('.topbar-left') || doc.querySelector('.topbar') || doc.querySelector('header') || body;
    if(target === body) body.insertBefore(btn, body.firstChild);
    else target.insertBefore(btn, target.firstChild);

    ensureBackdrop();
  }

  function closeMenuOnNavigation(){
    var sidebar = doc.querySelector('.app-sidebar');
    if(!sidebar) return;
    sidebar.addEventListener('click', function(event){
      var link = safeClosest(event.target, 'a[href]');
      if(link && isMobile()) closeMenu();
    }, true);
  }

  function headersForTable(table){
    var headers = Array.prototype.map.call(table.querySelectorAll('thead th'), function(th){ return norm(th.textContent); }).filter(Boolean);
    if(headers.length) return headers;
    var firstRow = table.querySelector('tr');
    if(!firstRow) return [];
    return Array.prototype.map.call(firstRow.children, function(cell){ return norm(cell.textContent); }).filter(Boolean);
  }

  function shouldCardTable(table, headers){
    if(table.classList.contains('bys360-mobile-v1-ignore') || table.classList.contains('bys360-mobile-v5-ignore')) return false;
    if(table.classList.contains('table-calendar') || table.classList.contains('fc-scrollgrid')) return false;
    if(safeClosest(table, '.tox, .note-editor, .fc, .CodeMirror, .skip-mobile-wrap, .skip-mobile-normalize')) return false;
    if(table.getAttribute('data-mobile-mode') === 'scroll') return false;
    if(table.getAttribute('data-mobile-mode') === 'card') return true;
    var columnCount = headers.length || ((table.querySelector('tr') || {}).children || []).length || 0;
    var text = norm(table.textContent).toLowerCase();
    var scoreLike = /puan|karne|kriter|değerlendirme|degerlendirme|başkan|baskan|onay|anket|destek|bildirim|duyuru|mesaj|görev|gorev/.test(text);
    if(isPerformance && columnCount <= 8) return true;
    if(isCommunication && columnCount <= 7) return true;
    if(isAdminHeavy && columnCount > CARD_TABLE_MAX_COLUMNS) return false;
    return scoreLike && columnCount <= CARD_TABLE_MAX_COLUMNS;
  }

  function ensureScrollWrapper(table){
    if(safeClosest(table, '.table-responsive, .mobile-table-wrap, .bys360-mobile-scroll-wrap')) return;
    var wrap = doc.createElement('div');
    wrap.className = 'bys360-mobile-scroll-wrap';
    table.parentNode.insertBefore(wrap, table);
    wrap.appendChild(table);
  }

  function labelAndModeTables(scope){
    var tables = (scope || doc).querySelectorAll('table');
    Array.prototype.forEach.call(tables, function(table){
      if(table.dataset.bys360MobileFaz1Processed === 'true') return;
      if(safeClosest(table, '.tox, .note-editor, .fc, .CodeMirror')) return;
      table.dataset.bys360MobileFaz1Processed = 'true';
      var headers = headersForTable(table);
      Array.prototype.forEach.call(table.querySelectorAll('tbody tr'), function(row){
        Array.prototype.forEach.call(row.children, function(cell, index){
          if(!cell.getAttribute('data-label')) cell.setAttribute('data-label', headers[index] || 'Bilgi');
        });
      });
      if(shouldCardTable(table, headers)){
        table.classList.add('bys360-mobile-card-table');
        table.classList.remove('bys360-mobile-scroll-table');
      }else{
        table.classList.add('bys360-mobile-scroll-table');
        ensureScrollWrapper(table);
      }
    });
  }

  function markActionBars(scope){
    var selectors = '.form-actions,.action-buttons,.actions,.page-actions,.header-actions,.btn-toolbar,.submit-row,.card-actions,.top-actions';
    Array.prototype.forEach.call((scope || doc).querySelectorAll(selectors), function(el){
      if(el.dataset.bys360MobileActions === 'true') return;
      var text = norm(el.textContent).toLowerCase();
      if(/kaydet|oluştur|olustur|onayla|yayınla|yayinla|gönder|gonder|puanla|tamamla|reddet|iade|güncelle|guncelle/.test(text)){
        el.classList.add('bys360-mobile-sticky-actions');
        el.dataset.bys360MobileActions = 'true';
      }
    });
  }

  function normalizeWideInlineElements(scope){
    if(!isMobile()) return;
    var limit = Math.max(360, window.innerWidth - 24);
    Array.prototype.forEach.call((scope || doc).querySelectorAll('[style]'), function(el){
      if(safeClosest(el, '.app-sidebar, .topbar, .modal, .tox, .note-editor, .fc, .CodeMirror')) return;
      var tag = el.tagName;
      if(/^(SCRIPT|STYLE|LINK|META)$/.test(tag)) return;
      var style = (el.getAttribute('style') || '').toLowerCase();
      var hit = false;
      style.replace(/(?:min-width|width|max-width)\s*:\s*(\d+)px/g, function(_, px){
        if(parseInt(px, 10) > limit) hit = true;
      });
      if(hit){
        el.style.maxWidth = '100%';
        el.style.minWidth = '0';
        el.style.width = '100%';
        el.classList.add('bys360-mobile-inline-width-fixed');
      }
      if(style.indexOf('white-space:nowrap') >= 0 || style.indexOf('white-space: nowrap') >= 0){
        el.style.whiteSpace = 'normal';
        el.style.overflowWrap = 'anywhere';
      }
    });
  }

  function markLongText(scope){
    Array.prototype.forEach.call((scope || doc).querySelectorAll('td,th,p,li,span,div,a,label'), function(el){
      if(el.children.length > 3) return;
      var text = norm(el.textContent);
      if(text.length > 42 && /[\/_.-]{2,}|[A-Z0-9_]{10,}/.test(text)){
        el.classList.add('bys360-mobile-wrap-token');
      }
    });
  }

  function applyAll(scope){
    createMenuButton();
    labelAndModeTables(scope || doc);
    markActionBars(scope || doc);
    normalizeWideInlineElements(scope || doc);
    markLongText(scope || doc);
  }

  function observeDynamicContent(){
    if(!('MutationObserver' in window)) return;
    var timer = null;
    var observer = new MutationObserver(function(records){
      var should = records.some(function(r){ return r.addedNodes && r.addedNodes.length; });
      if(!should) return;
      if(timer) window.clearTimeout(timer);
      timer = window.setTimeout(function(){ applyAll(doc); }, 120);
    });
    observer.observe(body, {childList:true, subtree:true});
  }

  doc.addEventListener('keydown', function(event){
    if(event.key === 'Escape') closeMenu();
  });

  window.addEventListener('resize', function(){
    if(!isMobile()) closeMenu();
    window.clearTimeout(window.__bys360MobileFaz1ResizeTimer);
    window.__bys360MobileFaz1ResizeTimer = window.setTimeout(function(){ applyAll(doc); }, 120);
  }, {passive:true});

  if(doc.readyState === 'loading'){
    doc.addEventListener('DOMContentLoaded', function(){
      applyAll(doc);
      closeMenuOnNavigation();
      observeDynamicContent();
    });
  }else{
    applyAll(doc);
    closeMenuOnNavigation();
    observeDynamicContent();
  }
})();
