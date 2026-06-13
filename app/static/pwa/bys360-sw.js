/* BYS360 iOS PWA V2 Advanced Mobile App Service Worker
   Güvenlik ilkesi: oturumlu HTML, API yanıtı, personel/performans/mesaj içeriği cache içine alınmaz.
   Sadece PWA kabuğu, ikonlar, splash ve ortak statik dosyalar kontrollü cache'lenir. */
const BYS360_SW_VERSION = 'bys360-logout-force-clear-v2-15-12';
const BYS360_STATIC_CACHE = `bys360-static-${BYS360_SW_VERSION}`;
const BYS360_OFFLINE_URL = '/static/pwa/offline.html';
const BYS360_STATIC_ASSETS = [
  BYS360_OFFLINE_URL,
  '/manifest.webmanifest',
  '/static/pwa/manifest.webmanifest',
  '/static/css/bys360_ios_pwa_v2.css',
  '/static/js/bys360_ios_pwa_v2.js',
  '/static/pwa/icons/icon-192.png',
  '/static/pwa/icons/icon-512.png',
  '/static/pwa/icons/apple-touch-icon.png'
];

function isSafeStaticRequest(url) {
  return url.pathname.startsWith('/static/pwa/') ||
         url.pathname === '/static/css/bys360_ios_pwa_v2.css' ||
         url.pathname === '/static/js/bys360_ios_pwa_v2.js' ||
         url.pathname === '/manifest.webmanifest';
}

function isSensitiveRequest(request, url) {
  if (request.method !== 'GET') return true;
  if (request.headers.has('Authorization')) return true;
  if (url.pathname.startsWith('/api/')) return true;
  if (url.pathname.startsWith('/auth')) return true;
  if (url.pathname.startsWith('/login')) return true;
  if (url.pathname.startsWith('/logout')) return true;
  if (url.pathname.startsWith('/admin')) return true;
  if (url.pathname.includes('/messages')) return true;
  if (url.searchParams.has('nocache')) return true;
  return false;
}

self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(BYS360_STATIC_CACHE);
    await cache.addAll(BYS360_STATIC_ASSETS.map(url => new Request(url, { cache: 'reload' })));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(key => key.startsWith('bys360-static-') && key !== BYS360_STATIC_CACHE).map(key => caches.delete(key)));
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', event => {
  const request = event.request;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  if (isSensitiveRequest(request, url)) return;

  if (request.mode === 'navigate') {
    event.respondWith((async () => {
      try {
        return await fetch(request);
      } catch (error) {
        const cache = await caches.open(BYS360_STATIC_CACHE);
        return (await cache.match(BYS360_OFFLINE_URL)) || new Response('BYS360 bağlantısı kurulamadı.', { status: 503, headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
      }
    })());
    return;
  }

  if (isSafeStaticRequest(url)) {
    event.respondWith((async () => {
      const cache = await caches.open(BYS360_STATIC_CACHE);
      const cached = await cache.match(request);
      const networkPromise = fetch(request).then(response => {
        if (response && response.ok) cache.put(request, response.clone());
        return response;
      }).catch(() => cached);
      return cached || networkPromise;
    })());
  }
});
