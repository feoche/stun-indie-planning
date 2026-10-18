// Service worker : coquille et données en réseau d'abord (délai 4 s), repli sur le cache hors-ligne.
// La coquille vient donc toujours d'un même déploiement quand le réseau répond.
const SHELL_CACHE = 'stunindie-shell-v1';
const DATA_CACHE = 'stunindie-data-v1';
const NETWORK_TIMEOUT_MS = 4000;
const SHELL = [
  './', './index.html', './style.css', './manifest.webmanifest',
  './js/app.js', './js/model.js', './js/store.js', './js/render.js', './js/data.js', './js/reminders.js', './js/team.js',
  './icons/icon-192.png', './icons/icon-512.png', './icons/apple-touch-icon.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil(Promise.all([
    caches.open(SHELL_CACHE).then((c) => c.addAll(SHELL.map((u) => new Request(u, { cache: 'reload' })))),
    // le planning est préchargé : ouvrir l'appli une fois suffit pour l'avoir hors-ligne
    caches.open(DATA_CACHE).then((c) => c.add(new Request('./data/planning.json', { cache: 'reload' }))),
  ]).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== SHELL_CACHE && k !== DATA_CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

const isData = (url) => url.pathname.endsWith('/data/planning.json') || url.pathname.includes('/cal/');

// Réseau d'abord avec délai maximal (4G saturée) : au-delà, on sert le cache.
function fetchWithTimeout(request, ms) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), ms);
  return fetch(request, { cache: 'no-store', signal: ctrl.signal }).finally(() => clearTimeout(timer));
}

async function networkFirst(request, cacheName, markCached) {
  const cache = await caches.open(cacheName);
  try {
    const response = await fetchWithTimeout(request, NETWORK_TIMEOUT_MS);
    if (response.ok) cache.put(request, response.clone());
    return response;
  } catch (err) {
    const cached = await cache.match(request, { ignoreSearch: markCached ? false : true });
    if (!cached) throw err;
    if (!markCached) return cached;
    const headers = new Headers(cached.headers);
    headers.set('x-sw-cache', '1');
    return new Response(cached.body, { status: cached.status, statusText: cached.statusText, headers });
  }
}

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  event.respondWith(isData(url) ? networkFirst(request, DATA_CACHE, true) : networkFirst(request, SHELL_CACHE, false));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(self.clients.matchAll({ type: 'window' }).then((wins) => (
    wins.length ? wins[0].focus() : self.clients.openWindow('./'))));
});
