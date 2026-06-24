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
      if(!input){ input=document.createElement('input'); input.type='hidden'; input.name='csrf_token'; form.appendChild(input); }
      if(!input.value) input.value=token;
    });
  }
  function refreshToken(){
    return fetch('/pwa/csrf-refresh',{credentials:'same-origin',headers:{'Accept':'application/json'}})
      .then(function(r){ return r.ok ? r.json() : null; })
      .then(function(data){
        var token = data && (data.csrf_token || data.token || data.csrf);
        if(token){ setMetaToken(token); syncForms(token); }
        return token || '';
      }).catch(function(){ return ''; });
  }
  document.addEventListener('DOMContentLoaded', function(){ syncForms(); refreshToken(); });
  document.addEventListener('submit', function(event){
    var form=event.target;
    if(!form || !form.matches || !form.matches('form')) return;
    if((form.getAttribute('method')||'').toLowerCase() !== 'post') return;
    syncForms();
  }, true);
  window.addEventListener('pageshow', function(){ refreshToken(); });
})();
