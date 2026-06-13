// BYS360_CIC_V3_0_RECIPIENTS_PRO_USABILITY_V1
(function(){
  function norm(v){ return (v || '').toString().toLocaleLowerCase('tr-TR').trim(); }
  function ready(fn){ if(document.readyState !== 'loading') fn(); else document.addEventListener('DOMContentLoaded', fn); }
  ready(function(){
    var root = document.querySelector('[data-recipient-page]');
    if(!root) return;
    var cards = Array.prototype.slice.call(root.querySelectorAll('[data-rec-card]'));
    var search = root.querySelector('#recipientSearch');
    var unitFilter = root.querySelector('#recipientUnitFilter');
    var emailFilter = root.querySelector('#recipientEmailFilter');
    var typeFilter = root.querySelector('#recipientTypeFilter');
    var visibleCount = root.querySelector('#visibleCount');
    var staffCount = root.querySelector('#staffCount');
    var managerCount = root.querySelector('#managerCount');
    var totalSelectedCount = root.querySelector('#totalSelectedCount');
    var missingEmailCount = root.querySelector('#missingEmailCount');
    var selectedPreview = root.querySelector('#selectedPreview');

    var unitMap = {};
    cards.forEach(function(card){
      var unit = (card.getAttribute('data-unit') || '').trim();
      if(unit && unit !== '-') unitMap[unit] = true;
    });
    Object.keys(unitMap).sort(function(a,b){return a.localeCompare(b,'tr');}).forEach(function(unit){
      var opt = document.createElement('option');
      opt.value = unit;
      opt.textContent = unit;
      unitFilter && unitFilter.appendChild(opt);
    });

    function getChecks(card){
      return {
        manager: card.querySelector('[data-manager-check]'),
        staff: card.querySelector('[data-staff-check]')
      };
    }
    function isVisible(card){ return !card.classList.contains('is-hidden'); }
    function selectedCards(){
      return cards.filter(function(card){ var c=getChecks(card); return (c.manager && c.manager.checked) || (c.staff && c.staff.checked); });
    }
    function applyFilters(){
      var q = norm(search && search.value);
      var unit = unitFilter ? unitFilter.value : '';
      var emailState = emailFilter ? emailFilter.value : '';
      var type = typeFilter ? typeFilter.value : '';
      cards.forEach(function(card){
        var c = getChecks(card);
        var hay = norm(card.getAttribute('data-search'));
        var cardUnit = card.getAttribute('data-unit') || '';
        var emailOk = card.getAttribute('data-email-ok') === '1';
        var isManager = !!(c.manager && c.manager.checked);
        var isStaff = !!(c.staff && c.staff.checked);
        var any = isManager || isStaff;
        var ok = true;
        if(q && hay.indexOf(q) === -1) ok = false;
        if(unit && cardUnit !== unit) ok = false;
        if(emailState === 'ok' && !emailOk) ok = false;
        if(emailState === 'missing' && emailOk) ok = false;
        if(type === 'selected' && !any) ok = false;
        if(type === 'manager' && !isManager) ok = false;
        if(type === 'staff' && !isStaff) ok = false;
        if(type === 'none' && any) ok = false;
        card.classList.toggle('is-hidden', !ok);
      });
      updateSummary();
    }
    function updateSummary(){
      var staff = 0, manager = 0, missing = 0, visible = 0;
      var preview = [];
      cards.forEach(function(card){
        if(isVisible(card)) visible += 1;
        var c = getChecks(card);
        var s = !!(c.staff && c.staff.checked);
        var m = !!(c.manager && c.manager.checked);
        card.classList.toggle('is-selected', s || m);
        if(s) staff += 1;
        if(m) manager += 1;
        if((s || m) && card.getAttribute('data-email-ok') !== '1') missing += 1;
        if((s || m) && preview.length < 8){
          preview.push({
            name: card.getAttribute('data-name') || 'Kullanıcı',
            role: [m ? 'Yönetici' : null, s ? 'Personel' : null].filter(Boolean).join(' + ')
          });
        }
      });
      if(visibleCount) visibleCount.textContent = visible;
      if(staffCount) staffCount.textContent = staff;
      if(managerCount) managerCount.textContent = manager;
      if(totalSelectedCount) totalSelectedCount.textContent = staff + manager;
      if(missingEmailCount) missingEmailCount.textContent = missing;
      if(selectedPreview){
        if(!preview.length){
          selectedPreview.innerHTML = '<span class="cic-rec-muted">Henüz seçim yok.</span>';
        } else {
          selectedPreview.innerHTML = preview.map(function(item){
            return '<div class="cic-rec-selected-item"><strong></strong><span></span></div>';
          }).join('');
          Array.prototype.slice.call(selectedPreview.querySelectorAll('.cic-rec-selected-item')).forEach(function(row, i){
            row.querySelector('strong').textContent = preview[i].name;
            row.querySelector('span').textContent = preview[i].role;
          });
          if(selectedCards().length > preview.length){
            var more = document.createElement('span');
            more.className = 'cic-rec-muted';
            more.textContent = '+' + (selectedCards().length - preview.length) + ' kayıt daha seçili';
            selectedPreview.appendChild(more);
          }
        }
      }
    }
    function targetCards(scope){
      return cards.filter(function(card){
        if(scope === 'visible' && !isVisible(card)) return false;
        if(scope === 'email' && card.getAttribute('data-email-ok') !== '1') return false;
        return true;
      });
    }
    function setSelection(list, opts){
      list.forEach(function(card){
        var c = getChecks(card);
        if(opts.staff !== undefined && c.staff) c.staff.checked = opts.staff;
        if(opts.manager !== undefined && c.manager) c.manager.checked = opts.manager;
      });
      applyFilters();
    }
    root.addEventListener('click', function(ev){
      var btn = ev.target.closest('[data-rec-action]');
      if(!btn) return;
      ev.preventDefault();
      var action = btn.getAttribute('data-rec-action');
      if(action === 'select-visible-staff') setSelection(targetCards('visible'), {staff:true});
      if(action === 'select-visible-managers') setSelection(targetCards('visible'), {manager:true});
      if(action === 'select-visible-both') setSelection(targetCards('visible'), {manager:true, staff:true});
      if(action === 'select-email-staff') setSelection(targetCards('email'), {staff:true});
      if(action === 'clear-visible') setSelection(targetCards('visible'), {manager:false, staff:false});
      if(action === 'clear-all') setSelection(cards, {manager:false, staff:false});
    });
    [search, unitFilter, emailFilter, typeFilter].forEach(function(el){ if(el) el.addEventListener('input', applyFilters); if(el) el.addEventListener('change', applyFilters); });
    root.addEventListener('change', function(ev){ if(ev.target.matches('[data-manager-check],[data-staff-check]')) updateSummary(); });
    applyFilters();
  });
})();
