// BYS360_NATIVE_APP_BRIDGE_V1_JS
// Capacitor/WebView içinden açılan BYS360 ekranlarında güvenli native davranışları etkinleştirir.
(function () {
  'use strict';

  var ua = navigator.userAgent || '';
  var isNativeUA = ua.indexOf('BYS360Mobile/') !== -1 || ua.indexOf('BYS360NativeApp/') !== -1;
  var isCapacitor = !!(window.Capacitor && (window.Capacitor.isNativePlatform ? window.Capacitor.isNativePlatform() : true));
  var isNativeApp = isNativeUA || isCapacitor;
  if (!isNativeApp) return;

  document.documentElement.classList.add('bys360-native-app');
  if (document.body) document.body.classList.add('bys360-native-app');
  document.addEventListener('DOMContentLoaded', function () {
    document.body && document.body.classList.add('bys360-native-app');
    document.documentElement.classList.add('bys360-native-app-ready');
  });

  try {
    localStorage.setItem('BYS360_PWA_INSTALL_CARD_HIDDEN_IN_NATIVE', '1');
  } catch (e) {}

  try {
    var plugins = window.Capacitor && window.Capacitor.Plugins ? window.Capacitor.Plugins : null;
    var App = plugins && plugins.App ? plugins.App : null;
    if (App && typeof App.addListener === 'function') {
      App.addListener('backButton', function () {
        var path = window.location.pathname || '/';
        var isHome = path === '/' || path === '/home' || path.indexOf('/login') === 0;
        if (!isHome && window.history && window.history.length > 1) {
          window.history.back();
          return;
        }
        if (typeof App.exitApp === 'function') {
          App.exitApp();
        }
      });
    }
  } catch (e) {
    // Sessiz kal: web ortamında veya eski WebView'de hata göstermeyelim.
  }

  function updateOnlineClass() {
    document.documentElement.classList.toggle('bys360-native-offline', navigator.onLine === false);
  }
  window.addEventListener('online', updateOnlineClass);
  window.addEventListener('offline', updateOnlineClass);
  updateOnlineClass();
})();
