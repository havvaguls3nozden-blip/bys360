// BYS360_MOBILE_EMERGENCY_VISIBLE_V8
// Beyaz ekran, loader takılması, ikinci hamburger ve eski mobil alt bar kalıntılarını güvenli şekilde temizler.
(function(){
  'use strict';
  function ready(fn){
    if(document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fn, {once:true});
    else fn();
  }
  function clearLoader(){
    document.body && document.body.classList.add('bys360-v8-loader-cleared');
    var loader=document.getElementById('pageLoader');
    if(loader){
      loader.classList.add('hidden');
      loader.style.display='none';
      loader.style.pointerEvents='none';
    }
  }
  function dedupeMenuToggle(){
    var toggles=Array.prototype.slice.call(document.querySelectorAll('#menuToggle, .mobile-menu-toggle, .bys360-mobile-menu-toggle, [data-bys360-extra-menu-toggle]'));
    var keep=document.getElementById('menuToggle') || toggles[0];
    toggles.forEach(function(btn){
      if(btn !== keep){
        btn.setAttribute('aria-hidden','true');
        btn.style.display='none';
      }
    });
  }
  function removeBadMobileBars(){
    var selectors=[
      '.bys360-mobile-bottom-nav', '.mobile-bottom-nav', '.bys-mobile-bottom-nav',
      '[data-bys360-mobile-bottom-nav]', '[data-mobile-native-tabbar]', '[data-bys360-native-tabbar]'
    ];
    selectors.forEach(function(sel){
      document.querySelectorAll(sel).forEach(function(node){ node.remove(); });
    });
  }
  function ensureMobileDrawer(){
    var sidebar=document.getElementById('appSidebar');
    var toggle=document.getElementById('menuToggle');
    var overlay=document.getElementById('mobileOverlay');
    if(!sidebar || !toggle) return;
    var mq=window.matchMedia ? window.matchMedia('(max-width:1100px)') : {matches:false};
    function setOpen(open){
      if(!mq.matches) return;
      sidebar.classList.toggle('mobile-open', !!open);
      document.body.classList.toggle('sidebar-mobile-open', !!open);
      if(overlay) overlay.classList.toggle('show', !!open);
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    }
    if(!toggle.dataset.bys360V8Bound){
      toggle.dataset.bys360V8Bound='1';
      toggle.addEventListener('click', function(e){
        if(!mq.matches) return;
        e.preventDefault();
        e.stopPropagation();
        setOpen(!sidebar.classList.contains('mobile-open'));
      }, true);
    }
    if(overlay && !overlay.dataset.bys360V8Bound){
      overlay.dataset.bys360V8Bound='1';
      overlay.addEventListener('click', function(){ setOpen(false); });
    }
    sidebar.querySelectorAll('a.nav-link-bys[href]').forEach(function(a){
      if(a.dataset.bys360V8CloseBound) return;
      a.dataset.bys360V8CloseBound='1';
      a.addEventListener('click', function(){ if(mq.matches) setOpen(false); });
    });
  }
  function unlockScroll(){
    if(!document.body) return;
    document.documentElement.style.overflowY='auto';
    document.documentElement.style.height='auto';
    document.body.style.overflowY='auto';
    document.body.style.height='auto';
    document.body.style.position='relative';
  }
  ready(function(){
    clearLoader();
    dedupeMenuToggle();
    removeBadMobileBars();
    ensureMobileDrawer();
    unlockScroll();
    setTimeout(clearLoader, 350);
    setTimeout(clearLoader, 1200);
  });
  window.addEventListener('pageshow', function(){ clearLoader(); unlockScroll(); });
})();
