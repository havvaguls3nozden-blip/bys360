// BYS360_CIC_V3_0_RECIPIENTS_SAVE_PERSISTENCE_V2
(function(){
  function ready(fn){ if(document.readyState !== 'loading') fn(); else document.addEventListener('DOMContentLoaded', fn); }
  function norm(v){ return (v || '').toString().toLocaleLowerCase('tr-TR').trim(); }
  ready(function(){
    var root = document.querySelector('[data-cic-recipient-save-v2]');
    if(!root) return;
    var form = root.querySelector('#cicRecipientSaveFormV2');
    var cards = Array.prototype.slice.call(root.querySelectorAll('[data-rec2-card]'));
    var search = root.querySelector('#rec2Search');
    var unit = root.querySelector('#rec2Unit');
    var email = root.querySelector('#rec2Email');
    var type = root.querySelector('#rec2Type');
    var visibleCount = root.querySelector('#rec2VisibleCount');
    var staffCount = root.querySelector('#rec2StaffCount');
    var managerCount = root.querySelector('#rec2ManagerCount');
    var totalCount = root.querySelector('#rec2TotalCount');
    var missingCount = root.querySelector('#rec2MissingCount');
    var preview = root.querySelector('#rec2Preview');
    var debugStaff = root.querySelector('#debugStaffCount');
    var debugManager = root.querySelector('#debugManagerCount');

    var units = {};
    cards.forEach(function(card){ var u=(card.getAttribute('data-unit')||'').trim(); if(u && u !== '-') units[u]=true; });
    Object.keys(units).sort(function(a,b){return a.localeCompare(b,'tr');}).forEach(function(u){ var o=document.createElement('option'); o.value=u; o.textContent=u; unit && unit.appendChild(o); });

    function checks(card){ return { staff: card.querySelector('[data-rec2-staff]'), manager: card.querySelector('[data-rec2-manager]') }; }
    function visible(card){ return !card.classList.contains('is-hidden'); }
    function selected(card){ var c=checks(card); return !!((c.staff && c.staff.checked) || (c.manager && c.manager.checked)); }
    function filter(){
      var q = norm(search && search.value), u = unit ? unit.value : '', e = email ? email.value : '', t = type ? type.value : '';
      cards.forEach(function(card){
        var c = checks(card), isStaff=!!(c.staff&&c.staff.checked), isManager=!!(c.manager&&c.manager.checked), any=isStaff||isManager;
        var ok=true;
        if(q && norm(card.getAttribute('data-search')).indexOf(q) === -1) ok=false;
        if(u && (card.getAttribute('data-unit')||'') !== u) ok=false;
        if(e === 'ok' && card.getAttribute('data-email-ok') !== '1') ok=false;
        if(e === 'missing' && card.getAttribute('data-email-ok') === '1') ok=false;
        if(t === 'selected' && !any) ok=false;
        if(t === 'staff' && !isStaff) ok=false;
        if(t === 'manager' && !isManager) ok=false;
        if(t === 'none' && any) ok=false;
        card.classList.toggle('is-hidden', !ok);
      });
      summary();
    }
    function summary(){
      var st=0, mn=0, miss=0, vis=0, rows=[];
      cards.forEach(function(card){
        if(visible(card)) vis++;
        var c=checks(card), s=!!(c.staff&&c.staff.checked), m=!!(c.manager&&c.manager.checked);
        card.classList.toggle('is-selected', s||m);
        if(s) st++; if(m) mn++; if((s||m) && card.getAttribute('data-email-ok') !== '1') miss++;
        if((s||m) && rows.length < 8) rows.push({name:card.getAttribute('data-name')||'Kullanıcı', role:[m?'Yönetici':null, s?'Personel':null].filter(Boolean).join(' + ')});
      });
      if(visibleCount) visibleCount.textContent=vis;
      if(staffCount) staffCount.textContent=st;
      if(managerCount) managerCount.textContent=mn;
      if(totalCount) totalCount.textContent=st+mn;
      if(missingCount) missingCount.textContent=miss;
      if(debugStaff) debugStaff.value=st;
      if(debugManager) debugManager.value=mn;
      if(preview){
        preview.innerHTML='';
        if(!rows.length){ var empty=document.createElement('span'); empty.className='cic-rec2-muted'; empty.textContent='Henüz seçim yok.'; preview.appendChild(empty); }
        else { rows.forEach(function(r){ var d=document.createElement('div'); d.className='cic-rec2-preview-item'; var strong=document.createElement('strong'); strong.textContent=r.name; var span=document.createElement('span'); span.textContent=r.role; d.appendChild(strong); d.appendChild(span); preview.appendChild(d); }); if((st+mn)>rows.length){ var more=document.createElement('span'); more.className='cic-rec2-muted'; more.textContent='+'+((st+mn)-rows.length)+' seçim daha var'; preview.appendChild(more); } }
      }
    }
    function target(scope){ return cards.filter(function(card){ if(scope==='visible' && !visible(card)) return false; if(scope==='email' && card.getAttribute('data-email-ok') !== '1') return false; return true; }); }
    function set(list, opts){ list.forEach(function(card){ var c=checks(card); if(opts.staff !== undefined && c.staff) c.staff.checked=opts.staff; if(opts.manager !== undefined && c.manager) c.manager.checked=opts.manager; }); filter(); }
    root.addEventListener('click', function(ev){ var btn=ev.target.closest('[data-rec2-action]'); if(!btn) return; ev.preventDefault(); var a=btn.getAttribute('data-rec2-action'); if(a==='visible-staff') set(target('visible'),{staff:true}); if(a==='visible-manager') set(target('visible'),{manager:true}); if(a==='email-staff') set(target('email'),{staff:true}); if(a==='visible-clear') set(target('visible'),{staff:false,manager:false}); if(a==='all-clear') set(cards,{staff:false,manager:false}); });
    [search,unit,email,type].forEach(function(el){ if(!el) return; el.addEventListener('input', filter); el.addEventListener('change', filter); });
    root.addEventListener('change', function(ev){ if(ev.target.matches('[data-rec2-staff],[data-rec2-manager]')) summary(); });
    if(form){
      form.addEventListener('submit', function(){
        // Hidden mirror fields make saving robust even if browser/JS/CSS changes checkbox state handling.
        Array.prototype.slice.call(form.querySelectorAll('[data-rec2-mirror]')).forEach(function(x){ x.remove(); });
        cards.forEach(function(card){
          var id=card.getAttribute('data-user-id'), c=checks(card);
          if(c.staff && c.staff.checked){ var h=document.createElement('input'); h.type='hidden'; h.name='staff_user_ids'; h.value=id; h.setAttribute('data-rec2-mirror','1'); form.appendChild(h); }
          if(c.manager && c.manager.checked){ var h2=document.createElement('input'); h2.type='hidden'; h2.name='manager_user_ids'; h2.value=id; h2.setAttribute('data-rec2-mirror','1'); form.appendChild(h2); }
        });
        summary();
      });
    }
    filter();
  });
})();
