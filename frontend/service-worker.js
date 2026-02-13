const CACHE_NAME = 'toci-tools-cache-v2026021303';
const PRECACHE_ASSETS = [
  '/',
  '/temu',
  '/pdf',
  '/csv',
  '/manifest.json',
  '/static/dashboard.js',
  '/components/navigation.html',
  '/components/nav-loader.js',
  '/components/progress-helper.js',
  '/components/ui-helpers.js',
  '/icons/icon-192.png',
  '/icons/icon-512.png'
];

// ═══ Caching Strategies ═══

/**
 * Stale-While-Revalidate: Return cached version immediately,
 * fetch fresh version in background for next request
 */
async function staleWhileRevalidate(request) {
  const cached = await caches.match(request);
  const fetchPromise = fetch(request)
    .then(async (response) => {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
      return response;
    })
    .catch(() => null);

  return cached || fetchPromise || caches.match('/');
}

/**
 * Delete all caches except the current version
 */
async function cleanOldCaches() {
  const keys = await caches.keys();
  const deletions = keys
    .filter((k) => k !== CACHE_NAME)
    .map((k) => {
      console.log('Deleting old cache:', k);
      return caches.delete(k);
    });
  await Promise.all(deletions);
  console.log('Service Worker activated with cache:', CACHE_NAME);
}

// ═══ Lifecycle Events ═══

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    cleanOldCaches().then(() => self.clients.claim())
  );
});

// ═══ Fetch Strategy Router ═══

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);

  // API calls → Network Only (live data must always be fresh)
  if (url.pathname.startsWith('/api/')) return;

  // Static Assets → Stale-While-Revalidate
  event.respondWith(staleWhileRevalidate(request));
});
