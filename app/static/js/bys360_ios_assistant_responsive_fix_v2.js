/* BYS360_IOS_ASISTAN_RESPONSIVE_FIX_V2
   iPhone Safari/PWA: visualViewport, doğru localStorage anahtarı, panel açık sınıfı ve giriş alanı görünürlüğü. */
(function () {
  'use strict';
  var ROOT_ID = 'bys360-assistant-module-root';
  var LEGACY_ROOT_ID = 'bys360-ai-agent-widget-root';
  var POS_KEYS = ['bys360AssistantModule.position.v1', 'bys360AssistantModulePosition'];
  var OPEN_KEYS = ['bys360AssistantModule.open.v1', 'bys360AssistantModuleOpen'];

  function isIOS() {
    return /iPad|iPhone|iPod/.test(navigator.userAgent || '') ||
      ((navigator.platform || '') === 'MacIntel' && navigator.maxTouchPoints > 1);
  }
  function isSmall() { return !window.matchMedia || window.matchMedia('(max-width: 820px)').matches; }
  function qs(sel, base) { return (base || document).querySelector(sel); }
  function root() { return document.getElementById(ROOT_ID); }
  function legacyRoot() { return document.getElementById(LEGACY_ROOT_ID); }

  function removeStoredPosition() {
    POS_KEYS.forEach(function (key) { try { localStorage.removeItem(key); } catch (e) {} });
  }

  function setVisualViewportVars() {
    if (!isIOS() || !isSmall()) return;
    var vv = window.visualViewport;
    var h = vv && vv.height ? vv.height : window.innerHeight;
    var top = vv && typeof vv.offsetTop === 'number' ? vv.offsetTop : 0;
    document.documentElement.style.setProperty('--bys360-ios-vvh', Math.max(320, Math.round(h)) + 'px');
    document.documentElement.style.setProperty('--bys360-ios-vtop', Math.max(0, Math.round(top)) + 'px');
  }

  function resetRootPosition(r) {
    if (!r || !isIOS() || !isSmall()) return;
    removeStoredPosition();
    r.style.position = 'fixed';
    r.style.left = 'auto';
    r.style.top = 'auto';
    r.style.right = 'max(10px, env(safe-area-inset-right))';
    r.style.bottom = 'max(10px, env(safe-area-inset-bottom))';
    r.style.width = 'auto';
    r.style.height = 'auto';
    r.style.maxWidth = 'calc(100vw - 20px)';
    r.style.transform = 'none';
    r.style.webkitTransform = 'none';
    r.style.zIndex = '2147483600';
  }

  function isPanelOpen(r) {
    if (!r) return false;
    var panel = qs('.bys360-am-panel', r);
    if (panel) return !panel.hidden;
    var legacyPanel = qs('.bys360-ai-agent-panel', r);
    if (legacyPanel) return legacyPanel.getAttribute('data-state') === 'open' || legacyPanel.getAttribute('aria-hidden') === 'false';
    return false;
  }

  function markOpenState() {
    var r = root();
    var lr = legacyRoot();
    var open = isPanelOpen(r) || isPanelOpen(lr);
    [r, lr].forEach(function (node) {
      if (!node) return;
      node.classList.toggle('is-open', open);
      node.setAttribute('data-bys360-ios-assistant-open-v2', open ? 'true' : 'false');
    });
    document.documentElement.classList.toggle('bys360-ios-assistant-open', open);
    document.body.classList.toggle('bys360-ios-assistant-open', open);
    if (open) setTimeout(ensureComposerVisible, 60);
  }

  function openAssistant(r) {
    if (!r) return;
    setVisualViewportVars();
    resetRootPosition(r);
    if (window.BYS360AssistantModule && typeof window.BYS360AssistantModule.open === 'function') {
      try { window.BYS360AssistantModule.open(); } catch (e) {}
    } else {
      var panel = qs('.bys360-am-panel', r);
      var launcher = qs('.bys360-am-launcher', r);
      if (panel) panel.hidden = false;
      if (launcher) launcher.setAttribute('aria-expanded', 'true');
      try { localStorage.setItem(OPEN_KEYS[0], '1'); } catch (e) {}
    }
    setTimeout(markOpenState, 0);
  }

  function ensureComposerVisible() {
    if (!isIOS() || !isSmall()) return;
    var r = root();
    if (!r) return;
    resetRootPosition(r);
    var panel = qs('.bys360-am-panel:not([hidden])', r);
    var form = panel && qs('.bys360-am-form', panel);
    if (!panel || !form) return;
    try { form.scrollIntoView({ block: 'end', inline: 'nearest' }); } catch (e) {}
    var log = qs('.bys360-am-log, [data-chat-log="true"]', panel);
    if (log) { try { log.scrollTop = log.scrollHeight; } catch (e) {} }
  }

  function bindRoot(r) {
    if (!r || r.getAttribute('data-bys360-ios-assistant-fix-v2') === '1') return;
    r.setAttribute('data-bys360-ios-assistant-fix-v2', '1');
    resetRootPosition(r);

    r.addEventListener('touchend', function (event) {
      if (!isIOS() || !isSmall()) return;
      var target = event.target;
      if (!target || !target.closest) return;
      var launcher = target.closest('.bys360-am-launcher');
      if (!launcher) return;
      event.preventDefault();
      event.stopPropagation();
      openAssistant(r);
    }, { capture: true, passive: false });

    r.addEventListener('click', function (event) {
      if (!isIOS() || !isSmall()) return;
      var target = event.target;
      if (!target || !target.closest) return;
      if (target.closest('.bys360-am-launcher')) {
        resetRootPosition(r);
        setTimeout(markOpenState, 0);
        setTimeout(ensureComposerVisible, 120);
      }
      if (target.closest('.bys360-am-close')) setTimeout(markOpenState, 0);
    }, true);

    r.addEventListener('focusin', function (event) {
      if (!isIOS() || !isSmall()) return;
      if (event.target && event.target.matches && event.target.matches('.bys360-am-form textarea, textarea, input')) {
        document.documentElement.classList.add('bys360-ios-assistant-keyboard');
        setVisualViewportVars();
        setTimeout(ensureComposerVisible, 180);
        setTimeout(ensureComposerVisible, 420);
      }
    }, true);

    r.addEventListener('focusout', function () {
      if (!isIOS() || !isSmall()) return;
      setTimeout(function () {
        document.documentElement.classList.remove('bys360-ios-assistant-keyboard');
        setVisualViewportVars();
        markOpenState();
      }, 220);
    }, true);

    var panel = qs('.bys360-am-panel', r);
    if (panel && window.MutationObserver) {
      new MutationObserver(function () { setVisualViewportVars(); markOpenState(); }).observe(panel, { attributes: true, attributeFilter: ['hidden', 'style', 'class'] });
    }
  }

  function bindLegacy(lr) {
    if (!lr || lr.getAttribute('data-bys360-ios-assistant-fix-v2') === '1') return;
    lr.setAttribute('data-bys360-ios-assistant-fix-v2', '1');
    lr.addEventListener('focusin', function () { setVisualViewportVars(); }, true);
    var p = qs('.bys360-ai-agent-panel', lr);
    if (p && window.MutationObserver) new MutationObserver(function(){ setVisualViewportVars(); markOpenState(); }).observe(p, { attributes: true, attributeFilter: ['aria-hidden','data-state','class','style'] });
  }

  function install() {
    if (!isIOS() || !isSmall()) return;
    setVisualViewportVars();
    removeStoredPosition();
    bindRoot(root());
    bindLegacy(legacyRoot());
    markOpenState();
  }

  function schedule() {
    install();
    setTimeout(install, 150);
    setTimeout(install, 700);
    setTimeout(install, 1500);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', schedule, { once: true });
  else schedule();
  window.addEventListener('pageshow', schedule);
  window.addEventListener('resize', function(){ setVisualViewportVars(); install(); ensureComposerVisible(); });
  window.addEventListener('orientationchange', function(){ setTimeout(schedule, 280); });
  if (window.visualViewport) {
    window.visualViewport.addEventListener('resize', function(){ setVisualViewportVars(); setTimeout(ensureComposerVisible, 80); });
    window.visualViewport.addEventListener('scroll', function(){ setVisualViewportVars(); setTimeout(ensureComposerVisible, 80); });
  }
})();
