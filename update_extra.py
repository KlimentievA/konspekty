#!/usr/bin/env python3
"""Дополнительные данные для раздела «Рынки» (запускается из scripts/update_all.sh после основного обновления):
  corp_cal.json — дивиденды российских эмитентов (Мосбиржа ISS: ближайшие отсечки и история за ~14 месяцев);
  fin.json      — отчётность американских компаний по годам (Yahoo fundamentals-timeseries), обновляется раз в 6 дней;
  digest.json   — «Сводка недели»: изменение цен за 7 дней, главные новости, события и дивиденды на ближайшие дни
                  (digest_hist.json хранит суточные снимки цен за 21 день).
Любая часть при сбое не трогает прежний файл. Код выхода всегда 0."""
import json, os, sys, time, datetime, urllib.request, urllib.parse, re

HERE = os.path.dirname(os.path.abspath(__file__))
_LOG = []
_print = print
def print(*a):
    t = ' '.join(str(x) for x in a); _LOG.append(t); _print(t)
sys.path.insert(0, os.path.join(HERE, 'src', 'finance'))
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36', 'Accept': 'application/json,*/*'}
try:
    import static_data as S
except Exception as e:
    print('static_data', e); S = None
NOW = datetime.datetime.utcnow()
TODAY = NOW.strftime('%Y-%m-%d')

def get(url, t=25):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=t) as r:
        return json.loads(r.read().decode('utf-8'))

def load(p, d=None):
    try: return json.load(open(os.path.join(HERE, p), encoding='utf-8'))
    except Exception: return d

def save(p, o):
    json.dump(o, open(os.path.join(HERE, p), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

# ---------- дивиденды ----------
def corp_cal():
    if not S: return
    lim = (NOW - datetime.timedelta(days=430)).strftime('%Y-%m-%d'); items = []; ok = 0
    for r in S.RU:
        t = r[0]
        try:
            j = get('https://iss.moex.com/iss/securities/%s/dividends.json?iss.meta=off' % t, 15)
            cols = j['dividends']['columns']; ix = {c: i for i, c in enumerate(cols)}
            for row in j['dividends']['data']:
                d = row[ix['registryclosedate']]; v = row[ix['value']]
                if d and v is not None and d >= lim:
                    items.append({'t': t, 'd': d, 'v': v, 'c': row[ix.get('currencyid', 0)] if 'currencyid' in ix else 'RUB'})
            ok += 1
        except Exception as e:
            print('div', t, e)
        time.sleep(0.15)
    if ok < 5:
        print('corp_cal: слишком мало ответов, файл не трогаем'); return
    items.sort(key=lambda x: x['d'], reverse=True)
    save('corp_cal.json', {'updated': NOW.strftime('%Y-%m-%dT%H:%MZ'), 'items': items})
    print('corp_cal', len(items), 'записей по', ok, 'эмитентам')

# ---------- отчётность США ----------
TYPES = ['TotalRevenue', 'GrossProfit', 'OperatingIncome', 'EBITDA', 'NetIncome', 'FreeCashFlow', 'TotalDebt', 'CashAndCashEquivalents', 'DilutedEPS']
def fin():
    if not S: return
    old = load('fin.json', {})
    if old.get('updated') and (NOW - datetime.datetime.strptime(old['updated'], '%Y-%m-%dT%H:%MZ')).days < 6: print('fin: свежий, пропуск'); return
    out = {}; p1 = int(datetime.datetime(NOW.year - 6, 1, 1).timestamp()); p2 = int(NOW.timestamp())
    for r in S.US:
        t = r[0]
        try:
            url = ('https://query1.finance.yahoo.com/ws/fundamentals-timeseries/v1/finance/timeseries/%s?symbol=%s&type=%s&merge=false&period1=%d&period2=%d'
                   % (urllib.parse.quote(t), urllib.parse.quote(t), ','.join('annual' + x for x in TYPES), p1, p2))
            j = get(url, 20); rows = {}
            for res in j['timeseries']['result']:
                ty = res['meta']['type'][0]
                for pt in res.get(ty) or []:
                    if pt and pt.get('reportedValue') is not None:
                        rows.setdefault(ty[6:], {})[pt['asOfDate'][:4]] = pt['reportedValue']['raw']
            ys = sorted({y for v in rows.values() for y in v})[-5:]
            if ys:
                out[t] = {'y': [int(y) for y in ys]}
                for k, v in rows.items(): out[t][k] = [v.get(y) for y in ys]
        except Exception as e:
            print('fin', t, e)
        time.sleep(0.5)
    if len(out) < 5:
        print('fin: мало данных, не трогаем'); return
    save('fin.json', {'updated': NOW.strftime('%Y-%m-%dT%H:%MZ'), 'us': out}); print('fin', len(out))

# ---------- сводка недели ----------
def digest():
    m = load('markets.json')
    if not m: return
    snap = {'ru': {k: v.get('p') for k, v in (m.get('ru') or {}).items() if v and v.get('p')},
            'us': {k: v.get('p') for k, v in (m.get('us') or {}).items() if v and v.get('p')},
            'idx': {k: v.get('v') for k, v in (m.get('idx') or {}).items() if v and v.get('v')},
            'cr': {x['s']: x['p'] for x in (m.get('crypto') or []) if x.get('p')},
            'fx': {k: v['Value'] / v.get('Nominal', 1) for k, v in ((m.get('fx') or {}).get('Valute') or {}).items() if k in ('USD', 'EUR', 'CNY')}}
    H = load('digest_hist.json', {'days': {}}); H['days'][TODAY] = snap
    keep = sorted(H['days'])[-21:]; H['days'] = {k: H['days'][k] for k in keep}; save('digest_hist.json', H)
    base_d = None
    for d in sorted(H['days']):
        if (NOW - datetime.datetime.strptime(d, '%Y-%m-%d')).days >= 6: base_d = d
    if not base_d:
        ds = [d for d in sorted(H['days']) if d < TODAY]; base_d = ds[0] if ds else None
    base = H['days'].get(base_d) if base_d else None
    days = (NOW - datetime.datetime.strptime(base_d, '%Y-%m-%d')).days if base_d else 0
    def chg(g):
        out = []
        for k, v in snap[g].items():
            b = (base or {}).get(g, {}).get(k)
            if b: out.append({'k': k, 'p': v, 'c': (v / b - 1) * 100})
        return out
    names = {}
    if S:
        for r in S.RU: names[r[0]] = r[1]
        for r in S.US: names[r[0]] = r[1]
    for x in (m.get('crypto') or []): names[x['s']] = x.get('n', x['s'])
    names.update({'IMOEX': 'Индекс Мосбиржи', 'RTSI': 'Индекс РТС', 'RGBI': 'Индекс гособлигаций RGBI', 'MOEXOG': 'Нефть и газ', 'MOEXFN': 'Финансы', 'MOEXMM': 'Металлы и добыча', 'MOEXIT': 'IT'})
    res = {'updated': NOW.strftime('%Y-%m-%dT%H:%MZ'), 'base': base_d, 'days': days, 'names': names}
    for g in ('ru', 'us', 'idx', 'cr', 'fx'):
        a = sorted(chg(g), key=lambda x: -x['c']); res[g] = a
    n = load('news.json', {}); lim = (NOW - datetime.timedelta(days=7)).strftime('%Y-%m-%dT%H:%M')
    items = [x for x in n.get('items', []) if not x.get('dup') and (x.get('d') or '') >= lim]
    items.sort(key=lambda x: -(x.get('imp') or 0))
    res['news'] = [{'id': x['id'], 't': x['t'], 's': x.get('s'), 'd': x.get('d'), 'u': x.get('u'), 'x': ((x.get('sum') or [''])[0] or '')[:260], 'cl': x.get('cl', 1)} for x in items[:8]]
    ev = []
    if S:
        for e in S.CAL:
            if TODAY <= e[0] <= (NOW + datetime.timedelta(days=10)).strftime('%Y-%m-%d'): ev.append(list(e))
    res['events'] = ev
    cc = load('corp_cal.json', {}); lim2 = (NOW + datetime.timedelta(days=21)).strftime('%Y-%m-%d')
    res['divs'] = sorted([x for x in cc.get('items', []) if TODAY <= x['d'] <= lim2], key=lambda x: x['d'])
    save('digest.json', res); print('digest: база', base_d, 'дней', days, 'новостей', len(res['news']))

for f in (corp_cal, fin, digest):
    try: f()
    except Exception as e: print(f.__name__, 'упал:', e)
try:   # журнал для диагностики: логи Actions отсюда не видны
    open(os.path.join(HERE, 'extra_debug.txt'), 'w', encoding='utf-8').write(NOW.strftime('%Y-%m-%dT%H:%MZ') + '\n' + '\n'.join(_LOG[:60]) + '\n')
except Exception: pass
