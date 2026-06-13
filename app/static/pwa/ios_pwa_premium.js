// BYS360 iOS PWA V3.5 stable mobile shell - install prompt disabled
(function () {
  'use strict';

  if (window.__BYS360_IOS_PWA_V35_STABLE__) return;
  window.__BYS360_IOS_PWA_V35_STABLE__ = true;

  var ua = window.navigator.userAgent || '';
  var isIOS = /iPad|iPhone|iPod/.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  var isStandalone = window.navigator.standalone === true || window.matchMedia('(display-mode: standalone)').matches;

  function setVh() {
    document.documentElement.style.setProperty('--bys-vh', (window.innerHeight * 0.01) + 'px');
  }

  function hideInstallPrompts() {
    var selectors = [
      '.bys-ios-install-card',
      '#bys360-ios-install-final-v34',
      '#bys360-ios-pwa-install',
      '#bys360-ios-install',
      '.ios-install-prompt',
      '.pwa-install-prompt',
      '.install-prompt',
      '.a2hs-prompt',
      '.add-to-home-screen',
      '.add-to-homescreen',
      '.home-screen-prompt',
      '.homescreen-prompt',
      '[data-bys360-ios-install-card]',
      '[data-bys360-ios-install-old]',
      '[data-ios-install]',
      '[data-pwa-install]'
    ];

    selectors.forEach(function (selector) {
      document.querySelectorAll(selector).forEach(function (el) {
        try {
          el.style.setProperty('display', 'none', 'important');
          el.style.setProperty('visibility', 'hidden', 'important');
          el.style.setProperty('opacity', '0', 'important');
          el.style.setProperty('height', '0', 'important');
          el.style.setProperty('min-height', '0', 'important');
          el.style.setProperty('max-height', '0', 'important');
          el.style.setProperty('overflow', 'hidden', 'important');
          el.setAttribute('aria-hidden', 'true');
        } catch (e) {}
      });
    });
  }

  function init() {
    setVh();
    window.addEventListener('resize', setVh, { passive: true });
    window.addEventListener('orientationchange', function () { setTimeout(setVh, 250); }, { passive: true });

    if (isIOS) {
      document.documentElement.classList.add(isStandalone ? 'bys-ios-pwa' : 'bys-ios-browser');
    }

    hideInstallPrompts();
    window.setTimeout(hideInstallPrompts, 300);
    window.setTimeout(hideInstallPrompts, 1200);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
