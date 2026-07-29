
(function(){
  function isMobile(){ return window.matchMedia('(max-width: 767.98px)').matches; }

  function cleanText(value){ return String(value || '').replace(/\s+/g, ' ').trim(); }

  function buildCardsForTable(table){
    if(!table) return;
    const wrapper = table.closest('.table-wrap') || table.parentElement;
    if(!wrapper) return;
    wrapper.classList.add('has-faz4-mobile-cards');

    let mount = wrapper.nextElementSibling;
    if(!(mount && mount.classList.contains('faz4-mobile-table-cards'))){
      mount = document.createElement('div');
      mount.className = 'faz4-mobile-table-cards';
      wrapper.insertAdjacentElement('afterend', mount);
    }

    const headers = Array.from(table.querySelectorAll('thead th')).map(th => cleanText(th.textContent));
    const rows = Array.from(table.querySelectorAll('tbody tr')).filter(tr => {
      const hidden = tr.hidden || tr.classList.contains('row-hidden') || window.getComputedStyle(tr).display === 'none';
      return !hidden;
    });

    mount.innerHTML = '';
    rows.forEach((tr) => {
      const cells = Array.from(tr.children);
      if(!cells.length) return;
      const card = document.createElement('article');
      card.className = 'faz4-mobile-record-card';

      const head = document.createElement('div');
      head.className = 'faz4-mobile-record-card__head';

      let titleHtml = cells[0].innerHTML;
      let titleText = cleanText(cells[0].textContent);
      let selectSource = null;
      if(cells[1] && titleText.length < 3){
        selectSource = cells[0].querySelector('input[type="checkbox"]');
        titleHtml = cells[1].innerHTML;
        titleText = cleanText(cells[1].textContent);
      }
      if(selectSource){
        const selectLabel = document.createElement('label');
        selectLabel.className = 'faz4-mobile-record-card__select';
        const mirror = document.createElement('input');
        mirror.type = 'checkbox';
        mirror.checked = selectSource.checked;
        mirror.setAttribute('aria-label', selectSource.getAttribute('aria-label') || 'Kaydı seç');
        mirror.addEventListener('change', function(){
          selectSource.checked = mirror.checked;
          selectSource.dispatchEvent(new Event('change', {bubbles:true}));
        });
        selectLabel.appendChild(mirror);
        const selectText = document.createElement('span');
        selectText.textContent = 'Seç';
        selectLabel.appendChild(selectText);
        head.appendChild(selectLabel);
      }
      const title = document.createElement('div');
      title.className = 'faz4-mobile-record-card__title';
      title.innerHTML = titleHtml;
      head.appendChild(title);

      const meta = document.createElement('div');
      meta.className = 'faz4-mobile-record-card__meta';
      const metaBits = [];
      if(cells[2]) metaBits.push(cleanText(cells[2].textContent));
      if(cells[3]) metaBits.push(cleanText(cells[3].textContent));
      meta.textContent = metaBits.filter(Boolean).join(' • ');
      if(meta.textContent) head.appendChild(meta);
      card.appendChild(head);

      const body = document.createElement('div');
      body.className = 'faz4-mobile-record-card__body';
      cells.forEach((cell, idx) => {
        if(idx === 0 && cells[1] && cleanText(cells[0].textContent).length < 3) return;
        if(idx === 1 && titleHtml === cells[1].innerHTML) return;
        const labelText = headers[idx] || ('Alan ' + (idx + 1));
        if(!labelText) return;
        const field = document.createElement('div');
        field.className = 'faz4-mobile-field';
        const label = document.createElement('div');
        label.className = 'faz4-mobile-field__label';
        label.textContent = labelText;
        const value = document.createElement('div');
        value.className = 'faz4-mobile-field__value';
        value.innerHTML = cell.innerHTML;
        field.appendChild(label);
        field.appendChild(value);
        body.appendChild(field);
      });
      card.appendChild(body);
      mount.appendChild(card);
    });
  }

  function refreshResponsiveTables(){
    document.querySelectorAll('.ticket-table, .survey-manage-shell .table-wrap table').forEach((table) => {
      if(isMobile()) {
        buildCardsForTable(table);
      }
    });
  }

  function bindObservers(){
    document.querySelectorAll('.ticket-table tbody, #surveyManageTableBody').forEach((tbody) => {
      if(!tbody || tbody.dataset.faz4Observed === '1') return;
      const obs = new MutationObserver(() => { if(isMobile()) refreshResponsiveTables(); });
      obs.observe(tbody, {childList:true, subtree:true, attributes:true, attributeFilter:['class','style','hidden']});
      tbody.dataset.faz4Observed = '1';
    });
  }

  function bindQuestionJump(){
    const btn = document.getElementById('jumpFirstMissingBtn');
    const form = document.getElementById('surveyTakeForm');
    if(!btn || !form) return;
    btn.addEventListener('click', function(){
      const invalid = form.querySelector(':invalid');
      if(invalid){ invalid.scrollIntoView({behavior:'smooth', block:'center'}); invalid.focus({preventScroll:true}); return; }
      const firstRequired = form.querySelector('.question-card[data-required="1"] textarea:placeholder-shown, .question-card[data-required="1"] input[required]:not(:checked)');
      if(firstRequired){ firstRequired.scrollIntoView({behavior:'smooth', block:'center'}); }
    });
  }

  function boot(){
    refreshResponsiveTables();
    bindObservers();
    bindQuestionJump();
  }

  document.addEventListener('DOMContentLoaded', boot);
  window.addEventListener('resize', function(){ if(isMobile()) refreshResponsiveTables(); });
})();
