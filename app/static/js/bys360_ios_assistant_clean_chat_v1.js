(function () {
  function cleanAssistantForIphone() {
    var isIphone = /iPhone|iPod/.test(navigator.userAgent);
    if (!isIphone) return;

    document.documentElement.classList.add("bys360-ios-clean-assistant");

    var texts = [
      "Nereye gitmeliyim?",
      "Yetki kontrollü güvenli özet",
      "Güvenli kullanım sınırları",
      "Anasayfa",
      "Dashboard",
      "Bekleyen bildirim",
      "Karar üretmez"
    ];

    document.querySelectorAll("h1,h2,h3,h4,p,div,section,article").forEach(function (el) {
      var t = (el.textContent || "").trim();
      if (texts.some(function (x) { return t.indexOf(x) >= 0; })) {
        var cls = (el.className || "").toString();
        if (!cls.includes("assistant-header") && !cls.includes("assistant-input")) {
          el.style.display = "none";
        }
      }
    });
  }

  document.addEventListener("DOMContentLoaded", cleanAssistantForIphone);
  document.addEventListener("click", function () {
    setTimeout(cleanAssistantForIphone, 250);
  });
})();
