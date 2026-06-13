/* BYS360_LIVE_FULL_OVERLAY_V2_17_60 */
(function(){
  'use strict';
  function metaToken(){
    var meta=document.querySelector('meta[name="csrf-token"],meta[name="csrf_token"]');
    return meta && meta.getAttribute('content') ? meta.getAttribute('content') : '';
  }
  function setMetaToken(token){
    if(!token) return;
    var meta=document.querySelector('meta[name="csrf-token"]');
    if(!meta){ meta=document.createElement('meta'); meta.setAttribute('name','csrf-token'); document.head.appendChild(meta); }
    meta.setAttribute('content', token);
  }
  function syncForms(token){
    token = token || metaToken();
    if(!token) return;
    document.querySelectorAll('form').forEach(function(form){
      var method=(form.getAttribute('method')||'').toLowerCase();
      if(method !== 'post') return;
      var input=form.querySelector('input[name="csrf_token"]');
      if(!input){ input=document.createElement('input'); input.type='hidden'; input.name='csrf_token'; form.prepend(input); }
      if(!input.value) input.value=token;
    });
  }
  function refresh(){
    if(!window.fetch) { syncForms(); return Promise.resolve(); }
    return fetch('/pwa/csrf-refresh', {headers:{'X-Requested-With':'XMLHttpRequest'}, cache:'no-store', credentials:'same-origin'})
      .then(function(res){ return res.ok ? res.json() : null; })
      .then(function(data){ if(data && data.csrf_token){ setMetaToken(data.csrf_token); syncForms(data.csrf_token); } else { syncForms(); } })
      .catch(function(){ syncForms(); });
  }
  document.addEventListener('DOMContentLoaded', function(){ refresh(); });
  window.addEventListener('pageshow', function(){ refresh(); });
  document.addEventListener('submit', function(event){
    var form=event.target;
    if(!form || !form.matches || !form.matches('form')) return;
    if((form.getAttribute('method')||'').toLowerCase() !== 'post') return;
    syncForms();
  }, true);
  window.bys360RefreshCsrf = refresh;
})();
