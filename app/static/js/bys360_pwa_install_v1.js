/* BYS360_MOBILE_PWA_FAZ2_V1_JS
   Ana ekrana ekle deneyimi, service worker kaydı ve güvenli PWA davranışı.
*/
(function(){
  'use strict';
  var doc = document;
  var body = doc.body;
  if(!body) return;

  var MARK = 'bys360-mobile-pwa-faz2-v1';
  var STORAGE_DISMISS = 'bys360_pwa_install_dismissed_v1';
  var deferredPrompt = null;
  var isStandalone = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;
  var isIOS = /iphone|ipad|ipod/i.test(window.navigator.userAgent || '');
  var isSecure = window.isSecureContext || location.hostname === 'localhost' || location.hostname === '127.0.0.1';

  doc.documentElement.classList.add(MARK);
  body.classList.add(MARK);
  if(isStandalone) body.classList.add('bys360-pwa-standalone');

  function mobileLike(){ return window.innerWidth <= 900 || /android|iphone|ipad|ipod/i.test(window.navigator.userAgent || ''); }
  function dismissed(){ return localStorage.getItem(STORAGE_DISMISS) === '1'; }
  function dismiss(){ try{ localStorage.setItem(STORAGE_DISMISS, '1'); }catch(e){} hidePrompt(); }

  function hidePrompt(){
    var el = doc.querySelector('[data-bys360-pwa-install="true"]');
    if(el) el.remove();
  }

  function createPrompt(mode){
    if(isStandalone || dismissed() || !mobileLike()) return;
    if(doc.querySelector('[data-bys360-pwa-install="true"]')) return;

    var box = doc.createElement('aside');
    box.className = 'bys360-pwa-install-card';
    box.setAttribute('data-bys360-pwa-install', 'true');
    box.setAttribute('role', 'dialog');
    box.setAttribute('aria-label', 'BYS360 ana ekrana ekle');

    var title = mode === 'ios' ? 'BYS360’ı ana ekrana ekleyebilirsiniz' : 'BYS360’ı uygulama gibi kullanın';
    var text = mode === 'ios'
      ? 'iPhone/iPad için Paylaş menüsünden “Ana Ekrana Ekle” seçeneğini kullanabilirsiniz.'
      : 'Telefonunuzda daha hızlı erişim için BYS360’ı ana ekrana ekleyebilirsiniz.';
    var primary = mode === 'ios' ? '' : '<button type="button" class="bys360-pwa-install-primary" data-bys360-pwa-action="install">Ana ekrana ekle</button>';

    box.innerHTML = ''+
      '<div class="bys360-pwa-install-mark" aria-hidden="true">BYS</div>'+
      '<div class="bys360-pwa-install-copy">'+
        '<strong>'+title+'</strong>'+
        '<span>'+text+'</span>'+
      '</div>'+
      '<div class="bys360-pwa-install-actions">'+
        primary+
        '<button type="button" class="bys360-pwa-install-secondary" data-bys360-pwa-action="dismiss">Sonra</button>'+
      '</div>';

    box.addEventListener('click', function(ev){
      var action = ev.target && ev.target.getAttribute('data-bys360-pwa-action');
      if(action === 'dismiss') dismiss();
      if(action === 'install') triggerInstall();
    });
    body.appendChild(box);
  }

  function triggerInstall(){
    if(!deferredPrompt) return;
    deferredPrompt.prompt();
    deferredPrompt.userChoice.finally(function(){
      deferredPrompt = null;
      dismiss();
    });
  }

  function registerServiceWorker(){
    if(!('serviceWorker' in navigator)) return;
    if(!isSecure) return;
    window.addEventListener('load', function(){
      navigator.serviceWorker.register('/bys360-sw.js', {scope: '/'})
        .then(function(reg){
          try{ reg.update(); }catch(e){}
          body.classList.add('bys360-pwa-sw-ready');
        })
        .catch(function(){ body.classList.add('bys360-pwa-sw-failed'); });
    });
  }

  window.addEventListener('beforeinstallprompt', function(ev){
    ev.preventDefault();
    deferredPrompt = ev;
    createPrompt('default');
  });

  window.addEventListener('appinstalled', function(){
    try{ localStorage.setItem(STORAGE_DISMISS, '1'); }catch(e){}
    body.classList.add('bys360-pwa-installed');
    hidePrompt();
  });

  registerServiceWorker();

  // iOS'ta beforeinstallprompt yoktur; rahatsız etmeyen kısa bilgilendirme gösterilir.
  window.setTimeout(function(){
    if(isIOS && !isStandalone && !dismissed() && mobileLike()) createPrompt('ios');
  }, 1600);
})();
