// BYS360_MOBILE_NATIVE_SHELL_V2_JS
// Tek hamburger, çalışan mobil drawer, native/PWA sınıfları ve stray markup temizliği.
(function(){
  'use strict';

  var doc = document;
  var root = doc.documentElement;
  var body = doc.body;
  if(!body) return;

  var BREAKPOINT = 1100;
  var ua = navigator.userAgent || '';
  var isNativeUA = /BYS360Mobile\/|BYS360NativeApp\//.test(ua);
  var isCapacitor = !!(window.Capacitor && (window.Capacitor.isNativePlatform ? window.Capacitor.isNativePlatform() : true));

  function isMobile(){ return window.innerWidth <= BREAKPOINT; }
  function closest(el, selector){ try { return el && el.closest ? el.closest(selector) : null; } catch(e){ return null; } }
  function sidebar(){ return doc.getElementById('appSidebar') || doc.querySelector('.app-sidebar'); }
  function overlay(){ return doc.getElementById('mobileOverlay') || doc.querySelector('.mobile-overlay') || doc.querySelector('.bys360-mobile-menu-backdrop'); }
  function toggles(){ return Array.prototype.slice.call(doc.querySelectorAll('#menuToggle,.menu-toggle,[data-bys360-mobile-menu-toggle="true"]')); }

  function markShell(){
    root.classList.add('bys360-mobile-native-shell-v2');
    body.classList.add('bys360-mobile-native-shell-v2');
    if(isNativeUA || isCapacitor){
      root.classList.add('bys360-native-app');
      body.classList.add('bys360-native-app');
      body.classList.add('bys360-native-real-app');
    }
    if(isMobile()) body.classList.add('bys360-mobile-viewport');
    else body.classList.remove('bys360-mobile-viewport');
  }

  function removeDuplicateHamburgers(){
    var primary = doc.getElementById('menuToggle') || doc.querySelector('.menu-toggle');
    if(primary){
      primary.setAttribute('data-bys360-primary-menu-toggle','true');
      primary.setAttribute('aria-controls','appSidebar');
      primary.setAttribute('aria-expanded', body.classList.contains('bys360-mobile-menu-open') ? 'true' : 'false');
      toggles().forEach(function(btn){
        if(btn !== primary && btn.classList.contains('bys360-mobile-menu-toggle')){
          btn.setAttribute('data-bys360-duplicate-hidden','true');
          try { btn.remove(); } catch(e) { btn.style.display = 'none'; }
        }
      });
    }
  }

  function ensureOverlay(){
    var ov = overlay();
    if(ov) return ov;
    ov = doc.createElement('button');
    ov.type = 'button';
    ov.id = 'mobileOverlay';
    ov.className = 'mobile-overlay';
    ov.setAttribute('aria-label','Menüyü kapat');
    body.appendChild(ov);
    return ov;
  }

  function setExpanded(value){
    toggles().forEach(function(btn){ btn.setAttribute('aria-expanded', value ? 'true' : 'false'); btn.classList.toggle('is-active', !!value); });
  }

  function openMenu(){
    var side = sidebar();
    if(!side) return;
    ensureOverlay();
    body.classList.add('bys360-mobile-menu-open');
    body.classList.remove('sidebar-collapsed');
    side.classList.add('mobile-open');
    setExpanded(true);
  }

  function closeMenu(){
    var side = sidebar();
    body.classList.remove('bys360-mobile-menu-open');
    if(side) side.classList.remove('mobile-open');
    setExpanded(false);
  }

  function toggleMenu(){
    if(body.classList.contains('bys360-mobile-menu-open')) closeMenu();
    else openMenu();
  }

  function bindMenu(){
    removeDuplicateHamburgers();
    ensureOverlay();

    doc.addEventListener('click', function(event){
      var btn = closest(event.target, '#menuToggle,.menu-toggle,[data-bys360-mobile-menu-toggle="true"]');
      if(btn && isMobile()){
        event.preventDefault();
        event.stopPropagation();
        if(event.stopImmediatePropagation) event.stopImmediatePropagation();
        toggleMenu();
        return false;
      }
      var ov = closest(event.target, '#mobileOverlay,.mobile-overlay,.bys360-mobile-menu-backdrop');
      if(ov && isMobile()){
        event.preventDefault();
        closeMenu();
      }
    }, true);

    var side = sidebar();
    if(side){
      side.addEventListener('click', function(event){
        var link = closest(event.target, 'a[href]');
        if(link && isMobile()) window.setTimeout(closeMenu, 80);
      }, true);
    }

    doc.addEventListener('keydown', function(event){
      if(event.key === 'Escape') closeMenu();
    });
  }

  function cleanStrayMarkup(){
    var walker;
    try {
      walker = doc.createTreeWalker(body, NodeFilter.SHOW_TEXT, null);
    } catch(e){ return; }
    var doomed = [];
    var node;
    while((node = walker.nextNode())){
      var t = (node.nodeValue || '').replace(/\s+/g,' ').trim();
      if(t === 'dy>' || t === 'body>' || t === '/body>' || t === '</body>' || t === '</html>'){
        doomed.push(node);
      }
    }
    doomed.forEach(function(n){
      try { n.parentNode && n.parentNode.removeChild(n); } catch(e){}
    });
  }

  function apply(){
    markShell();
    removeDuplicateHamburgers();
    cleanStrayMarkup();
    if(!isMobile()) closeMenu();
  }

  bindMenu();
  apply();
  doc.addEventListener('DOMContentLoaded', apply);
  window.addEventListener('resize', function(){ window.clearTimeout(window.__bys360NativeShellV2Resize); window.__bys360NativeShellV2Resize = window.setTimeout(apply, 120); }, {passive:true});

  if('MutationObserver' in window){
    var timer = null;
    new MutationObserver(function(records){
      if(!records.some(function(r){ return r.addedNodes && r.addedNodes.length; })) return;
      window.clearTimeout(timer);
      timer = window.setTimeout(apply, 100);
    }).observe(body, {childList:true, subtree:true});
  }
})();
