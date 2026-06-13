(function(){
  function ready(fn){if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',fn);else fn();}
  function text(el){return (el&&el.textContent||'').toLocaleLowerCase('tr-TR');}
  ready(function(){
    document.querySelectorAll('body *').forEach(function(el){
      if(el.children&&el.children.length)return;
      var t=el.textContent||'';
      var n=t.replace(/Pilot önce/g,'Aktif / Pasif').replace(/pilot önce/g,'Aktif / Pasif')
        .replace(/Pilot test yap/g,'Önizleme / test gönderimi').replace(/pilot test yap/g,'Önizleme / test gönderimi')
        .replace(/Pilot test/g,'Test gönderimi').replace(/pilot test/g,'test gönderimi')
        .replace(/Kuru çalışma/g,'Ön kontrol').replace(/kuru çalışma/g,'ön kontrol');
      if(n!==t)el.textContent=n;
    });
    var href='/dashboard/kurumsal-bilgilendirme/kutlamalar';
    if(document.querySelector('a[href="'+href+'"]'))return;
    var candidates=Array.from(document.querySelectorAll('a')).filter(function(a){
      return (a.getAttribute('href')||'').indexOf('/dashboard/kurumsal-bilgilendirme')>=0||text(a).indexOf('kurumsal bilgilendirme')>=0;
    });
    if(!candidates.length)return;
    var parent=candidates[0];
    var link=document.createElement('a');
    link.href=href;
    link.className='cic-sidebar-celebrations-link'+(location.pathname===href?' is-active':'');
    link.innerHTML='<i class="fa-solid fa-cake-candles"></i><span>Kutlamalar</span>';
    parent.insertAdjacentElement('afterend',link);
  });
})();
