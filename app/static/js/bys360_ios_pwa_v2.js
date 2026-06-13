/* BYS360 iOS PWA V2 Advanced Mobile App */
(function(){
  'use strict';
  var ua = navigator.userAgent || '';
  var isIOS = /iPad|iPhone|iPod/.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  var isStandalone = window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;
  var root = document.documentElement;
  root.classList.toggle('bys360-ios-browser', isIOS && !isStandalone);
  root.classList.toggle('bys360-ios-pwa', isIOS && isStandalone);
  root.classList.toggle('bys360-pwa-standalone', isStandalone);

  function registerServiceWorker(){
    if (!('serviceWorker' in navigator)) return;
    window.addEventListener('load', function(){
      navigator.serviceWorker.register('/service-worker.js', { scope: '/' }).then(function(reg){
        if (reg && reg.update) { setTimeout(function(){ try { reg.update(); } catch(e){} }, 1500); }
      }).catch(function(){});
    });
  }

  function showIOSInstallHint(){
    if (!isIOS || isStandalone) return;
    try {
      if (sessionStorage.getItem('bys360_ios_pwa_hint_closed') === '1') return;
    } catch(e) {}
    if (document.getElementById('bys360PwaInstallHint')) return;
    var hint = document.createElement('div');
    hint.id = 'bys360PwaInstallHint';
    hint.className = 'bys360-pwa-install-hint';
    hint.setAttribute('role', 'status');
    hint.innerHTML = '<button type="button" class="bys360-pwa-install-close" aria-label="Kapat">×</button><p class="bys360-pwa-install-title">BYS360\u2019ı ana ekrana ekleyin</p><p class="bys360-pwa-install-text">Paylaş simgesine dokunun ve <strong>Ana Ekrana Ekle</strong> seçeneğiyle BYS360\u2019ı uygulama gibi açın.</p>';
    document.body.appendChild(hint);
    var close = hint.querySelector('button');
    close.addEventListener('click', function(){
      hint.classList.remove('is-visible');
      try { sessionStorage.setItem('bys360_ios_pwa_hint_closed', '1'); } catch(e) {}
    });
    setTimeout(function(){ hint.classList.add('is-visible'); }, 900);
  }

  function protectExternalLinksInStandalone(){
    if (!isStandalone) return;
    document.addEventListener('click', function(ev){
      var a = ev.target && ev.target.closest ? ev.target.closest('a[href]') : null;
      if (!a) return;
      var href = a.getAttribute('href') || '';
      if (/^https?:\/\//i.test(href) && a.hostname !== window.location.hostname) {
        a.setAttribute('target','_blank');
        a.setAttribute('rel','noopener noreferrer');
      }
    }, true);
  }

  registerServiceWorker();
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function(){ showIOSInstallHint(); protectExternalLinksInStandalone(); });
  } else {
    showIOSInstallHint(); protectExternalLinksInStandalone();
  }
})();
