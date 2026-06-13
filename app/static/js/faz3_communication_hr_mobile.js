(function(){
  const mq = window.matchMedia('(max-width: 767.98px)');

  function buildCardsForTableWrap(wrap){
    if (!wrap || wrap.dataset.mobileCardsBuilt === 'true') return;
    const table = wrap.querySelector('table');
    if (!table) return;
    const headers = Array.from(table.querySelectorAll('thead th')).map(th => (th.textContent || '').trim());
    const bodyRows = Array.from(table.querySelectorAll('tbody tr'));
    const cardHost = document.createElement('div');
    cardHost.className = 'mobile-table-cards';

    let builtAny = false;
    bodyRows.forEach((row) => {
      const cells = Array.from(row.children || []);
      if (!cells.length) return;
      if (cells.length === 1 && /bulunamadı|henüz/i.test((cells[0].textContent || '').trim())) {
        const empty = document.createElement('div');
        empty.className = 'mobile-data-empty';
        empty.textContent = (cells[0].textContent || '').trim();
        cardHost.appendChild(empty);
        return;
      }
      const card = document.createElement('article');
      card.className = 'mobile-data-card';

      const title = document.createElement('h4');
      title.className = 'mobile-data-card__title';
      title.textContent = (cells[0].innerText || cells[0].textContent || 'Kayıt').trim();
      card.appendChild(title);

      const grid = document.createElement('div');
      grid.className = 'mobile-data-card__grid';
      cells.forEach((cell, index) => {
        const label = headers[index] || `Alan ${index + 1}`;
        const rowEl = document.createElement('div');
        rowEl.className = 'mobile-data-row';
        const labelEl = document.createElement('div');
        labelEl.className = 'mobile-data-label';
        labelEl.textContent = label;
        const valueEl = document.createElement('div');
        valueEl.className = 'mobile-data-value';
        valueEl.innerHTML = cell.innerHTML;
        rowEl.appendChild(labelEl);
        rowEl.appendChild(valueEl);
        grid.appendChild(rowEl);
      });
      card.appendChild(grid);
      cardHost.appendChild(card);
      builtAny = true;
    });

    if (!builtAny && !cardHost.children.length) {
      const empty = document.createElement('div');
      empty.className = 'mobile-data-empty';
      empty.textContent = 'Kayıt bulunamadı.';
      cardHost.appendChild(empty);
    }

    wrap.insertAdjacentElement('afterend', cardHost);
    wrap.dataset.mobileCardsBuilt = 'true';
  }

  function initLeaveMobileCards(){
    if (!mq.matches) return;
    document.querySelectorAll('.page-grid .table-wrap').forEach(buildCardsForTableWrap);
  }

  function improveNotificationToolbar(){
    const searchInput = document.querySelector('.notification-toolbar input[type="search"], .notification-toolbar input[type="text"]');
    if (searchInput && mq.matches) searchInput.setAttribute('placeholder', 'Bildirim ara');
  }

  function pinComposeTitle(){
    const composer = document.querySelector('#newMessageForm .message-actions');
    if (!composer || !mq.matches) return;
    composer.dataset.mobileEnhanced = 'true';
  }

  document.addEventListener('DOMContentLoaded', function(){
    initLeaveMobileCards();
    improveNotificationToolbar();
    pinComposeTitle();
  });
})();
