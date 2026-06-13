// BYS360_CIC_V4_6B_CELEBRATIONS_TEMPLATE_FINAL_FIX
(function(){
  "use strict";
  var page="/dashboard/kurumsal-bilgilendirme/kutlamalar";
  function norm(h){try{return new URL(h||location.href,location.origin).pathname.replace(/\/+$/,"")||"/";}catch(e){return String(h||"").replace(/\/+$/,"")||"/";}}
  function apply(){
    if(norm(location.href)!==page)return;
    document.body.classList.add("bys360-cic-v46-celebrations");
    document.querySelectorAll('a[href*="/dashboard/kurumsal-bilgilendirme"]').forEach(function(a){
      var href=norm(a.getAttribute('href'));
      ['active','is-active','current','selected','router-link-active','text-primary','link-primary','btn-link'].forEach(function(c){a.classList.remove(c);});
      a.removeAttribute('aria-current');
      if(href===page){a.classList.add('active');a.setAttribute('aria-current','page');}
    });
    var file=document.querySelector('.cic-celeb-file');
    if(file&&!file.dataset.v46bBound){file.dataset.v46bBound='1';file.addEventListener('change',function(){var name=(file.files&&file.files[0])?file.files[0].name:'Dosya seçilmedi';var label=document.querySelector('[data-cic-v46-file-name]');if(label)label.textContent=name;});}
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',apply);else apply();
  setTimeout(apply,250);setTimeout(apply,900);
})();
