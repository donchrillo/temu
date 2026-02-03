const CACHE_NAME = 'toci-tools-cache-v2026020318'; // Removed old files
const ASSETS = [
  '/',
  '/temu',
  '/pdf',
  '/manifest.json',
  '/static/dashboard.css',
  '/static/pdf.css?v=20260203',
  '/static/pdf.js?v=20260203',
  '/static/temu.css?v=20260203',
  '/static/temu.js?v=20260203'
];

self.addEventListener('install', (event) => {
  // FORCE UNREGISTER OLD SERVICE WORKERS
  event.waitUntil(
    caches.keys().then((keys) => {
      // Delete ALL old caches
      return Promise.all(keys.map((key) => caches.delete(key)));
    }).then(() => {
      // Then install new cache
      return caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS));
    })
  );
  self.skipWaiting(); // Force immediate activation
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      // Delete ALL caches except current
      return Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => {
          console.log('Deleting old cache:', k);
          return caches.delete(k);
        })
      );
    }).then(() => {
      console.log('Service Worker activated with cache:', CACHE_NAME);
      return self.clients.claim(); // Take control immediately
    })
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);

  // ALL API calls: Network Only (NEVER cache)
  // Reason: Live data must always be fresh
  if (url.pathname.startsWith('/api/')) {
    return; // Let browser handle API calls normally (no service worker intervention)
  }
  
  // HTML/CSS/JS: Stale-while-revalidate
  event.respondWith(
    caches.match(request).then((cached) => {
      const fetchPromise = fetch(request).then((resp) => {
        const respClone = resp.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(request, respClone));
        return resp;
      });
      return cached || fetchPromise;
    }).catch(() => caches.match('/'))
  );
});
