(function(){
  function text(el){ return (el?.value || '').trim(); }
  function typeLabel(value){
    return ({text:'Metin',single_choice:'Tek seçim',multiple_choice:'Çoklu seçim',rating_5:'1-5 puan',rating_10:'1-10 puan',yes_no:'Evet / Hayır'})[value] || 'Metin';
  }
  function defaultOptions(type){
    if (type === 'yes_no') return 'Evet\nHayır';
    if (type === 'single_choice') return 'Seçenek 1\nSeçenek 2\nSeçenek 3';
    if (type === 'multiple_choice') return 'Seçenek 1\nSeçenek 2\nSeçenek 3';
    return '';
  }
  function initStudio(){
    const studio = document.querySelector('[data-survey-studio="1"]');
    if (!studio) return;
    const questionBlock = document.getElementById('questionBlock');
    const addBtn = document.getElementById('addQuestionBtn');
    const titleInput = document.getElementById('title');
    const descriptionInput = document.getElementById('description');
    const surveyType = document.getElementById('survey_type');
    const status = document.getElementById('status');
    const targetType = document.getElementById('target_type');
    const previewMount = document.getElementById('builderPreviewMount');
    const outlineMount = document.getElementById('builderQuestionOutlineMount');
    const quickButtons = Array.from(document.querySelectorAll('[data-quick-question-type]'));
    if (!questionBlock || !previewMount || !outlineMount) return;

    function cards(){ return Array.from(questionBlock.querySelectorAll('.question-card')); }
    function activeCard(){ return questionBlock.querySelector('.question-card.is-active') || cards()[0] || null; }
    function setActive(card){
      cards().forEach((item) => item.classList.toggle('is-active', item === card));
      renderOutline();
    }
    function syncCardMeta(card, index){
      card.dataset.questionIndex = String(index + 1);
      const number = card.querySelector('.question-no');
      if (number) number.innerHTML = `<i class="fa-solid fa-circle-dot"></i> Soru ${index + 1}`;
    }
    function renderPreview(){
      const list = cards().map((card, index) => {
        const label = text(card.querySelector('textarea[name="question_text[]"]')) || `Soru ${index + 1}`;
        const type = card.querySelector('select[name="question_type[]"]')?.value || 'text';
        const required = card.querySelector('select[name="question_required[]"]')?.value === '1';
        return {index, label, type, required};
      });
      const previewRows = list.length ? list.slice(0, 5).map((item) => `
        <div class="phase1-preview-row">
          <b>${item.index + 1}</b>
          <div>
            <strong>${escapeHtml(item.label)}</strong>
            <span>${item.required ? 'Zorunlu alan' : 'İsteğe bağlı alan'} · ${typeLabel(item.type)}</span>
          </div>
          <span class="phase1-tag">${typeLabel(item.type)}</span>
        </div>`).join('') : '<div class="phase1-results-note">Henüz soru eklenmedi. Sol panelden bir bileşen seçebilir veya “Soru Ekle” düğmesini kullanabilirsiniz.</div>';
      const surveyTypeLabel = surveyType?.selectedOptions?.[0]?.textContent?.trim() || 'Kurum İçi';
      const statusLabel = status?.selectedOptions?.[0]?.textContent?.trim() || 'Taslak';
      const targetLabel = targetType?.selectedOptions?.[0]?.textContent?.trim() || 'Tüm personel';
      previewMount.innerHTML = `
        <div class="phase1-preview-card">
          <div class="phase1-preview-hero">
            <div class="phase1-preview-kicker"><i class="fa-solid fa-eye"></i> Canlı bakış</div>
            <h3 class="phase1-preview-title">${escapeHtml(text(titleInput) || 'Yeni anket başlığı')}</h3>
            <p class="phase1-preview-text">${escapeHtml(text(descriptionInput) || 'Açıklama alanı boşsa burada kısa bir özet görünür.')}</p>
          </div>
          <div class="phase1-preview-meta">
            <div class="item"><span class="label">Anket türü</span><span class="value">${escapeHtml(surveyTypeLabel)}</span></div>
            <div class="item"><span class="label">Hedefleme</span><span class="value">${escapeHtml(targetLabel)}</span></div>
            <div class="item"><span class="label">Durum</span><span class="value">${escapeHtml(statusLabel)}</span></div>
          </div>
          <div class="phase1-preview-list">${previewRows}</div>
        </div>`;
    }
    function renderOutline(){
      const current = activeCard();
      const list = cards();
      outlineMount.innerHTML = `
        <div class="phase1-outline-card">
          <div>
            <h3 class="section-title" style="margin-bottom:6px;">Soru akış haritası</h3>
            <p class="section-sub" style="margin:0;">Tuvaldeki soru sırasını ve tür dağılımını izleyin.</p>
          </div>
          ${list.length ? list.map((card, index) => {
            const label = text(card.querySelector('textarea[name="question_text[]"]')) || `Soru ${index + 1}`;
            const type = card.querySelector('select[name="question_type[]"]')?.value || 'text';
            const required = card.querySelector('select[name="question_required[]"]')?.value === '1';
            const active = current === card ? 'is-active' : '';
            return `<a href="#" class="phase1-outline-item ${active}" data-outline-index="${index}">
              <span class="num">${index + 1}</span>
              <div><strong>${escapeHtml(label)}</strong><span>${required ? 'Zorunlu' : 'İsteğe bağlı'} · ${typeLabel(type)}</span></div>
              <span class="phase1-tag">${typeLabel(type)}</span>
            </a>`;
          }).join('') : '<div class="phase1-results-note">Soru listesi burada oluşur.</div>'}
        </div>`;
      Array.from(outlineMount.querySelectorAll('[data-outline-index]')).forEach((link) => {
        link.addEventListener('click', (event) => {
          event.preventDefault();
          const index = Number(link.getAttribute('data-outline-index') || '-1');
          const target = cards()[index];
          if (!target) return;
          setActive(target);
          target.scrollIntoView({behavior:'smooth', block:'center'});
          const focusField = target.querySelector('textarea, input, select');
          if (focusField) focusField.focus({preventScroll:true});
        });
      });
    }
    function syncAll(){
      cards().forEach(syncCardMeta);
      if (!activeCard() && cards()[0]) setActive(cards()[0]);
      renderPreview();
      renderOutline();
    }
    function applyType(card, type, label){
      const select = card.querySelector('select[name="question_type[]"]');
      const textArea = card.querySelector('textarea[name="question_text[]"]');
      const optionsArea = card.querySelector('textarea[name="question_options[]"]');
      if (select) {
        select.value = type;
        select.dispatchEvent(new Event('change', {bubbles:true}));
      }
      if (textArea && !text(textArea)) textArea.value = `${label || typeLabel(type)}?`;
      if (optionsArea && !text(optionsArea) && ['single_choice','multiple_choice','yes_no'].includes(type)) optionsArea.value = defaultOptions(type);
      [textArea, optionsArea, select].forEach((el) => el && el.dispatchEvent(new Event('input', {bubbles:true})));
      setActive(card);
      syncAll();
    }
    function addQuestion(type, label){
      if (!addBtn || addBtn.disabled) return;
      const before = cards().length;
      addBtn.click();
      window.setTimeout(() => {
        const list = cards();
        const card = list[list.length - 1];
        if (!card || list.length < before) return;
        applyType(card, type, label);
        card.scrollIntoView({behavior:'smooth', block:'center'});
      }, 10);
    }
    quickButtons.forEach((button) => {
      button.addEventListener('click', () => addQuestion(button.dataset.quickQuestionType, button.dataset.quickLabel));
    });
    questionBlock.addEventListener('focusin', (event) => {
      const card = event.target.closest('.question-card');
      if (card) setActive(card);
    });
    questionBlock.addEventListener('click', (event) => {
      const card = event.target.closest('.question-card');
      if (card) setActive(card);
    });
    questionBlock.addEventListener('input', syncAll);
    questionBlock.addEventListener('change', syncAll);
    [titleInput, descriptionInput, surveyType, status, targetType].forEach((el) => el && el.addEventListener('input', syncAll));
    [surveyType, status, targetType].forEach((el) => el && el.addEventListener('change', syncAll));
    const observer = new MutationObserver(syncAll);
    observer.observe(questionBlock, {childList:true, subtree:false});
    syncAll();
  }
  function escapeHtml(value){
    return String(value || '').replace(/[&<>"']/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initStudio);
  } else {
    initStudio();
  }
})();
