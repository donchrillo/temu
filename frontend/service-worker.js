const CACHE_NAME = 'toci-tools-cache-v' + new Date().getTime();
const ASSETS = [
  '/',
  '/index.html',
  '/temu',
  '/styles.css',
  '/app.js',
  '/navbar.js',
  '/manifest.json',
  '/pdf-reader.html',
  '/pdf-reader.js'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => !k.includes('toci-tools-cache-v')).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  
  // API calls: Network first
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then((resp) => {
          const respClone = resp.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, respClone));
          return resp;
        })
        .catch(() => caches.match(request))
    );
    return;
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
