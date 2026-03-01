/**
 * TestMakon — Service Worker
 * Strategy: Cache-first for static assets, Network-first for API/HTML
 */

const CACHE_NAME = 'testmakon-v1';
const STATIC_CACHE = 'testmakon-static-v1';

// Cache these on install
const PRECACHE_URLS = [
  '/',
  '/tests/',
  '/ai/mentor/',
  '/leaderboard/',
];

// Always fetch fresh from network (no cache)
const NETWORK_ONLY = [
  '/admin/',
  '/tgbot/',
  '/api/',
  '/accounts/login/',
  '/accounts/logout/',
];

self.addEventListener('install', event => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(STATIC_CACHE).then(cache => {
      return cache.addAll(PRECACHE_URLS).catch(() => {});
    })
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(k => k !== CACHE_NAME && k !== STATIC_CACHE).map(k => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  // Skip non-GET, cross-origin, network-only paths
  if (event.request.method !== 'GET') return;
  if (url.origin !== self.location.origin) return;
  if (NETWORK_ONLY.some(p => url.pathname.startsWith(p))) return;

  // Static assets — cache first
  if (url.pathname.startsWith('/static/') || url.pathname.startsWith('/media/')) {
    event.respondWith(
      caches.match(event.request).then(cached => {
        if (cached) return cached;
        return fetch(event.request).then(resp => {
          if (resp.ok) {
            const clone = resp.clone();
            caches.open(STATIC_CACHE).then(c => c.put(event.request, clone));
          }
          return resp;
        }).catch(() => cached);
      })
    );
    return;
  }

  // HTML pages — network first, fallback to cache
  event.respondWith(
    fetch(event.request)
      .then(resp => {
        if (resp.ok) {
          const clone = resp.clone();
          caches.open(CACHE_NAME).then(c => c.put(event.request, clone));
        }
        return resp;
      })
      .catch(() => caches.match(event.request))
  );
});
