(function () {
  'use strict';

  var MOBILE_LIMIT = 768;
  var ROOT_CLASS = 'bys360-mobile-assistant-v5-root';
  var HIDDEN_CLASS = 'bys360-mobile-assistant-v5-hidden';

  function isMobile() {
    return window.matchMedia && window.matchMedia('(max-width: ' + MOBILE_LIMIT + 'px)').matches;
  }

  function textOf(el) {
    return (el && el.textContent ? el.textContent : '').replace(/\s+/g, ' ').trim();
  }

  function idClassOf(el) {
    return ((el.id || '') + ' ' + (el.className || '')).toString().toLowerCase();
  }

  function looksAssistant(el) {
    if (!el || el === document.body || el === document.documentElement) return false;
    var sig = idClassOf(el);
    var text = textOf(el).toLowerCase();
    if (el.hasAttribute('data-bys360-assistant') || el.hasAttribute('data-assistant-widget')) return true;
    if (sig.indexOf('bys360') !== -1 && sig.indexOf('assistant') !== -1) return true;
    if (sig.indexOf('assistant') !== -1 && (sig.indexOf('widget') !== -1 || sig.indexOf('panel') !== -1 || sig.indexOf('launcher') !== -1 || sig.indexOf('fab') !== -1)) return true;
    if (sig.indexOf('ai-agent') !== -1 || sig.indexOf('ai_agent') !== -1) return true;
    if (text.indexOf('bys360 asistan') !== -1 || text.indexOf('bys360 asistanı') !== -1) return true;
    return false;
  }

  function rootFor(el) {
    if (!el) return null;
    var preferred = el.closest('[data-bys360-assistant-root], [data-bys360-assistant], [data-assistant-widget], .bys360-assistant-widget, .bys360-assistant-panel, .bys360-assistant-shell, .bys360-ai-agent-widget, .bys360-ai-agent-panel, .ai-agent-widget, .ai-agent-panel, .assistant-widget, .assistant-panel, .assistant-launcher, .assistant-fab');
    if (preferred && preferred !== document.body && preferred !== document.documentElement) return preferred;

    var node = el;
    var lastGood = el;
    for (var i = 0; i < 4 && node && node.parentElement; i += 1) {
      if (node.parentElement === document.body || node.parentElement === document.documentElement) break;
      if (looksAssistant(node.parentElement)) lastGood = node.parentElement;
      node = node.parentElement;
    }
    return lastGood;
  }

  function uniqueRoots(nodes) {
    var roots = [];
    nodes.forEach(function (el) {
      var root = rootFor(el);
      if (!root || root === document.body || root === document.documentElement) return;
      if (roots.some(function (r) { return r === root || r.contains(root); })) return;
      roots = roots.filter(function (r) { return !root.contains(r); });
      roots.push(root);
    });
    return roots;
  }

  function scoreRoot(root) {
    var score = 0;
    var sig = idClassOf(root);
    var text = textOf(root).toLowerCase();
    var rect = root.getBoundingClientRect ? root.getBoundingClientRect() : { width: 0, height: 0, top: 0 };

    if (sig.indexOf('bys360') !== -1) score += 30;
    if (sig.indexOf('assistant') !== -1 || sig.indexOf('ai-agent') !== -1) score += 30;
    if (text.indexOf('bys360 asistan') !== -1 || text.indexOf('bys360 asistanı') !== -1) score += 25;
    if (root.querySelector('input, textarea, button, a')) score += 10;
    if (rect.width > 40 && rect.height > 40) score += 5;
    if (rect.top < 110) score -= 20; // Üste yapışan kopyayı tercih etme.
    if (root.classList.contains(ROOT_CLASS)) score += 100;
    return score;
  }

  function collectCandidates() {
    var selector = [
      '[id*="assistant" i]', '[class*="assistant" i]',
      '[id*="ai-agent" i]', '[class*="ai-agent" i]',
      '[id*="ai_agent" i]', '[class*="ai_agent" i]',
      '[data-bys360-assistant]', '[data-assistant-widget]', '[data-bys360-assistant-root]'
    ].join(',');

    var nodes = Array.prototype.slice.call(document.querySelectorAll(selector));

    // Metninde BYS360 Asistanı geçen sabit/panel benzeri alanları da yakala.
    Array.prototype.slice.call(document.querySelectorAll('body *')).forEach(function (el) {
      if (nodes.indexOf(el) !== -1) return;
      var t = textOf(el).toLowerCase();
      if ((t.indexOf('bys360 asistan') !== -1 || t.indexOf('bys360 asistanı') !== -1) && el.children.length < 12) {
        nodes.push(el);
      }
    });

    return uniqueRoots(nodes).filter(looksAssistant);
  }

  function applyFix() {
    if (!isMobile()) return;
    document.body.classList.add('bys360-mobile-assistant-v5-ready');

    var roots = collectCandidates();
    if (!roots.length) return;

    roots.sort(function (a, b) { return scoreRoot(b) - scoreRoot(a); });
    var keep = roots[0];

    roots.forEach(function (root) {
      if (root === keep) return;
      root.classList.add(HIDDEN_CLASS);
      root.setAttribute('aria-hidden', 'true');
      root.setAttribute('data-bys360-assistant-v5-duplicate', 'true');
    });

    keep.classList.remove(HIDDEN_CLASS);
    keep.removeAttribute('aria-hidden');
    keep.classList.add(ROOT_CLASS);
    keep.setAttribute('data-bys360-assistant-v5-primary', 'true');

    // Üste sabitlenmiş inline stilleri temizle.
    try {
      keep.style.top = 'auto';
      keep.style.left = 'auto';
      keep.style.right = '16px';
      keep.style.bottom = 'max(18px, env(safe-area-inset-bottom))';
      keep.style.position = 'fixed';
      keep.style.zIndex = '2147483000';
    } catch (err) {}
  }

  function scheduleFix() {
    applyFix();
    setTimeout(applyFix, 250);
    setTimeout(applyFix, 900);
    setTimeout(applyFix, 1800);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', scheduleFix);
  } else {
    scheduleFix();
  }

  window.addEventListener('resize', scheduleFix);
  window.addEventListener('orientationchange', scheduleFix);

  if ('MutationObserver' in window) {
    var obs = new MutationObserver(function () {
      clearTimeout(window.__bys360AssistantV5Timer);
      window.__bys360AssistantV5Timer = setTimeout(applyFix, 120);
    });
    if (document.documentElement) {
      obs.observe(document.documentElement, { childList: true, subtree: true });
    }
  }
})();
