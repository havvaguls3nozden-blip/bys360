// BYS360_LIVE_FULL_OVERLAY_V2_13_0
(function(){
  "use strict";

  function ready(fn){
    if(document.readyState === "loading") document.addEventListener("DOMContentLoaded", fn);
    else fn();
  }

  function path(){ return (window.location.pathname || "").toLowerCase(); }

  function addBodyClasses(){
    var p = path();
    document.body.classList.add("bys360-live-enhanced");
    if(p.indexOf("/feedback") === 0 || p.indexOf("/geri-bildirim") === 0) document.body.classList.add("bys360-feedback-page");
    if(p.indexOf("/settings") === 0 || p.indexOf("/ayar") === 0 || p.indexOf("role-matrix") >= 0 || p.indexOf("rol") >= 0) document.body.classList.add("bys360-role-matrix-page");
    if(p.indexOf("/portal") === 0) document.body.classList.add("bys360-portal-page");
    if(p.indexOf("/person") === 0 || p.indexOf("/personel") === 0) document.body.classList.add("bys360-personnel-page");
  }

  function firstContent(){
    return document.querySelector("main .container, .main-content, main, .content, .container-fluid, .container, body");
  }

  function panel(id, title, text, pills){
    if(document.getElementById(id)) return null;
    var wrap = document.createElement("section");
    wrap.className = "bys360-live-panel";
    wrap.id = id;
    var h = document.createElement("h2");
    h.textContent = title;
    var p = document.createElement("p");
    p.textContent = text;
    wrap.appendChild(h);
    wrap.appendChild(p);
    if(pills && pills.length){
      var actions = document.createElement("div");
      actions.className = "bys360-live-actions";
      pills.forEach(function(label){
        var s = document.createElement("span");
        s.className = "bys360-live-pill";
        s.textContent = label;
        actions.appendChild(s);
      });
      wrap.appendChild(actions);
    }
    return wrap;
  }

  function insertTop(el){
    var c = firstContent();
    if(!c || !el) return;
    var target = c.querySelector("h1, .page-title, .content-header") || c.firstElementChild;
    if(target && target.parentNode) target.parentNode.insertBefore(el, target.nextSibling);
    else c.insertBefore(el, c.firstChild);
  }

  function enhanceFeedback(){
    var p = path();
    if(!(p.indexOf("/feedback") === 0 || p.indexOf("/geri-bildirim") === 0)) return;
    var isCampaignNew = p.indexOf("campaign") >= 0 || p.indexOf("kampanya") >= 0;
    if(isCampaignNew){
      insertTop(panel(
        "bys360-feedback-campaign-guidance",
        "Geri Bildirim Kampanyası Oluşturma",
        "Bu ekran; ekran hatası, eksik bildirme, öneri, tebrik ve teşekkür gibi kurumsal geri bildirimleri belirli dönem veya hedef kitle için toplamak amacıyla kullanılır. Kampanya açıldıktan sonra sonuçlar yetkili kullanıcılar tarafından izlenebilir ve raporlanabilir.",
        ["Kolay kullanım", "Yetki kontrollü görünürlük", "Kurumsal raporlama", "Takip edilebilir süreç"]
      ));
    }else{
      insertTop(panel(
        "bys360-feedback-guidance",
        "BYS360 Geri Bildirim Merkezi",
        "Bu alan; ekran hataları, eksikler, öneriler, tebrikler ve teşekkürlerin kayıtlı şekilde alınması için düzenlenmiştir. Amaç yalnızca mesaj toplamak değil, kurumsal gelişim için izlenebilir geri bildirim hafızası oluşturmaktır.",
        ["Ekran hatası", "Eksik bildirme", "Öneri", "Tebrik / teşekkür"]
      ));
    }
  }

  function enhanceRoleMatrix(){
    var p = path();
    if(!(p.indexOf("/settings") === 0 || p.indexOf("/ayar") === 0 || p.indexOf("role-matrix") >= 0 || p.indexOf("rol") >= 0)) return;
    var title = "Rol ve Menü Görünürlüğü Matrisi";
    var desc = "Bu bölümde rol, kişi ve birim bazlı görünürlük birlikte düşünülmelidir. Menü görünürlüğü kullanıcı deneyimi kadar güvenlik kontrolünün de parçasıdır; bu nedenle değişikliklerden sonra yetkili/yetkisiz kullanıcı senaryosu mutlaka kontrol edilmelidir.";
    if(p.indexOf("person") >= 0 || p.indexOf("personel") >= 0) {
      title = "Personel Bazlı Rol Matrisi";
      desc = "Bu ekran belirli personelin rol, menü ve işlem görünürlüğünü kontrol etmek için kullanılmalıdır. Kişi bazlı istisnalar kalıcı role dönüşmemeli; yapılan değişiklikler izlenebilir olmalıdır.";
    }
    insertTop(panel("bys360-role-matrix-guidance", title, desc, ["Rol bazlı", "Kişi bazlı", "Birim bazlı", "Audit log"]));
  }

  function enhancePortal(){
    var p = path();
    if(p.indexOf("/portal") !== 0) return;
    insertTop(panel(
      "bys360-portal-mobile-guidance",
      "Kurumsal Portal Mobil Uyumluluk",
      "Portal ekranı iPhone ve dar ekranlarda tek kolon, okunur kartlar ve taşmayan içerik mantığıyla düzenlenir. Instagram akışı gibi canlı bağlantı gerektiren alanlar hazır olana kadar ana görünümden gizlenir.",
      ["iPhone uyumlu", "Tek kolon kartlar", "Taşma kontrolü", "Sade portal"]
    ));
  }

  function cleanTechnicalLanguage(){
    var replacements = [
      [/\bunauthorized_scope\b/gi, "Bu işlem için yetkiniz bulunmamaktadır"],
      [/\bworkflow state\b/gi, "Süreç durumu"],
      [/\bphase sync\b/gi, "Süreç eşitleme"],
      [/\bsync\b/gi, "eşitleme"],
      [/\bdebug\b/gi, "kontrol"],
      [/\bendpoint\b/gi, "bağlantı"],
      [/\bexception\b/gi, "işlem hatası"],
      [/\btraceback\b/gi, "hata ayrıntısı"],
      [/\bJSON\b/g, "veri"],
      [/\bAPI error\b/gi, "Veriler şu anda alınamadı"]
    ];
    var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
      acceptNode:function(node){
        if(!node.nodeValue || !node.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
        var parent = node.parentElement;
        if(!parent) return NodeFilter.FILTER_REJECT;
        var tag = parent.tagName ? parent.tagName.toLowerCase() : "";
        if(["script","style","code","pre","textarea"].indexOf(tag) >= 0) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    var nodes = [];
    while(walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(function(n){
      var text = n.nodeValue;
      var out = text;
      replacements.forEach(function(r){ out = out.replace(r[0], r[1]); });
      if(out !== text) {
        n.nodeValue = out;
        if(n.parentElement) n.parentElement.classList.add("bys360-live-tech-clean");
      }
    });
  }

  function ensureTablesResponsive(){
    document.querySelectorAll("table").forEach(function(tbl){
      if(tbl.parentElement && tbl.parentElement.classList.contains("table-responsive")) return;
      var wrap = document.createElement("div");
      wrap.className = "table-responsive";
      tbl.parentNode.insertBefore(wrap, tbl);
      wrap.appendChild(tbl);
    });
  }

  ready(function(){
    addBodyClasses();
    enhanceFeedback();
    enhanceRoleMatrix();
    enhancePortal();
    ensureTablesResponsive();
    cleanTechnicalLanguage();
  });
})();
