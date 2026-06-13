(function () {
  'use strict';

  function repair() {
    try {
      document.documentElement.style.overflowY = 'auto';
      document.body.style.overflowY = 'auto';
      document.body.style.visibility = 'visible';
      document.body.style.opacity = '1';
      document.body.classList.remove('bys360-mobile-assistant-v5-ready');

      document.querySelectorAll('.bys360-mobile-assistant-v5-hidden').forEach(function (el) {
        el.classList.remove('bys360-mobile-assistant-v5-hidden');
        el.removeAttribute('aria-hidden');
        el.removeAttribute('data-bys360-assistant-v5-duplicate');
      });

      document.querySelectorAll('.bys360-mobile-tabbar, .bys360-mobile-bottom-nav, .bys360-mobile-native-tabbar, [data-bys360-mobile-tabbar="true"]').forEach(function (el) {
        el.style.display = 'none';
      });
    } catch (e) {}
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', repair);
  } else {
    repair();
  }
  setTimeout(repair, 250);
  setTimeout(repair, 900);
})();
