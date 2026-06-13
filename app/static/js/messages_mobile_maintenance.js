(function(){
  function isPhone(){
    return window.matchMedia('(max-width: 767.98px)').matches;
  }

  function bindInboxLinks(){
    if (!isPhone()) return;
    document.querySelectorAll('.wa-thread-item[href]').forEach(function(link){
      if (link.dataset.hotfixBound === '1') return;
      link.dataset.hotfixBound = '1';
      link.style.touchAction = 'pan-y';
      link.addEventListener('click', function(){
        try { localStorage.setItem('bys360-message-mobile-mode', 'mobile-thread'); } catch (err) {}
      });
    });
  }

  function bindComposeButtons(){
    document.querySelectorAll('#openComposePickerBtn[href], #openComposePickerFab[href], #waPhoneComposeBtn[href]').forEach(function(link){
      if (link.dataset.hotfixBound === '1') return;
      link.dataset.hotfixBound = '1';
      link.addEventListener('click', function(event){
        var href = link.getAttribute('href');
        if (href) {
          event.preventDefault();
          window.location.href = href;
        }
      });
    });
  }

  function focusTextareas(){
    if (!isPhone()) return;
    var area = document.getElementById('threadMessageBody') || document.querySelector('#newMessageForm textarea[name="body"]') || document.getElementById('messageComposeBox');
    if (area) {
      area.removeAttribute('readonly');
      area.disabled = false;
      area.style.pointerEvents = 'auto';
      area.style.touchAction = 'manipulation';
    }
  }

  function setStatus(form, message, isError){
    var statusEl = form.querySelector('#messageDraftState, .chat-compose-status, [data-message-status]');
    if (!statusEl) return;
    statusEl.textContent = message || '';
    statusEl.style.color = isError ? '#991b1b' : '';
  }

  function disableButton(btn, loading){
    if (!btn) return;
    if (!btn.dataset.originalHtml) btn.dataset.originalHtml = btn.innerHTML;
    btn.disabled = !!loading;
    btn.style.opacity = loading ? '0.84' : '';
    if (loading) {
      btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
    } else {
      btn.innerHTML = btn.dataset.originalHtml || btn.innerHTML;
    }
  }

  function bindSafeSubmit(formSelector, buttonSelector){
    var form = document.querySelector(formSelector);
    if (!form || form.dataset.safeSubmitBound === '1') return;
    form.dataset.safeSubmitBound = '1';

    var sendUrl = form.getAttribute('data-send-url') || form.getAttribute('action') || '';
    if (sendUrl) form.setAttribute('action', sendUrl);

    var btn = document.querySelector(buttonSelector);
    var textArea = form.querySelector('#messageComposeBox, #threadMessageBody, textarea[name="body"]');
    var fileInput = form.querySelector('input[type="file"][name="attachments"], input[type="file"][name="attachment"], input[type="file"]');

    form.addEventListener('submit', function(event){
      var bodyValue = textArea ? (textArea.value || '').trim() : '';
      var hasAttachment = !!(fileInput && fileInput.files && fileInput.files.length);

      if (!(bodyValue || hasAttachment)) {
        event.preventDefault();
        if (textArea) textArea.focus();
        setStatus(form, 'Boş mesaj gönderilemez.', true);
        return false;
      }

      if (form.dataset.sending === '1') {
        event.preventDefault();
        return false;
      }

      form.dataset.sending = '1';
      disableButton(btn, true);
      setStatus(form, 'Mesaj gönderiliyor...', false);
    });
  }

  document.addEventListener('DOMContentLoaded', function(){
    bindInboxLinks();
    bindComposeButtons();
    focusTextareas();
    bindSafeSubmit('#messageComposeForm', '#messageSendBtn');
    bindSafeSubmit('#threadMessageForm', '#threadMessageForm .chat-send');
  });
})();
