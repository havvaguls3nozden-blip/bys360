// BYS360 iOS PWA V3.1 Performance Mobile Screens
// Performans sayfalarında mobil kart tablo, puan butonu, sticky aksiyon ve akordeon davranışları.
(function () {
  'use strict';

  var path = (window.location.pathname || '').toLowerCase();
  var isPerformancePage = path.indexOf('/performance') !== -1 || path.indexOf('/performans') !== -1;

  // BYS360_IOS_PWA_V3_1_DASHBOARD_DOM_GUARD_V1
  // Bu dosya mobil performans ekranlarını kart/akordeon yapısına dönüştürür.
  // Masaüstü dashboard sayfasında çalışırsa section/grid DOM yapısını sonradan sarar
  // ve sayfa önce düzgün gelip sonra sol kolona sıkışır. Dashboard kendi responsive
  // gridini kullandığı için bu dönüştürücüden tamamen hariç tutulur.
  var isDashboardPage = path === '/dashboard' || path === '/performance/dashboard' || path.indexOf('/performance/dashboard/') === 0;
  if (!isPerformancePage || isDashboardPage) return;

  var ua = navigator.userAgent || '';
  var isIOS = /iPad|iPhone|iPod/.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  var isStandalone = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;
  var isNarrow = window.matchMedia('(max-width: 992px)').matches;
  var isCoarsePointer = window.matchMedia('(pointer: coarse)').matches;
  var shouldEnhanceMobile = isNarrow || isIOS || isStandalone || isCoarsePointer;
  if (!shouldEnhanceMobile) return;

  var root = document.documentElement;
  var body = document.body;
  root.classList.add('bys-perf-mobile-active');
  body.classList.add('bys-perf-mobile-page');

  function textOf(el) {
    return (el && (el.innerText || el.textContent) || '').replace(/\s+/g, ' ').trim();
  }

  function enhanceTables() {
    var tables = document.querySelectorAll('table');
    tables.forEach(function (table) {
      if (table.classList.contains('bys-mobile-card-table')) return;
      var headers = [];
      var ths = table.querySelectorAll('thead th');
      if (!ths.length) {
        ths = table.querySelectorAll('tr:first-child th, tr:first-child td');
      }
      ths.forEach(function (th, index) {
        headers[index] = textOf(th) || ('Alan ' + (index + 1));
      });
      if (!headers.length) return;
      table.classList.add('bys-mobile-card-table');
      var rows = table.querySelectorAll('tbody tr');
      if (!rows.length) rows = table.querySelectorAll('tr');
      rows.forEach(function (tr) {
        var cells = tr.children || [];
        for (var i = 0; i < cells.length; i++) {
          var cell = cells[i];
          if (!cell || cell.tagName === 'TH') continue;
          if (!cell.getAttribute('data-bys-label')) {
            cell.setAttribute('data-bys-label', headers[i] || ('Alan ' + (i + 1)));
          }
        }
      });
    });
  }

  function enhanceScoreInputs() {
    var selectors = [
      'input[type="radio"][name*="score"]',
      'input[type="radio"][name*="puan"]',
      'input[type="radio"][name*="rating"]',
      'input[type="radio"][name*="rate"]'
    ];
    var radios = Array.prototype.slice.call(document.querySelectorAll(selectors.join(',')));
    var groups = {};
    radios.forEach(function (radio) {
      var value = (radio.value || '').trim();
      if (!/^[1-5]$/.test(value)) return;
      var key = radio.name || ('bys-score-' + Math.random());
      if (!groups[key]) groups[key] = [];
      groups[key].push(radio);
    });
    Object.keys(groups).forEach(function (key) {
      var group = groups[key];
      if (group.length < 2) return;
      if (group[0].closest('.bys-score-choice-group')) return;
      var wrapper = document.createElement('div');
      wrapper.className = 'bys-score-choice-group';
      var first = group[0];
      var parent = first.parentNode;
      parent.insertBefore(wrapper, first);
      group.forEach(function (radio) {
        var label = radio.closest('label');
        var value = radio.value;
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'bys-score-choice' + (radio.checked ? ' is-selected' : '');
        btn.setAttribute('aria-label', value + ' puan');
        btn.textContent = value;
        btn.addEventListener('click', function () {
          radio.checked = true;
          radio.dispatchEvent(new Event('change', { bubbles: true }));
          wrapper.querySelectorAll('.bys-score-choice').forEach(function (b) { b.classList.remove('is-selected'); });
          btn.classList.add('is-selected');
        });
        wrapper.appendChild(btn);
        radio.style.position = 'absolute';
        radio.style.opacity = '0';
        radio.style.pointerEvents = 'none';
        radio.tabIndex = -1;
        if (label && label !== wrapper && label.parentNode) {
          var labelText = textOf(label).replace(value, '').trim();
          if (!labelText || labelText.length < 3) {
            label.style.display = 'none';
          }
        }
      });
    });
  }

  function enhanceStickyActions() {
    if (document.querySelector('.bys-mobile-action-sticky')) return;
    var candidates = Array.prototype.slice.call(document.querySelectorAll(
      'button[type="submit"], input[type="submit"], .btn-primary, .btn-success, .btn-danger, a.btn-primary, a.btn-success, a.btn-danger'
    )).filter(function (el) {
      if (!el || !el.offsetParent) return false;
      var t = textOf(el).toLowerCase();
      return /kaydet|gönder|gonder|yayınla|yayinla|onay|reddet|iade|tamamla|puanla|değerlendir|degerlendir/.test(t);
    });
    if (!candidates.length) return;
    var sticky = document.createElement('div');
    sticky.className = 'bys-mobile-action-sticky';
    candidates.slice(0, 3).forEach(function (source) {
      var clone = source.cloneNode(true);
      clone.removeAttribute('id');
      clone.addEventListener('click', function (ev) {
        ev.preventDefault();
        source.click();
      });
      sticky.appendChild(clone);
      source.classList.add('bys-mobile-hide-source-action');
    });
    document.body.appendChild(sticky);
  }

  function enhanceCollapsibleSections() {
    var sections = Array.prototype.slice.call(document.querySelectorAll('.card, .panel, .glass-card, section'));
    sections.slice(0, 20).forEach(function (section) {
      if (section.classList.contains('bys-mobile-collapsible')) return;
      var title = section.querySelector('h2, h3, .card-title, .section-title, .panel-title');
      if (!title) return;
      var titleText = textOf(title);
      if (!titleText || titleText.length > 90) return;
      var bodyWrap = document.createElement('div');
      bodyWrap.className = 'bys-mobile-section-body';
      var children = Array.prototype.slice.call(section.childNodes);
      children.forEach(function (child) {
        if (child === title) return;
        bodyWrap.appendChild(child);
      });
      var toggle = document.createElement('button');
      toggle.type = 'button';
      toggle.className = 'bys-mobile-section-toggle';
      toggle.textContent = titleText;
      toggle.addEventListener('click', function () {
        section.classList.toggle('is-collapsed');
      });
      section.classList.add('bys-mobile-collapsible');
      title.style.display = 'none';
      section.appendChild(toggle);
      section.appendChild(bodyWrap);
    });
  }

  function addStatusChips() {
    var badges = document.querySelectorAll('.badge, .status, [class*="status"], [class*="badge"]');
    badges.forEach(function (badge) {
      if (badge.classList.contains('bys-mobile-status-chip')) return;
      var t = textOf(badge);
      if (t && t.length <= 42) badge.classList.add('bys-mobile-status-chip');
    });
  }

  function runAll() {
    enhanceTables();
    enhanceScoreInputs();
    enhanceStickyActions();
    enhanceCollapsibleSections();
    addStatusChips();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', runAll);
  } else {
    runAll();
  }

  var observer = new MutationObserver(function () {
    window.clearTimeout(observer._bysTimer);
    observer._bysTimer = window.setTimeout(runAll, 120);
  });
  observer.observe(document.documentElement, { childList: true, subtree: true });
})();
