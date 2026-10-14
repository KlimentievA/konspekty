/* Hub service worker.
   Страницы и картинки — сразу из кэша (мгновенно), а в фоне проверяется новая версия; если она вышла — странице приходит сигнал «обновлено».
   Данные (*.json) — сначала сеть (свежие котировки и новости), если сеть не ответила за 4 с — из кэша.
   Шрифты Google и история цен с GitHub — из кэша с фоновым обновлением. */
const V = 'hub-v30', STATIC = V + '-static', DATA = 'hub-data', EXT = 'hub-ext';
const CORE = ['./', 'index.html', 'ucheba.html', 'finance.html', 'manifest.webmanifest', 'icon-192.png', 'apple-touch-icon.png'];

self.addEventListener('install', e => {
  self.skipWaiting();
  e.waitUntil(caches.open(STATIC).then(c => c.addAll(CORE)).catch(() => {}));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(k => Promise.all(k.filter(x => ![STATIC, DATA, EXT].includes(x)).map(x => caches.delete(x)))).then(() => self.clients.claim()));
});

function tag(res) { return res && (res.headers.get('etag') || res.headers.get('last-modified') || res.headers.get('content-length')) || ''; }

// страница могла ещё не успеть открыться, когда пришла новая версия, — запоминаем и отвечаем на её вопрос «я свежая?»
const UPDATED = new Map();   // путь → когда пришла новая версия
function pth(u) { const p = new URL(u).pathname; return p.endsWith('/') ? p + 'index.html' : p; }
async function notify(url) {
  UPDATED.set(pth(url), Date.now());
  const cs = await self.clients.matchAll({ type: 'window' });
  cs.forEach(c => { if (pth(c.url) === pth(url)) c.postMessage({ t: 'hub-updated', url }); });
}
self.addEventListener('message', e => {
  if (!e.data || e.data.t !== 'hub-check' || !e.source) return;
  const t = UPDATED.get(pth(e.data.url));
  if (t && Date.now() - t < 20000) { UPDATED.delete(pth(e.data.url)); e.source.postMessage({ t: 'hub-updated', url: e.data.url }); }
});

// кэш сразу, сеть в фоне
async function swr(ev, req, cacheName, watch) {
  const cache = await caches.open(cacheName);
  const hit = await cache.match(req, { ignoreSearch: false });
  const net = fetch(req, { cache: 'no-cache' }).then(async res => {
    if (res && (res.ok || res.type === 'opaque')) {
      if (watch && hit && tag(hit) && tag(res) && tag(hit) !== tag(res)) notify(req.url);
      await cache.put(req, res.clone());
    }
    return res;
  }).catch(() => null);
  if (hit) { ev.waitUntil(net); return hit; }
  const res = await net;
  if (res) return res;
  if (req.mode === 'navigate') return (await caches.match('index.html')) || Response.error();
  return Response.error();
}

// сеть с таймаутом, потом кэш
async function nf(req, cacheName, ms) {
  const cache = await caches.open(cacheName);
  const u = new URL(req.url), key = u.origin + u.pathname;   // ?t=… не плодит копии в кэше
  const net = fetch(req, { cache: 'no-cache' }).then(res => { if (res && res.ok) cache.put(key, res.clone()); return res; });
  net.catch(() => {});
  const timeout = new Promise(r => setTimeout(() => r(null), ms));
  try {
    const first = await Promise.race([net.catch(() => null), timeout]);
    if (first) return first;
    const hit = await cache.match(key);
    if (hit) return hit;
    return await net;
  } catch (e) {
    return (await cache.match(key)) || Response.error();
  }
}

self.addEventListener('fetch', e => {
  const r = e.request;
  if (r.method !== 'GET') return;
  const u = new URL(r.url);
  if (u.origin === location.origin) {
    if (/\.json$/.test(u.pathname)) { e.respondWith(nf(r, DATA, 4000)); return; }
    e.respondWith(swr(e, r, STATIC, r.mode === 'navigate' || /\.html$|\/$/.test(u.pathname)));
    return;
  }
  if (u.hostname === 'fonts.googleapis.com' || u.hostname === 'fonts.gstatic.com' || u.hostname === 'raw.githubusercontent.com') {
    e.respondWith(swr(e, r, EXT, false));
  }
});
