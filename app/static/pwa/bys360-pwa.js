(function () {
  "use strict";

  function isStandalone() {
    return window.matchMedia("(display-mode: standalone)").matches || window.navigator.standalone === true;
  }

  function markMode() {
    document.documentElement.classList.toggle("bys360-pwa-standalone", isStandalone());
    document.documentElement.classList.add("bys360-pwa-ready");
  }

  function registerServiceWorker() {
    if (!("serviceWorker" in navigator)) {
      return;
    }

    // Register only after the first render. If registration fails, BYS360 must still work normally.
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("/sw.js", { scope: "/" }).catch(function () {
        // Silent by design: users should not see technical service worker messages.
      });
    });
  }

  function addInstallHintForIOS() {
    var isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) ||
      (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);

    if (!isIOS || isStandalone()) {
      return;
    }

    // The hint is intentionally unobtrusive and shown only once per browser.
    try {
      if (window.localStorage.getItem("bys360_ios_install_hint_closed") === "1") {
        return;
      }
    } catch (e) {
      return;
    }

    window.addEventListener("load", function () {
      if (document.querySelector(".bys360-ios-install-hint")) {
        return;
      }

      var hint = document.createElement("div");
      hint.className = "bys360-ios-install-hint";
      hint.innerHTML = "<strong>BYS360</strong><span>iPad/iPhone ana ekranına eklemek için Safari paylaş menüsünden <b>Ana Ekrana Ekle</b> seçeneğini kullanabilirsiniz.</span><button type=\"button\" aria-label=\"Kapat\">×</button>";
      document.body.appendChild(hint);

      var close = hint.querySelector("button");
      close.addEventListener("click", function () {
        hint.remove();
        try { window.localStorage.setItem("bys360_ios_install_hint_closed", "1"); } catch (e) {}
      });
    });
  }

  markMode();
  registerServiceWorker();
  addInstallHintForIOS();
})();
