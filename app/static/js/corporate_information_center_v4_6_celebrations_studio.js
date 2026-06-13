// BYS360_CIC_V4_6_CELEBRATIONS_STUDIO_PRO_UI
(function(){
  "use strict";
  var ROOT="/dashboard/kurumsal-bilgilendirme";
  var PAGE=ROOT+"/kutlamalar";
  function pathOf(x){try{return new URL(x||location.href,location.origin).pathname.replace(/\/+$/,"")||"/";}catch(e){return String(x||"").replace(/\/+$/,"")||"/";}}
  function apply(){
    var current=pathOf(location.href);
    if(current.indexOf(ROOT)!==0)return;
    if(current.indexOf(PAGE)===0)document.body.classList.add("bys360-cic-v46-celebrations");
    document.querySelectorAll('a[href*="/dashboard/kurumsal-bilgilendirme"]').forEach(function(a){
      var href=pathOf(a.getAttribute('href'));
      var active=false;
      if(current===ROOT) active=(href===ROOT);
      else if(current.indexOf(PAGE)===0) active=(href===PAGE);
      else active=(href!==ROOT && href!==PAGE && (current===href || current.indexOf(href+"/")===0));
      ['active','is-active','current','selected','router-link-active'].forEach(function(c){a.classList.remove(c);});
      a.removeAttribute('aria-current');
      if(active){a.classList.add('active');a.setAttribute('aria-current','page');}
      if(current.indexOf(PAGE)===0 && (a.textContent||'').trim()==='Kutlamalar'){
        a.classList.remove('text-primary','link-primary','btn-link');
      }
    });
    document.querySelectorAll('.cic-celeb-studio a,.cic-celeb-studio button').forEach(function(el){el.classList.remove('text-primary','link-primary','btn-link');});
    document.querySelectorAll('.cic-celeb-studio,.cicp-content').forEach(function(scope){
      scope.querySelectorAll('*').forEach(function(el){
        var t=(el.textContent||'').trim();
        if(t==='kuru çalışma'||t==='Kuru çalışma') el.textContent='Ön kontrol';
        if(t==='test yap'||t==='Pilot test yap') el.textContent='Önizleme / test gönderimi';
      });
    });
    var file=document.querySelector('.cic-celeb-file');
    if(file&&!file.dataset.v46Bound){file.dataset.v46Bound='1';file.addEventListener('change',function(){var name=(file.files&&file.files[0])?file.files[0].name:'Dosya seçilmedi';var label=document.querySelector('[data-cic-v46-file-name]');if(label)label.textContent=name;});}
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',apply);else apply();
  setTimeout(apply,250);setTimeout(apply,900);setTimeout(apply,1800);
})();
