// BYS360 iOS PWA V3 service worker shell helper
// Not: Tam kapsamlı offline veri saklama yapmaz; sadece statik PWA varlıkları için güvenli kabuk sağlar.
const BYS360_IOS_PWA_CACHE = 'bys360-ios-pwa-logout-v2-15-12';
const BYS360_IOS_PWA_ASSETS = [
  '/static/pwa/ios_pwa_premium.css',
  '/static/pwa/ios_pwa_premium.js',
  '/static/pwa/manifest-ios-premium.webmanifest'
];
self.addEventListener('install', event => {
  event.waitUntil(caches.open(BYS360_IOS_PWA_CACHE).then(cache => cache.addAll(BYS360_IOS_PWA_ASSETS)).catch(() => undefined));
  self.skipWaiting();
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== BYS360_IOS_PWA_CACHE && k.indexOf('bys360-ios-pwa-') === 0).map(k => caches.delete(k)))));
  self.clients.claim();
});
self.addEventListener('fetch', event => {
  try { if (new URL(event.request.url).pathname.startsWith('/logout')) return; } catch (e) {}
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;
  if (url.pathname.startsWith('/static/pwa/')) {
    event.respondWith(caches.match(req).then(cached => cached || fetch(req)));
  }
});
