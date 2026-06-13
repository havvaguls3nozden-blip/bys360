/* BYS360_IOS_ASISTAN_RESPONSIVE_FIX_V1
   iPhone Safari/PWA: asistan açılma, safe-area, eski sürükleme konumu ve panel açık sınıf düzeltmesi. */
(function () {
  'use strict';

  var ROOT_ID = 'bys360-assistant-module-root';
  var STORAGE_POS = 'bys360AssistantModulePosition';
  var STORAGE_OPEN = 'bys360AssistantModuleOpen';

  function isIOS() {
    return /iPad|iPhone|iPod/.test(navigator.userAgent || '') ||
      ((navigator.platform || '') === 'MacIntel' && navigator.maxTouchPoints > 1);
  }

  function isSmall() {
    return window.matchMedia && window.matchMedia('(max-width: 768px)').matches;
  }

  function root() { return document.getElementById(ROOT_ID); }
  function qs(sel, base) { return (base || document).querySelector(sel); }

  function markOpenState(r) {
    if (!r) return;
    var panel = qs('.bys360-am-panel', r);
    var open = !!(panel && !panel.hidden);
    r.classList.toggle('is-open', open);
    r.setAttribute('data-bys360-assistant-panel-open', open ? 'true' : 'false');
    document.documentElement.classList.toggle('bys360-ios-assistant-open', open);
    document.body.classList.toggle('bys360-ios-assistant-open', open);
  }

  function resetMobilePosition(r) {
    if (!r || !isIOS() || !isSmall()) return;
    try { localStorage.removeItem(STORAGE_POS); } catch (e) {}
    r.style.left = 'auto';
    r.style.top = 'auto';
    r.style.right = 'max(12px, env(safe-area-inset-right))';
    r.style.bottom = 'max(14px, env(safe-area-inset-bottom))';
    r.style.position = 'fixed';
    r.style.zIndex = '2147483400';
  }

  function openAssistant(r) {
    if (!r) return;
    resetMobilePosition(r);
    if (window.BYS360AssistantModule && typeof window.BYS360AssistantModule.open === 'function') {
      try { window.BYS360AssistantModule.open(); } catch (e) {}
    } else {
      var panel = qs('.bys360-am-panel', r);
      var launcher = qs('.bys360-am-launcher', r);
      if (panel) panel.hidden = false;
      if (launcher) launcher.setAttribute('aria-expanded', 'true');
      try { localStorage.setItem(STORAGE_OPEN, '1'); } catch (e) {}
    }
    markOpenState(r);
  }

  function installTouchFallback() {
    if (!isIOS()) return;
    var r = root();
    if (!r || r.getAttribute('data-bys360-ios-assistant-fix-v1') === '1') return;
    r.setAttribute('data-bys360-ios-assistant-fix-v1', '1');
    resetMobilePosition(r);
    markOpenState(r);

    r.addEventListener('touchend', function (event) {
      var target = event.target;
      if (!target || !target.closest) return;
      var launcher = target.closest('.bys360-am-launcher');
      if (!launcher) return;
      event.preventDefault();
      event.stopPropagation();
      openAssistant(r);
    }, { capture: true, passive: false });

    r.addEventListener('click', function (event) {
      var target = event.target;
      if (!target || !target.closest) return;
      var launcher = target.closest('.bys360-am-launcher');
      if (!launcher) return;
      resetMobilePosition(r);
      setTimeout(function () { markOpenState(r); }, 0);
    }, true);

    var observer = new MutationObserver(function () { markOpenState(r); });
    var panel = qs('.bys360-am-panel', r);
    if (panel) observer.observe(panel, { attributes: true, attributeFilter: ['hidden'] });
  }

  function schedule() {
    installTouchFallback();
    setTimeout(installTouchFallback, 250);
    setTimeout(installTouchFallback, 900);
    setTimeout(installTouchFallback, 1800);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', schedule);
  else schedule();
  window.addEventListener('pageshow', schedule);
  window.addEventListener('resize', function () { var r = root(); resetMobilePosition(r); markOpenState(r); });
  window.addEventListener('orientationchange', function () { setTimeout(schedule, 250); });
})();
