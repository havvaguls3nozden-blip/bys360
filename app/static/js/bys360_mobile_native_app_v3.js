(function () {
  'use strict';

  function isMobile() {
    return window.matchMedia && window.matchMedia('(max-width: 900px)').matches;
  }

  function qsAny(selectors) {
    for (var i = 0; i < selectors.length; i++) {
      var el = document.querySelector(selectors[i]);
      if (el) return el;
    }
    return null;
  }

  function removeBrokenTailText() {
    try {
      var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null);
      var nodes = [];
      while (walker.nextNode()) nodes.push(walker.currentNode);
      nodes.forEach(function (node) {
        var t = (node.nodeValue || '').trim();
        if (t === 'dy>' || t === '/dy>' || t === 'body>' || t === '</dy>') {
          node.parentNode && node.parentNode.removeChild(node);
        }
      });
    } catch (e) {}
  }

  function restoreScroll() {
    document.documentElement.style.overflowY = 'auto';
    document.documentElement.style.height = 'auto';
    document.body.style.overflowY = 'auto';
    document.body.style.height = 'auto';
    document.body.style.position = 'static';
    document.body.style.touchAction = 'pan-y';
  }

  function findSidebar() {
    return qsAny(['#appSidebar', '.app-sidebar', 'aside.sidebar', '.sidebar', '[data-sidebar]']);
  }

  function ensureBackdrop() {
    var b = document.getElementById('bys360MobileDrawerBackdropV3');
    if (!b) {
      b = document.createElement('div');
      b.id = 'bys360MobileDrawerBackdropV3';
      b.setAttribute('aria-hidden', 'true');
      document.body.appendChild(b);
    }
    return b;
  }

  function setDrawer(open) {
    restoreScroll();
    var sidebar = findSidebar();
    if (!sidebar) return;
    document.body.classList.toggle('bys360-mobile-drawer-open', !!open);
    sidebar.setAttribute('aria-hidden', open ? 'false' : 'true');
  }

  function toggleDrawer() {
    setDrawer(!document.body.classList.contains('bys360-mobile-drawer-open'));
  }

  function ensureMenuButton() {
    var btn = document.getElementById('bys360MobileNativeMenuV3');
    if (!btn) {
      btn = document.createElement('button');
      btn.id = 'bys360MobileNativeMenuV3';
      btn.className = 'bys360-mobile-native-menu-button';
      btn.type = 'button';
      btn.setAttribute('aria-label', 'Menüyü aç veya kapat');
      btn.innerHTML = '<span aria-hidden="true"></span>';
      document.body.appendChild(btn);
    }
    btn.onclick = function (ev) {
      ev.preventDefault();
      ev.stopPropagation();
      toggleDrawer();
    };
    return btn;
  }

  function assistantAction() {
    var selectors = [
      '#bys360AssistantButton',
      '#bys360AssistantToggle',
      '.bys360-assistant-toggle',
      '.bys360-assistant-trigger',
      '.assistant-toggle',
      '.chat-widget-toggle'
    ];
    var target = qsAny(selectors);
    if (target) {
      target.click();
      return;
    }
    window.location.href = '/ai-agent/panel';
  }

  function ensureTabbar() {
    var bar = document.getElementById('bys360MobileTabbarV3');
    if (bar) return bar;

    bar = document.createElement('nav');
    bar.id = 'bys360MobileTabbarV3';
    bar.setAttribute('aria-label', 'BYS360 mobil hızlı menü');

    var path = (window.location.pathname || '').toLowerCase();
    function activeFor(prefixes) {
      return prefixes.some(function (p) { return path.indexOf(p) === 0; }) ? ' is-active' : '';
    }

    bar.innerHTML = [
      '<a class="tab-item' + activeFor(['/home', '/dashboard', '/']) + '" href="/home"><span class="tab-icon">⌂</span><span>Ana</span></a>',
      '<button class="tab-item" type="button" data-bys360-mobile-menu><span class="tab-icon">☰</span><span>Menü</span></button>',
      '<a class="tab-item' + activeFor(['/support']) + '" href="/support"><span class="tab-icon">◌</span><span>Destek</span></a>',
      '<button class="tab-item" type="button" data-bys360-mobile-assistant><span class="tab-icon">✦</span><span>Asistan</span></button>'
    ].join('');

    document.body.appendChild(bar);
    bar.querySelector('[data-bys360-mobile-menu]').addEventListener('click', function (ev) {
      ev.preventDefault();
      toggleDrawer();
    });
    bar.querySelector('[data-bys360-mobile-assistant]').addEventListener('click', function (ev) {
      ev.preventDefault();
      assistantAction();
    });
    return bar;
  }

  function wireSidebarLinks() {
    var sidebar = findSidebar();
    if (!sidebar || sidebar.dataset.bys360MobileV3Wired === '1') return;
    sidebar.dataset.bys360MobileV3Wired = '1';
    sidebar.addEventListener('click', function (ev) {
      var a = ev.target && ev.target.closest ? ev.target.closest('a') : null;
      if (a && a.getAttribute('href') && !a.getAttribute('href').startsWith('#')) {
        setDrawer(false);
      }
    });
  }

  function fixMobileLayout() {
    if (!isMobile()) return;
    document.documentElement.classList.add('bys360-mobile-native-v3-root');
    document.body.classList.add('bys360-mobile-native-v3');
    restoreScroll();
    removeBrokenTailText();
    ensureBackdrop().onclick = function () { setDrawer(false); };
    ensureMenuButton();
    ensureTabbar();
    wireSidebarLinks();

    document.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape') setDrawer(false);
    });

    // Önceki hotfixlerden kalan kilit sınıflarını temizle.
    document.body.classList.remove('no-scroll', 'modal-open', 'drawer-lock', 'menu-lock');
    restoreScroll();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', fixMobileLayout);
  } else {
    fixMobileLayout();
  }
  window.addEventListener('resize', function () {
    if (isMobile()) fixMobileLayout();
    else document.body.classList.remove('bys360-mobile-drawer-open');
  });
})();
