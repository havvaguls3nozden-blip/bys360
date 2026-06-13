// BYS360 Mobile Clean Native V4
(function(){
  'use strict';
  var BREAKPOINT = 1100;
  var doc = document;

  function ready(fn){ if(doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', fn); else fn(); }
  function isMobile(){ return window.innerWidth <= BREAKPOINT; }
  function q(sel){ return doc.querySelector(sel); }
  function qa(sel){ return Array.prototype.slice.call(doc.querySelectorAll(sel)); }
  function closest(el, sel){ try { return el && el.closest ? el.closest(sel) : null; } catch(e){ return null; } }
  function body(){ return doc.body; }

  function sidebar(){ return q('#appSidebar') || q('aside.sidebar') || q('.app-sidebar') || q('[data-sidebar]') || q('.sidebar'); }

  function removeBadV3Runtime(){
    ['#bys360MobileTabbarV3','#bys360MobileNativeMenuV3','#bys360MobileNativeMenuV2'].forEach(function(sel){
      qa(sel).forEach(function(el){ try{ el.remove(); } catch(e){ el.style.display='none'; } });
    });
  }

  function removeStrayText(){
    var b = body(); if(!b || !doc.createTreeWalker) return;
    try{
      var walker = doc.createTreeWalker(b, NodeFilter.SHOW_TEXT, null);
      var doomed = [], n;
      while((n = walker.nextNode())){
        var t = (n.nodeValue || '').replace(/\s+/g,' ').trim();
        if(t === 'dy>' || t === '/dy>' || t === 'body>' || t === '/body>' || t === '</body>' || t === '</html>') doomed.push(n);
      }
      doomed.forEach(function(n){ if(n.parentNode) n.parentNode.removeChild(n); });
    }catch(e){}
  }

  function restoreScroll(){
    var b = body(); if(!b) return;
    doc.documentElement.style.overflowY = 'auto';
    doc.documentElement.style.height = 'auto';
    doc.documentElement.style.maxHeight = 'none';
    doc.documentElement.style.position = 'static';
    b.style.overflowY = 'auto';
    b.style.height = 'auto';
    b.style.maxHeight = 'none';
    b.style.position = 'static';
    b.style.touchAction = 'pan-y';
    ['no-scroll','modal-open','drawer-lock','menu-lock','overflow-hidden','bys360-mobile-drawer-open'].forEach(function(cls){ b.classList.remove(cls); });
  }

  function ensureBackdrop(){
    var b = q('#bys360MobileBackdropV4');
    if(!b){
      b = doc.createElement('button');
      b.type = 'button';
      b.id = 'bys360MobileBackdropV4';
      b.setAttribute('aria-label','Menüyü kapat');
      body().appendChild(b);
    }
    b.onclick = function(ev){ ev.preventDefault(); closeMenu(); };
    return b;
  }

  function possibleToggles(){
    return qa('#menuToggle,.menu-toggle,[data-bys360-mobile-menu-toggle="true"],.bys360-mobile-menu-toggle,.bys360-mobile-toggle,button[aria-label="Menüyü aç"],button[aria-label="Menüyü aç veya kapat"]')
      .filter(function(el){ return el && el.id !== 'bys360MobileNativeMenuV3' && el.id !== 'bys360MobileNativeMenuV2'; });
  }

  function ensurePrimaryToggle(){
    removeBadV3Runtime();
    var toggles = possibleToggles();
    var primary = q('#menuToggle') || q('.menu-toggle') || toggles[0];
    if(!primary){
      primary = doc.createElement('button');
      primary.id = 'bys360MobileMenuV4';
      primary.type = 'button';
      primary.setAttribute('aria-label','Menüyü aç');
      primary.innerHTML = '<span aria-hidden="true"></span>';
      body().appendChild(primary);
    }
    primary.setAttribute('data-bys360-v4-primary','true');
    primary.setAttribute('aria-controls','appSidebar');

    possibleToggles().forEach(function(btn){
      if(btn !== primary){
        btn.setAttribute('data-bys360-v4-duplicate','true');
        try { btn.remove(); } catch(e){ btn.style.display='none'; }
      }
    });
    return primary;
  }

  function setOpen(open){
    var b = body(); if(!b) return;
    restoreScroll();
    var side = sidebar();
    b.classList.toggle('bys360-mobile-menu-open', !!open);
    if(side){
      side.classList.toggle('mobile-open', !!open);
      side.setAttribute('aria-hidden', open ? 'false' : 'true');
    }
    var primary = ensurePrimaryToggle();
    primary.setAttribute('aria-expanded', open ? 'true' : 'false');
  }
  function closeMenu(){ setOpen(false); }
  function toggleMenu(){ setOpen(!body().classList.contains('bys360-mobile-menu-open')); }

  var bound = false;
  function bind(){
    if(bound) return; bound = true;
    doc.addEventListener('click', function(ev){
      if(!isMobile()) return;
      var btn = closest(ev.target, '[data-bys360-v4-primary="true"],#menuToggle,.menu-toggle,#bys360MobileMenuV4');
      if(btn){
        ev.preventDefault(); ev.stopPropagation();
        if(ev.stopImmediatePropagation) ev.stopImmediatePropagation();
        toggleMenu();
        return false;
      }
      if(closest(ev.target, '#appSidebar a[href], aside.sidebar a[href], .app-sidebar a[href], .sidebar a[href]')){
        setTimeout(closeMenu, 80);
      }
    }, true);
    doc.addEventListener('keydown', function(ev){ if(ev.key === 'Escape') closeMenu(); });
  }

  function apply(){
    var b = body(); if(!b) return;
    doc.documentElement.classList.add('bys360-mobile-clean-v4');
    b.classList.add('bys360-mobile-clean-v4');
    removeBadV3Runtime(); removeStrayText(); restoreScroll(); ensureBackdrop(); ensurePrimaryToggle();
    if(!isMobile()) closeMenu();
  }

  ready(function(){ bind(); apply(); });
  window.addEventListener('resize', function(){ clearTimeout(window.__bys360MobileV4Resize); window.__bys360MobileV4Resize=setTimeout(apply,120); }, {passive:true});
  if('MutationObserver' in window){ ready(function(){ var t=null; new MutationObserver(function(){ clearTimeout(t); t=setTimeout(apply,80); }).observe(body(), {childList:true, subtree:true}); }); }
})();
