/* BYS360 Corporate Information Center - Recipient UX V2.3
   Kurumsal Bilgilendirme > Alıcılar sayfasında seçim araçlarını ekler.
   Dış sayfalarda çalışmaz. */
(function () {
  'use strict';

  var path = (window.location.pathname || '').toLocaleLowerCase('tr-TR');
  if (!(path.indexOf('kurumsal-bilgilendirme') >= 0 && path.indexOf('alicilar') >= 0)) {
    return;
  }

  function ready(fn) {
    if (document.readyState !== 'loading') { fn(); }
    else { document.addEventListener('DOMContentLoaded', fn); }
  }

  function norm(value) {
    return String(value || '')
      .toLocaleLowerCase('tr-TR')
      .replace(/\\s+/g, ' ')
      .trim();
  }

  function closestRow(el) {
    return el.closest('tr, .recipient-row, .user-row, .person-row, .employee-row, .list-group-item, .form-check, li, .card, .table-row, .row') || el.parentElement;
  }

  function textOf(row) {
    return row ? (row.innerText || row.textContent || '') : '';
  }

  function isVisible(row) {
    if (!row) { return false; }
    if (row.hidden) { return false; }
    if (row.style && row.style.display === 'none') { return false; }
    var rect = row.getBoundingClientRect();
    return rect.width > 0 || rect.height > 0 || row.offsetParent !== null;
  }

  function checkboxLabel(cb) {
    var row = closestRow(cb);
    var text = textOf(row).replace(/\\s+/g, ' ').trim();
    if (text) { return text.substring(0, 120); }
    return cb.getAttribute('aria-label') || cb.name || cb.value || 'Seçili alıcı';
  }

  function getUnit(row) {
    if (!row) { return ''; }
    var ds = row.dataset || {};
    var direct = ds.unit || ds.birim || ds.organizationUnit || ds.organization || ds.orgUnit || '';
    if (direct) { return direct.trim(); }

    var unitCell = row.querySelector('[data-unit], [data-birim], .unit, .birim, .org-unit, .organization-unit');
    if (unitCell) {
      return (unitCell.getAttribute('data-unit') || unitCell.getAttribute('data-birim') || unitCell.innerText || unitCell.textContent || '').trim();
    }

    var text = textOf(row);
    var m = text.match(/(?:Birim|Üst Birim|Unit)\\s*[:\\-]\\s*([^\\n\\r|•]+)/i);
    if (m && m[1]) { return m[1].trim(); }
    return '';
  }

  function getRoleText(row) {
    if (!row) { return ''; }
    var ds = row.dataset || {};
    return [ds.role, ds.rol, ds.title, ds.unvan, ds.gorev, textOf(row)].join(' ');
  }

  function collectCheckboxes() {
    return Array.prototype.slice.call(document.querySelectorAll('input[type="checkbox"]')).filter(function (cb) {
      if (cb.hasAttribute('data-bys360-recipient-control')) { return false; }
      if (cb.disabled) { return false; }
      var name = norm(cb.name + ' ' + cb.id + ' ' + cb.className);
      if (name.indexOf('csrf') >= 0) { return false; }
      if (name.indexOf('remember') >= 0) { return false; }
      if (name.indexOf('toggle-sidebar') >= 0) { return false; }
      var row = closestRow(cb);
      if (!row) { return false; }
      var rowText = norm(textOf(row));
      if (!rowText && !cb.value) { return false; }
      return true;
    });
  }

  function enhanceFormsWithCsrf() {
    // Aynı sayfadaki tokenı bulan formlara taşır; yeni butonlar form submit etmez ama mevcut formları güvenli tutar.
    var tokenInput = document.querySelector('input[name="csrf_token"][value], input[name="csrfmiddlewaretoken"][value]');
    var meta = document.querySelector('meta[name="csrf-token"], meta[name="csrf_token"]');
    var token = tokenInput ? tokenInput.value : (meta ? meta.getAttribute('content') : '');
    if (!token) { return; }

    Array.prototype.slice.call(document.querySelectorAll('form[method="post"], form[method="POST"]')).forEach(function (form) {
      if (form.querySelector('input[name="csrf_token"], input[name="csrfmiddlewaretoken"]')) { return; }
      var hidden = document.createElement('input');
      hidden.type = 'hidden';
      hidden.name = tokenInput && tokenInput.name ? tokenInput.name : 'csrf_token';
      hidden.value = token;
      form.appendChild(hidden);
    });
  }

  function buildToolbar() {
    var existing = document.querySelector('[data-bys360-recipient-toolbar="1"]');
    if (existing) { return existing; }

    var toolbar = document.createElement('section');
    toolbar.className = 'bys360-recipient-toolbar';
    toolbar.setAttribute('data-bys360-recipient-toolbar', '1');
    toolbar.innerHTML = [
      '<div class="bys360-rt-head">',
      '  <div>',
      '    <div class="bys360-rt-kicker">Kurumsal Bilgilendirme</div>',
      '    <h3>Alıcı seçim araçları</h3>',
      '    <p>Alıcıları hızlı seçmek, filtrelemek ve kontrol etmek için bu alanı kullanın.</p>',
      '  </div>',
      '  <div class="bys360-rt-count"><strong data-bys360-selected-count>0</strong><span>seçili alıcı</span></div>',
      '</div>',
      '<div class="bys360-rt-controls">',
      '  <label class="bys360-rt-field"><span>İsme / e-postaya göre ara</span><input data-bys360-recipient-control="1" data-bys360-search type="search" placeholder="Ad, soyad, e-posta, sicil no, birim veya unvan"></label>',
      '  <label class="bys360-rt-field"><span>Birime göre filtrele</span><input data-bys360-recipient-control="1" data-bys360-unit-filter type="search" list="bys360-recipient-units" placeholder="Birim adı yazın"></label>',
      '  <datalist id="bys360-recipient-units"></datalist>',
      '</div>',
      '<div class="bys360-rt-actions">',
      '  <button type="button" data-bys360-action="select-all">Tümünü seç</button>',
      '  <button type="button" data-bys360-action="select-visible">Görünenleri seç</button>',
      '  <button type="button" data-bys360-action="select-managers">Yönetici / amirleri seç</button>',
      '  <button type="button" data-bys360-action="select-staff">Personeli seç</button>',
      '  <button type="button" data-bys360-action="select-pilot">Pilot grup seç</button>',
      '  <button type="button" data-bys360-action="clear" class="ghost">Seçimleri temizle</button>',
      '</div>',
      '<div class="bys360-rt-selected" data-bys360-selected-panel>',
      '  <div class="bys360-rt-selected-title">Seçili alıcılar</div>',
      '  <div class="bys360-rt-selected-list" data-bys360-selected-list>Henüz alıcı seçilmedi.</div>',
      '</div>'
    ].join('');

    var anchor = document.querySelector('main, .main-content, .content, .container, .container-fluid, body');
    var table = document.querySelector('table');
    var form = document.querySelector('form');
    var target = table || form || anchor.firstElementChild || anchor;
    if (target && target.parentNode) {
      target.parentNode.insertBefore(toolbar, target);
    } else {
      document.body.insertBefore(toolbar, document.body.firstChild);
    }
    return toolbar;
  }

  ready(function () {
    enhanceFormsWithCsrf();

    var boxes = collectCheckboxes();
    if (!boxes.length) {
      // Sayfa verisi geç yüklenirse tekrar dene.
      setTimeout(function () {
        boxes = collectCheckboxes();
        if (boxes.length) { init(boxes); }
      }, 700);
      return;
    }
    init(boxes);
  });

  function init(boxes) {
    var toolbar = buildToolbar();
    var search = toolbar.querySelector('[data-bys360-search]');
    var unitFilter = toolbar.querySelector('[data-bys360-unit-filter]');
    var unitsList = toolbar.querySelector('#bys360-recipient-units');
    var countEl = toolbar.querySelector('[data-bys360-selected-count]');
    var selectedList = toolbar.querySelector('[data-bys360-selected-list]');

    function rows() {
      boxes = collectCheckboxes();
      return boxes.map(function (cb) { return { cb: cb, row: closestRow(cb) }; });
    }

    function refreshUnits() {
      var units = {};
      rows().forEach(function (item) {
        var unit = getUnit(item.row);
        if (unit) { units[unit] = true; }
      });
      unitsList.innerHTML = Object.keys(units).sort(function (a, b) { return a.localeCompare(b, 'tr'); }).map(function (u) {
        return '<option value="' + u.replace(/"/g, '&quot;') + '"></option>';
      }).join('');
    }

    function applyFilter() {
      var q = norm(search && search.value);
      var u = norm(unitFilter && unitFilter.value);
      rows().forEach(function (item) {
        var rowText = norm(textOf(item.row));
        var unitText = norm(getUnit(item.row));
        var matchQ = !q || rowText.indexOf(q) >= 0 || norm(item.cb.value).indexOf(q) >= 0;
        var matchU = !u || unitText.indexOf(u) >= 0 || rowText.indexOf(u) >= 0;
        if (item.row) {
          item.row.style.display = (matchQ && matchU) ? '' : 'none';
        }
      });
      updateSummary();
    }

    function visibleItems() {
      return rows().filter(function (item) { return isVisible(item.row); });
    }

    function setChecked(items, checked) {
      items.forEach(function (item) {
        item.cb.checked = checked;
        item.cb.dispatchEvent(new Event('change', { bubbles: true }));
      });
      updateSummary();
    }

    function updateSummary() {
      var selected = rows().filter(function (item) { return item.cb.checked; });
      countEl.textContent = String(selected.length);
      if (!selected.length) {
        selectedList.textContent = 'Henüz alıcı seçilmedi.';
        selectedList.classList.add('is-empty');
        return;
      }
      selectedList.classList.remove('is-empty');
      selectedList.innerHTML = selected.slice(0, 40).map(function (item) {
        return '<span>' + checkboxLabel(item.cb).replace(/[<>&]/g, function (s) {
          return ({ '<': '&lt;', '>': '&gt;', '&': '&amp;' })[s];
        }) + '</span>';
      }).join('');
      if (selected.length > 40) {
        selectedList.innerHTML += '<em>+' + (selected.length - 40) + ' alıcı daha</em>';
      }
    }

    function selectByRole(kind) {
      var managerWords = ['başkan', 'baskan', 'amir', 'yönetici', 'yonetici', 'koordinatör', 'koordinator', 'müdür', 'mudur', 'şef', 'sef', 'grup başkanı', 'grup baskani'];
      var staffWords = ['personel', 'memur', 'işçi', 'isci', 'çalışan', 'calisan'];
      var words = kind === 'manager' ? managerWords : staffWords;
      var matched = visibleItems().filter(function (item) {
        var txt = norm(getRoleText(item.row));
        return words.some(function (w) { return txt.indexOf(w) >= 0; });
      });
      if (!matched.length && kind === 'staff') {
        matched = visibleItems();
      }
      setChecked(matched, true);
    }

    toolbar.addEventListener('click', function (ev) {
      var btn = ev.target.closest('button[data-bys360-action]');
      if (!btn) { return; }
      var action = btn.getAttribute('data-bys360-action');
      if (action === 'select-all') { setChecked(rows(), true); }
      if (action === 'select-visible') { setChecked(visibleItems(), true); }
      if (action === 'clear') { setChecked(rows(), false); }
      if (action === 'select-managers') { selectByRole('manager'); }
      if (action === 'select-staff') { selectByRole('staff'); }
      if (action === 'select-pilot') {
        var pilot = visibleItems().filter(function (item) {
          return norm(textOf(item.row)).indexOf('pilot') >= 0 || (item.row.dataset && item.row.dataset.pilot === '1');
        });
        if (!pilot.length) { pilot = visibleItems().slice(0, Math.min(5, visibleItems().length)); }
        setChecked(pilot, true);
      }
    });

    if (search) { search.addEventListener('input', applyFilter); }
    if (unitFilter) { unitFilter.addEventListener('input', applyFilter); }
    document.addEventListener('change', function (ev) {
      if (ev.target && ev.target.matches('input[type="checkbox"]')) { updateSummary(); }
    });

    refreshUnits();
    applyFilter();
    updateSummary();
  }
})();
