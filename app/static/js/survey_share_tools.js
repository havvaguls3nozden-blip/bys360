(function(){
  if (window.__bysSurveyShareInitialized) return;
  window.__bysSurveyShareInitialized = true;

  function byId(id){ return document.getElementById(id); }
  function enc(v){ return encodeURIComponent(String(v || '')); }
  function safeText(v, fallback){
    const value = String(v || '').trim();
    return value || String(fallback || '').trim();
  }
  async function copyText(value){
    const text = String(value || '');
    if (!text) return false;
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
        return true;
      }
    } catch (err) {}
    try {
      const area = document.createElement('textarea');
      area.value = text;
      area.setAttribute('readonly', 'readonly');
      area.style.position = 'fixed';
      area.style.opacity = '0';
      area.style.pointerEvents = 'none';
      document.body.appendChild(area);
      area.focus();
      area.select();
      area.setSelectionRange(0, area.value.length);
      const ok = document.execCommand('copy');
      area.remove();
      return !!ok;
    } catch (err) {
      return false;
    }
  }
  function buildState(title, url){
    const safeTitle = safeText(title, 'Anket');
    const safeUrl = safeText(url, window.location.href);
    const subject = safeTitle + ' anket bağlantısı';
    const bodyText = safeTitle + ' anketine aşağıdaki bağlantıdan erişebilirsiniz:\n' + safeUrl;
    return {
      title: safeTitle,
      url: safeUrl,
      subject: subject,
      body: bodyText,
      mailto: 'mailto:?subject=' + enc(subject) + '&body=' + enc(bodyText),
      whatsapp: 'https://wa.me/?text=' + enc(safeTitle + ' anket bağlantısı: ' + safeUrl)
    };
  }
  function showToast(message, tone){
    if (!document.body) return;
    let box = byId('surveyShareToast');
    if (!box){
      box = document.createElement('div');
      box.id = 'surveyShareToast';
      box.style.position = 'fixed';
      box.style.right = '20px';
      box.style.bottom = '20px';
      box.style.zIndex = '5000';
      box.style.padding = '12px 14px';
      box.style.borderRadius = '14px';
      box.style.fontWeight = '800';
      box.style.fontSize = '.88rem';
      box.style.boxShadow = '0 14px 34px rgba(15,23,42,.16)';
      document.body.appendChild(box);
    }
    box.style.background = tone === 'error' ? '#7f1d1d' : '#111827';
    box.style.color = '#fff';
    box.textContent = safeText(message, 'İşlem tamamlandı.');
    box.hidden = false;
    clearTimeout(box._timer);
    box._timer = setTimeout(function(){ box.hidden = true; }, 2200);
  }

  const modal = byId('surveyShareModal');
  const titleEl = byId('surveyShareTitle');
  const input = byId('surveyShareUrl');
  const copyBtn = byId('surveyShareCopyBtn');
  const mailBtn = byId('surveyShareMailBtn');
  const waBtn = byId('surveyShareWhatsappBtn');
  const nativeBtn = byId('surveyShareNativeBtn');
  let currentState = null;

  function applyState(next){
    currentState = next;
    if (titleEl) titleEl.textContent = next.title || 'Anket paylaşımı';
    if (input) input.value = next.url || '';
    if (mailBtn) mailBtn.href = next.mailto || '#';
    if (waBtn) waBtn.href = next.whatsapp || '#';
    if (nativeBtn) nativeBtn.hidden = !(navigator.share && next.url);
  }
  function openModal(next){
    applyState(next);
    if (!modal) return false;
    modal.hidden = false;
    document.body.classList.add('survey-share-open');
    return true;
  }
  function closeModal(){
    if (!modal) return;
    modal.hidden = true;
    document.body.classList.remove('survey-share-open');
  }
  async function fallbackShare(next){
    if (navigator.share) {
      try {
        await navigator.share({ title: next.title, text: next.title + ' anket bağlantısı', url: next.url });
        return true;
      } catch (err) {}
    }
    const ok = await copyText(next.url);
    showToast(ok ? 'Bağlantı kopyalandı.' : 'Bağlantı kopyalanamadı.', ok ? 'ok' : 'error');
    return ok;
  }

  document.addEventListener('click', async function(event){
    const trigger = event.target.closest('[data-share-survey]');
    if (trigger){
      event.preventDefault();
      const state = buildState(trigger.getAttribute('data-share-title'), trigger.getAttribute('data-share-url'));
      if (!openModal(state)) {
        await fallbackShare(state);
      }
      return;
    }

    if (event.target.closest('[data-share-close]')){
      event.preventDefault();
      closeModal();
      return;
    }

    if (copyBtn && event.target.closest('#surveyShareCopyBtn')){
      event.preventDefault();
      if (!currentState) return;
      const ok = await copyText(currentState.url);
      showToast(ok ? 'Bağlantı kopyalandı.' : 'Bağlantı kopyalanamadı.', ok ? 'ok' : 'error');
      return;
    }

    if (nativeBtn && event.target.closest('#surveyShareNativeBtn')){
      event.preventDefault();
      if (!currentState) return;
      await fallbackShare(currentState);
    }
  }, true);

  if (mailBtn){
    mailBtn.addEventListener('click', function(event){
      if (!currentState) return;
      mailBtn.href = currentState.mailto;
    });
  }
  if (waBtn){
    waBtn.addEventListener('click', function(event){
      if (!currentState) return;
      waBtn.href = currentState.whatsapp;
    });
  }

  if (modal){
    modal.addEventListener('click', function(event){
      if (event.target === modal) closeModal();
    });
    document.addEventListener('keydown', function(event){
      if (event.key === 'Escape' && !modal.hidden) closeModal();
    });
  }

  window.BYSSurveyShare = {
    open: function(title, url){
      const next = buildState(title, url);
      if (!openModal(next)) return fallbackShare(next);
      return true;
    },
    close: closeModal,
    copy: function(url){ return copyText(url); }
  };
})();
