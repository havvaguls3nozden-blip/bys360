/* BYS360_REAL_MOBILE_APP_V9_JS
   Gerçek Capacitor Android uygulama kabuğu davranışı. */
(function(){
  'use strict';

  function isNativeApp(){
    var ua = String(navigator.userAgent || '');
    return !!(window.Capacitor && window.Capacitor.isNativePlatform) ||
           /BYS360NativeApp|BYS360Mobile|Capacitor/i.test(ua);
  }

  if (!isNativeApp()) { return; }

  var root = document.documentElement;
  root.classList.add('bys360-real-mobile-app');
  if (/Android/i.test(navigator.userAgent || '')) {
    root.classList.add('bys360-android-app');
  }

  function ready(){
    if (document.body) {
      document.body.classList.add('bys360-native-ready');
      document.body.setAttribute('data-bys360-native-app', 'v9');
      dedupeMobileControls();
      forceVisible();
    }
  }

  function forceVisible(){
    try {
      var loaders = document.querySelectorAll('.page-loader, #pageLoader, [data-page-loader]');
      loaders.forEach(function(el){ el.classList.add('hidden'); el.style.pointerEvents = 'none'; });
      document.documentElement.style.overflowY = 'auto';
      document.body.style.overflowY = 'auto';
      document.body.style.minHeight = '100%';
    } catch(e) {}
  }

  function dedupeMobileControls(){
    try {
      var toggles = Array.from(document.querySelectorAll('.sidebar-toggle, #sidebarToggle, .mobile-menu-toggle, .bys360-mobile-menu-toggle, [data-mobile-menu-toggle]'));
      var primary = document.getElementById('sidebarToggle') || document.querySelector('.sidebar-toggle');
      toggles.forEach(function(btn){
        if (primary && btn !== primary) {
          btn.setAttribute('aria-hidden','true');
          btn.style.display = 'none';
        }
      });
      var bottomBars = document.querySelectorAll('.bys360-mobile-bottom-nav,.mobile-bottom-nav,.bys360-bottom-app-nav,[data-mobile-bottom-nav]');
      bottomBars.forEach(function(el){ el.style.display='none'; el.setAttribute('aria-hidden','true'); });
    } catch(e) {}
  }

  function closeAssistantIfOpen(){
    var openPanel = document.querySelector('[data-ai-agent-panel][data-state="open"], .bys360-ai-agent-panel[data-state="open"], .bys360-assistant-panel.is-open, .bys360-assistant-panel.open');
    if (!openPanel) { return false; }
    var close = document.querySelector('[data-ai-agent-close], .bys360-ai-agent-close, .bys360-assistant-close');
    if (close) { close.click(); return true; }
    openPanel.setAttribute('data-state', 'closed');
    openPanel.setAttribute('aria-hidden', 'true');
    return true;
  }

  function closeSidebarIfOpen(){
    var sidebar = document.getElementById('appSidebar') || document.querySelector('.app-sidebar');
    var overlay = document.getElementById('mobileOverlay') || document.querySelector('.mobile-overlay.show');
    if (sidebar && sidebar.classList.contains('mobile-open')) {
      if (overlay) { overlay.click(); }
      else {
        sidebar.classList.remove('mobile-open');
        document.body.classList.remove('sidebar-mobile-open');
      }
      return true;
    }
    return false;
  }

  function bindCapacitor(){
    var cap = window.Capacitor;
    if (!cap || !cap.Plugins) { return; }
    var plugins = cap.Plugins;

    try { if (plugins.SplashScreen && plugins.SplashScreen.hide) { plugins.SplashScreen.hide(); } } catch(e) {}
    try {
      if (plugins.StatusBar) {
        if (plugins.StatusBar.setBackgroundColor) { plugins.StatusBar.setBackgroundColor({ color: '#8B0000' }); }
        if (plugins.StatusBar.setStyle) { plugins.StatusBar.setStyle({ style: 'DARK' }); }
      }
    } catch(e) {}

    try {
      if (plugins.Keyboard && plugins.Keyboard.addListener) {
        plugins.Keyboard.addListener('keyboardWillShow', function(){ root.classList.add('keyboard-open'); });
        plugins.Keyboard.addListener('keyboardDidShow', function(){ root.classList.add('keyboard-open'); });
        plugins.Keyboard.addListener('keyboardWillHide', function(){ root.classList.remove('keyboard-open'); });
        plugins.Keyboard.addListener('keyboardDidHide', function(){ root.classList.remove('keyboard-open'); });
      }
    } catch(e) {}

    try {
      if (plugins.App && plugins.App.addListener) {
        plugins.App.addListener('backButton', function(){
          if (closeAssistantIfOpen()) { return; }
          if (closeSidebarIfOpen()) { return; }
          if (window.history && window.history.length > 1) { window.history.back(); return; }
          if (plugins.App.minimizeApp) { plugins.App.minimizeApp(); }
        });
      }
    } catch(e) {}
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', ready, { once: true });
  } else { ready(); }
  window.addEventListener('load', function(){ ready(); bindCapacitor(); setTimeout(forceVisible, 800); }, { once: true });
  setTimeout(function(){ ready(); bindCapacitor(); }, 1200);
})();
