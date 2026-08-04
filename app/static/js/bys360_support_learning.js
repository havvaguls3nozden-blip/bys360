(function(){
  function copyArticleLink(){
    var btn=document.querySelector('[data-copy-support-link]');
    if(!btn) return;
    btn.addEventListener('click', function(){
      var url=window.location.href;
      if(navigator.clipboard){
        navigator.clipboard.writeText(url).then(function(){btn.innerHTML='<i class="fa-solid fa-check"></i> Bağlantı Kopyalandı';});
      }
    });
  }
  function smoothAnchors(){
    document.querySelectorAll('[data-support-anchor]').forEach(function(link){
      link.addEventListener('click',function(e){
        var target=document.querySelector(link.getAttribute('href'));
        if(target){e.preventDefault();target.scrollIntoView({behavior:'smooth',block:'start'});}
      });
    });
  }
  function bindArticlePrint(){
    var btn=document.getElementById('helpArticlePrintBtn');
    if(!btn) return;
    btn.addEventListener('click', function(){
      window.print();
    });
  }
  document.addEventListener('DOMContentLoaded', function(){copyArticleLink(); smoothAnchors(); bindArticlePrint();});
})();
