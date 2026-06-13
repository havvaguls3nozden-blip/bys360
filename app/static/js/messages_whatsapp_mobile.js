(function(){
  function isPhone(){ return window.matchMedia('(max-width: 767.98px)').matches; }

  function enhanceInbox(){
    const shell = document.getElementById('messageShell');
    if (!shell) return;
    document.body.classList.add('wa-mobile-chat-active');

    
    if (!isPhone()) return;

    const hasActiveThread = !!document.querySelector('.wa-thread-item.active');
    const mobileKey = 'bys360-message-mobile-mode';
    if (!sessionStorage.getItem('bys360-message-phone-init')){
      sessionStorage.setItem('bys360-message-phone-init', '1');
      try { localStorage.setItem(mobileKey, hasActiveThread ? 'mobile-thread' : 'mobile-list'); } catch (err) {}
    }

    const search = document.getElementById('threadSearch');
    if (search) search.setAttribute('placeholder', 'Konuşmalarda ara');

    const items = Array.from(document.querySelectorAll('.wa-thread-item'));
    items.forEach(function(item){
      if (item.dataset.waPhoneBound) return;
      item.dataset.waPhoneBound = '1';
      item.addEventListener('click', function(){
        try { localStorage.setItem(mobileKey, 'mobile-thread'); } catch (err) {}
      });
    });
  }

  function enhanceThread(){
    const shell = document.querySelector('.chat-shell');
    if (!shell) return;
    document.body.classList.add('wa-mobile-chat-active');
    if (!isPhone()) return;

    const box = document.getElementById('chatMessages') || document.querySelector('.chat-messages');
    if (box) {
      setTimeout(function(){ box.scrollTop = box.scrollHeight; }, 50);
    }

    const textarea = document.querySelector('.chat-compose textarea, #messageBody, textarea.chat-textarea');
    if (textarea && !textarea.dataset.waPhoneBound){
      textarea.dataset.waPhoneBound = '1';
      textarea.setAttribute('placeholder', 'Mesaj yaz');
      textarea.addEventListener('focus', function(){
        setTimeout(function(){
          try { textarea.scrollIntoView({block:'center', behavior:'smooth'}); } catch(err){}
        }, 120);
      });
    }
  }

  function enhanceCompose(){
    const form = document.getElementById('newMessageForm');
    if (!form) return;
    document.body.classList.add('wa-mobile-chat-active');
    if (!isPhone()) return;

    const body = form.querySelector('textarea[name="body"]');
    if (body) body.setAttribute('placeholder', 'Mesajınızı yazın');

    const selfBtn = document.getElementById('selectSelfNoteBtn');
    if (selfBtn) selfBtn.classList.add('is-phone-primary');
  }

  document.addEventListener('DOMContentLoaded', function(){
    enhanceInbox();
    enhanceThread();
    enhanceCompose();
  });
})();
