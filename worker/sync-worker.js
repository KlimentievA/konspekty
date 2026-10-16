// Cloudflare Worker: хранит прогресс двух профилей (artem, nastya) в KV.
// GET  /p/<профиль>  -> JSON { ключ: [значение, время] }
// PUT  /p/<профиль>  <- JSON с изменёнными ключами; воркер сливает его с сохранённым (побеждает более позднее время)
const ALLOW = ['https://klimentiev-a.github.io'];
export default {
  async fetch(req, env) {
    const o = req.headers.get('Origin') || '';
    const cors = {
      'Access-Control-Allow-Origin': ALLOW.includes(o) ? o : ALLOW[0],
      'Access-Control-Allow-Methods': 'GET,PUT,OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Access-Control-Max-Age': '86400',
      'Vary': 'Origin',
    };
    if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });
    const m = new URL(req.url).pathname.match(/^\/p\/(artem|nastya)$/);
    if (!m) return new Response('not found', { status: 404, headers: cors });
    const key = 'p:' + m[1];
    if (req.method === 'GET') {
      const v = await env.KV.get(key);
      return new Response(v || '{}', { headers: { ...cors, 'Content-Type': 'application/json', 'Cache-Control': 'no-store' } });
    }
    if (req.method === 'PUT') {
      const t = await req.text();
      if (t.length > 900000) return new Response('too big', { status: 413, headers: cors });
      let j; try { j = JSON.parse(t) } catch (e) { return new Response('bad json', { status: 400, headers: cors }) }
      if (!j || typeof j !== 'object' || Array.isArray(j)) return new Response('bad shape', { status: 400, headers: cors });
      // сливаем с тем, что уже лежит: по каждому ключу остаётся версия с более поздним временем
      let cur = {};
      try { cur = JSON.parse((await env.KV.get(key)) || '{}') || {} } catch (e) { cur = {} }
      for (const k of Object.keys(j)) {
        const n = j[k];
        if (!Array.isArray(n) || n.length !== 2 || typeof n[1] !== 'number') continue;
        if (k.length > 80) continue;
        if (!cur[k] || !(cur[k][1] >= n[1])) cur[k] = n;
      }
      const out = JSON.stringify(cur);
      if (out.length > 900000) return new Response('too big', { status: 413, headers: cors });
      await env.KV.put(key, out);
      return new Response('ok', { headers: cors });
    }
    return new Response('method', { status: 405, headers: cors });
  },
};
