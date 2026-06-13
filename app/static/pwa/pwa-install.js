// BYS360_PWA_B73_INSTALL_SCRIPT
(function () {
  function isStandalone() {
    return window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;
  }

  document.documentElement.classList.add('bys360-pwa-ready');
  if (isStandalone()) {
    document.documentElement.classList.add('bys360-pwa-standalone');
  }

  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function () {
      var secureEnough = window.location.protocol === 'https:' || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
      if (!secureEnough) return;
      navigator.serviceWorker.register('/service-worker.js', { scope: '/' }).catch(function (err) {
        console.warn('BYS360 PWA servis işçisi kaydı yapılamadı:', err);
      });
    });
  }
})();
