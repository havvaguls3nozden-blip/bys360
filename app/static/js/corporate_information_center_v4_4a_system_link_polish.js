// BYS360_CIC_V4_4A_SYSTEM_LINK_POLISH
(function(){
  "use strict";
  var ROOT = "/dashboard/kurumsal-bilgilendirme";
  function norm(x){
    try { return new URL(x || window.location.href, window.location.origin).pathname.replace(/\/+$/, "") || "/"; }
    catch(e){ return String(x || "").replace(/\/+$/, "") || "/"; }
  }
  function apply(){
    var current = norm(window.location.href);
    if(current.indexOf(ROOT)!==0) return;
    document.body.classList.add("bys360-cic-v44a");
    var isSystem = current === ROOT + "/sistem" || current.indexOf(ROOT + "/sistem/") === 0;
    document.body.classList.toggle("bys360-cic-system-page", isSystem);
    document.querySelectorAll('a[href*="/dashboard/kurumsal-bilgilendirme/kutlamalar"]').forEach(function(a){
      if(isSystem){
        a.classList.remove("text-primary","link-primary","btn-link","active","is-active","selected","current");
        a.removeAttribute("aria-current");
        a.classList.add("cic-v44a-link-polished");
      }
    });
    if(isSystem){
      document.querySelectorAll('a[href*="/dashboard/kurumsal-bilgilendirme/sistem"]').forEach(function(a){
        a.classList.add("active");
        a.setAttribute("aria-current","page");
      });
    }
  }
  if(document.readyState === "loading") document.addEventListener("DOMContentLoaded", apply); else apply();
  setTimeout(apply, 250); setTimeout(apply, 900); setTimeout(apply, 1600);
})();
