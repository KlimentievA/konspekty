/* Синхронизация прогресса между устройствами (телефон, компьютер, приложение).
   Хранилище — Cloudflare Worker (worker/sync-worker.js). Пока SYNC_URL пуст, скрипт ничего не делает.
   Как работает: любая запись в localStorage по ключам прогресса помечается временем изменения, затем в фоне
   страница забирает облачную копию, берёт у каждого ключа более свежую версию и отправляет результат обратно.
   Профиль (artem / nastya) берётся из входа в Hub: у каждого человека своя копия. */
(function () {
  var SYNC_URL = '';
  if (!SYNC_URL || !window.fetch || !window.localStorage || !window.Storage) return;

  var LS = window.localStorage, SP = Storage.prototype;
  var nset = SP.setItem, nrem = SP.removeItem, nget = SP.getItem;

  /* 2 — отметки и тесты: при подтягивании чужих изменений страница один раз перезагружается;
     1 — «мягкие» настройки и место, где остановились: применяются при следующем открытии */
  var HARD = /^(fin:(done|quiz|fav|qa)|eng:[^:]+|zach|tk|tkstar|plan|bm|hl|todo)$/;
  var SOFT = /^(fin:(last|sub|skin)|last(:.+)?|eng:last:.+|fz|skin|theme|siteZoom|calc)$/;
  function kind(k) { return HARD.test(k) ? 2 : SOFT.test(k) ? 1 : 0 }

  var P = nget.call(LS, 'hub:last');
  if (!P || !/^(artem|nastya)$/.test(P) || !nget.call(LS, 'hub:auth:' + P)) return;
  var URL_ = SYNC_URL.replace(/\/+$/, '') + '/p/' + P;

  function meta() { try { return JSON.parse(nget.call(LS, 'sync:meta') || '{}') || {} } catch (e) { return {} } }
  function saveMeta(m) { try { nset.call(LS, 'sync:meta', JSON.stringify(m)) } catch (e) {} }
  function allKeys() { var a = []; for (var i = 0; i < LS.length; i++) { var k = LS.key(i); if (k && kind(k)) a.push(k) } return a }

  /* на устройстве уже был другой профиль — его данные сюда не относятся */
  var prevP = nget.call(LS, 'sync:prof');
  if (prevP && prevP !== P) { allKeys().forEach(function (k) { nrem.call(LS, k) }); nrem.call(LS, 'sync:meta') }
  nset.call(LS, 'sync:prof', P);

  /* первая синхронизация: у ключей, записанных до появления синхронизации, нет метки времени.
     Если такие данные есть и в облаке, объединяем (отметки «пройдено» складываются, а не затирают друг друга) */
  function isObj(x) { return x && typeof x === 'object' && !Array.isArray(x) }
  function deep(a, b) {
    var byId = function (x) { return x.every(function (e) { return e && typeof e === 'object' && e.id != null }) };
    if (Array.isArray(a) && Array.isArray(b) && a.length && b.length && byId(a) && byId(b)) {
      var seenId = {}, res = [];
      a.concat(b).forEach(function (e) { if (!seenId[e.id]) { seenId[e.id] = 1; res.push(e) } });
      return res;
    }
    if (Array.isArray(a) && Array.isArray(b)) { var s = {}, o = []; a.concat(b).forEach(function (x) { var j = JSON.stringify(x); if (!s[j]) { s[j] = 1; o.push(x) } }); return o }
    if (isObj(a) && isObj(b)) { var r = {}, k; for (k in b) r[k] = b[k]; for (k in a) r[k] = k in b ? deep(a[k], b[k]) : a[k]; return r }
    return a;
  }
  function union(lv, rv) {
    try { return JSON.stringify(deep(JSON.parse(lv), JSON.parse(rv))) } catch (e) { return rv }
  }

  var applying = false, timer = 0, busy = false, again = false, lastRun = 0, dirty = {};
  function touch(k) { var m = meta(); m[k] = Date.now(); saveMeta(m); dirty[k] = 1; plan(1500) }
  function plan(ms) { clearTimeout(timer); timer = setTimeout(function () { sync(false) }, ms) }

  SP.setItem = function (k, v) {
    if (this === LS && !applying && kind(k)) {
      var old = nget.call(this, k);
      nset.call(this, k, v);
      if (old !== String(v)) touch(k);
      return;
    }
    return nset.apply(this, arguments);
  };
  SP.removeItem = function (k) {
    if (this === LS && !applying && kind(k)) {
      var had = nget.call(this, k) !== null;
      nrem.call(this, k);
      if (had) touch(k);
      return;
    }
    return nrem.apply(this, arguments);
  };

  function req(opts, ms) {
    var ac = window.AbortController ? new AbortController() : null, t = ac && setTimeout(function () { ac.abort() }, ms || 9000);
    if (ac) opts.signal = ac.signal;
    return fetch(URL_, opts).then(function (r) { clearTimeout(t); return r }, function (e) { clearTimeout(t); throw e });
  }

  function flush() {
    var ks = Object.keys(dirty);
    if (!ks.length) return;
    clearTimeout(timer); timer = 0;
    var m = meta(), body = {};
    ks.forEach(function (k) { var v = nget.call(LS, k); body[k] = [v, m[k] || Date.now()] });
    try { fetch(URL_, { method: 'PUT', keepalive: true, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }) } catch (e) {}
  }

  function sync(first) {
    if (busy) { again = true; return }
    busy = true; lastRun = Date.now();
    req({ cache: 'no-store' }).then(function (r) {
      if (r.status === 404) return {};
      if (!r.ok) throw 0;
      return r.json();
    }).then(function (R) {
      R = isObj(R) ? R : {};
      var m = meta(), out = {}, push = false, hard = false, seen = {}, k;
      for (k in R) seen[k] = 1;
      allKeys().forEach(function (x) { seen[x] = 1 });
      for (k in m) if (kind(k)) seen[k] = 1;
      applying = true;
      try {
        Object.keys(seen).forEach(function (k) {
          if (!kind(k)) return;
          var lv = nget.call(LS, k), lt = m[k] || 0, r = R[k], rv = r ? r[0] : null, rt = r ? (+r[1] || 0) : 0, now = Date.now();
          if (lv !== null && !lt) {                       /* данные из времён до синхронизации */
            if (r && rv !== null && rv !== undefined) {
              var u = union(lv, String(rv));
              if (u !== lv) { nset.call(LS, k, u); if (kind(k) === 2) hard = true }
              if (u !== String(rv)) { m[k] = now; out[k] = [u, now]; push = true } else m[k] = rt;
            } else { m[k] = now; out[k] = [lv, now]; push = true }
            return;
          }
          if (rt > lt) {                                  /* в облаке свежее */
            var cur = lv;
            if (rv === null || rv === undefined) nrem.call(LS, k); else nset.call(LS, k, String(rv));
            if (cur !== (rv === undefined ? null : rv) && kind(k) === 2) hard = true;
            m[k] = rt;
          } else if (lt > rt) {                           /* на устройстве свежее */
            out[k] = [lv, lt]; push = true;
          }
        });
      } finally { applying = false }
      saveMeta(m);
      if (hard || Object.keys(out).length) { try { window.dispatchEvent(new Event('sync:applied')) } catch (e) {} }
      if (!push) return hard;
      return req({ method: 'PUT', keepalive: true, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(out) }).then(function (r) { if (!r.ok) throw 0; dirty = {}; return hard });
    }).then(function (hard) {
      busy = false;
      if (hard && first) {
        var last = +(sessionStorage.getItem('sync:rl') || 0);
        if (Date.now() - last > 30000) { try { sessionStorage.setItem('sync:rl', String(Date.now())) } catch (e) {} location.reload(); return }
      }
      if (again) { again = false; plan(300) }
    }).catch(function () { busy = false; again = false });
  }

  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'visible') { if (Date.now() - lastRun > 20000) sync(false) }
    else flush();
  });
  window.addEventListener('online', function () { sync(false) });
  window.addEventListener('pagehide', flush);
  setInterval(function () { if (document.visibilityState === 'visible') sync(false) }, 90000);
  sync(true);
})();
