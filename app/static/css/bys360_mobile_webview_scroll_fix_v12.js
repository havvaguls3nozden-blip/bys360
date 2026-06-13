// BYS360 Mobile WebView Scroll Fix V12
// Android WebView içinde kalan scroll kilitlerini güvenli şekilde kaldırır.
(function () {
  function isMobileWidth() {
    return window.matchMedia && window.matchMedia('(max-width: 900px)').matches;
  }

  function unlockScroll() {
    if (!isMobileWidth()) return;
    var html = document.documentElement;
    var body = document.body;
    if (!body) return;

    [html, body].forEach(function (el) {
      el.style.height = 'auto';
      el.style.minHeight = '100%';
      el.style.maxHeight = 'none';
      el.style.overflowX = 'hidden';
      el.style.overflowY = 'auto';
      el.style.webkitOverflowScrolling = 'touch';
      el.style.touchAction = 'pan-y';
    });

    var selectors = [
      '#app', '.app', '.app-shell', '.layout', '.layout-wrapper', '.page-wrapper',
      '.main-wrapper', '.main-content', '.content', '.content-wrapper', '.page-content',
      'main', '.app-main', '.layout-content', '.dashboard-content', '.bys360-content'
    ];

    document.querySelectorAll(selectors.join(',')).forEach(function (el) {
      if (!el.closest('.modal')) {
        el.style.height = 'auto';
        el.style.minHeight = 'auto';
        el.style.maxHeight = 'none';
        el.style.overflow = 'visible';
      }
    });
  }

  document.addEventListener('DOMContentLoaded', unlockScroll);
  window.addEventListener('load', unlockScroll);
  window.addEventListener('resize', unlockScroll);
  window.addEventListener('orientationchange', function () {
    setTimeout(unlockScroll, 250);
  });
  setTimeout(unlockScroll, 500);
  setTimeout(unlockScroll, 1500);
})();
