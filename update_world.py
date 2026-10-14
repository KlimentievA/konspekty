#!/usr/bin/env python3
"""Макроданные по странам мира → world.json (карта «Мир» на finance.html#world). Запускается из scripts/update_all.sh.
Источник 1 — IMF DataMapper API (World Economic Outlook: факт + прогноз МВФ на 5 лет вперёд);
источник 2 — World Bank API: если МВФ не ответил по показателю, и чтобы заполнить страны, которых у МВФ нет (Куба, КНДР…).
Обновляет раз в сутки: если world.json моложе 20 часов — ничего не делает (WORLD_FORCE=1 — обновить принудительно).
Если всё упало — старый world.json не трогаем, выходим с кодом 0."""
import json, os, sys, time, datetime, urllib.request, urllib.error

OUT = 'world.json'
IMF = os.environ.get('WORLD_IMF_URL') or 'https://www.imf.org/external/datamapper/api/v1/'   # переменные — только для проверки на копии API
WB = (os.environ.get('WORLD_WB_URL') or 'https://api.worldbank.org/v2/') + 'country/all/indicator/%s?format=json&date=2000:%d&per_page=20000'
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36',
      'Accept': 'application/json,text/plain,*/*', 'Accept-Language': 'en-US,en;q=0.9',
      'Referer': 'https://www.imf.org/external/datamapper/NGDPD@WEO/OEMDC/ADVEC/WEOWORLD', 'Origin': 'https://www.imf.org'}
FIRST = 2000

# код МВФ: (название, единица, код Всемирного банка, множитель WB → единица МВФ)
IND = {
    'NGDPD':       ('ВВП', 'млрд $', 'NY.GDP.MKTP.CD', 1e-9),
    'PPPGDP':      ('ВВП (ППС)', 'млрд межд. $', 'NY.GDP.MKTP.PP.CD', 1e-9),
    'NGDPDPC':     ('ВВП на душу', '$', 'NY.GDP.PCAP.CD', 1),
    'PPPPC':       ('ВВП на душу (ППС)', 'межд. $', 'NY.GDP.PCAP.PP.CD', 1),
    'NGDP_RPCH':   ('Рост ВВП', '%', 'NY.GDP.MKTP.KD.ZG', 1),
    'PCPIPCH':     ('Инфляция', '%', 'FP.CPI.TOTL.ZG', 1),
    'LUR':         ('Безработица', '%', 'SL.UEM.TOTL.ZS', 1),
    'GGXWDG_NGDP': ('Госдолг', '% ВВП', 'GC.DOD.TOTL.GD.ZS', 1),
    'BCA_NGDPD':   ('Счёт текущих операций', '% ВВП', 'BN.CAB.XOKA.GD.ZS', 1),
    'LP':          ('Население', 'млн', 'SP.POP.TOTL', 1e-6),
}
# агрегаты МВФ, которые сохраняем (код МВФ → ключ в world.json, название)
AGG = {'WEOWORLD': ('WORLD', 'Мир'), 'ADVEC': ('ADVEC', 'Развитые экономики'), 'OEMDC': ('OEMDC', 'Развивающиеся рынки'),
       'EU': ('EU', 'Евросоюз'), 'EURO': ('EURO', 'Еврозона'), 'MAE': ('MAE', 'Крупные развитые (G7)'),
       'DA': ('DA', 'Развивающаяся Азия'), 'EME': ('EME', 'Развивающаяся Европа'), 'LAC': ('LAC', 'Латинская Америка'),
       'MECA': ('MECA', 'Ближний Восток и Центр. Азия'), 'SSA': ('SSA', 'Африка южнее Сахары')}
FIX = {'WBG': 'PSE'}   # у МВФ «Западный берег и Газа» = PSE в ISO; Косово (UVK) на карте без кода — пропускаем

now = datetime.datetime.now(datetime.timezone.utc)


LOGL = []
def log(*a):
    print(*a, file=sys.stderr, flush=True)
    LOGL.append(' '.join(str(x) for x in a)[:300])
    try: open('world_debug.txt', 'w', encoding='utf-8').write('\n'.join(LOGL[-60:]) + '\n')
    except Exception: pass


def get(url, t=40, tries=3):
    err = None
    for i in range(tries):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=t)
            return json.loads(r.read().decode('utf-8'))
        except Exception as e:
            err = e
            if isinstance(e, urllib.error.HTTPError) and e.code in (400, 404): break
            if i < tries - 1: time.sleep(2 + 3 * i)
    raise err


def rnd(v):
    if v is None: return None
    try: v = float(v)
    except (TypeError, ValueError): return None
    if v != v or v in (float('inf'), float('-inf')): return None
    a = abs(v)
    r = round(v, 3 if a < 1 else 2 if a < 100 else 1 if a < 10000 else 0)
    return int(r) if r == int(r) and a >= 10000 else r


def load_old():
    try: return json.load(open(OUT, encoding='utf-8'))
    except Exception: return None


old = load_old()
if old and os.environ.get('WORLD_FORCE') != '1':
    try:
        age = (now - datetime.datetime.fromisoformat(old['updated'].replace('Z', '+00:00'))).total_seconds() / 3600
        if age < 20 and old.get('weo'):
            print('world.json свежий (%.1f ч) — пропускаю; WORLD_FORCE=1 — обновить принудительно' % age); sys.exit(0)
    except Exception: pass

# какие страны есть на карте (чтобы отсеять агрегаты Всемирного банка: «Мир», «Еврозона», «Страны с высоким доходом»…)
GEO = set()
try:
    for g in json.load(open('world/countries.json', encoding='utf-8'))['objects']['countries']['geometries']:
        if g.get('id'): GEO.add(g['id'])
except Exception as e: log('world/countries.json:', e)

# ---- МВФ ----
imf, imf_dead, fails = {}, False, 0
countries = set()
try:
    countries = {FIX.get(k, k) for k in get(IMF + 'countries', 30).get('countries', {})}
except Exception as e:
    log('IMF countries:', e); fails += 1
for code in IND:
    if imf_dead: break
    try:
        v = get(IMF + code, 60).get('values', {}).get(code) or {}
        if not v: raise ValueError('пустой ответ')
        imf[code] = {FIX.get(k, k): s for k, s in v.items()}
        fails = 0
    except Exception as e:
        log('IMF', code, e); fails += 1
        if fails >= 3: imf_dead = True; log('МВФ не отвечает — дальше только Всемирный банк')

# ---- запасной путь: зеркало WEO на DBnomics (МВФ режет запросы с серверов GitHub — 403) ----
if len(imf) < len(IND) // 2:
    DBN = 'https://api.db.nomics.world/v22/'
    try:
        import re, urllib.parse
        ed, probe = None, None
        for y_ in range(now.year, now.year - 2, -1):
            for m_ in ('10', '04'):
                try:
                    pr = get(DBN + 'series/IMF/WEO:%d-%s?limit=1&observations=0' % (y_, m_), 40)
                    if (pr.get('series') or {}).get('docs'): ed, probe = 'WEO:%d-%s' % (y_, m_), pr; break
                except Exception as e: log('DBnomics WEO:%d-%s' % (y_, m_), e)
            if ed: break
        if not ed: raise ValueError('нет выпусков WEO')
        order = (probe.get('dataset') or {}).get('dimensions_codes_order') or []
        sk = next((k for k in order if 'subject' in k.lower()), None)
        ck = next((k for k in order if 'country' in k.lower()), None)
        log('DBnomics', ed, 'измерения', order)
        if not sk or not ck: raise ValueError('не нашёл измерения')
        for code in IND:
            res = {}
            off = 0
            while True:
                q = urllib.parse.urlencode({'dimensions': json.dumps({sk: [code]}), 'observations': 1, 'limit': 1000, 'offset': off})
                j = get(DBN + 'series/IMF/%s?%s' % (ed, q), 60)
                ser = j.get('series') or {}
                dd = ser.get('docs') or []
                for d in dd:
                    c = FIX.get((d.get('dimensions') or {}).get(ck) or '', (d.get('dimensions') or {}).get(ck) or '')
                    per, val = d.get('period') or [], d.get('value') or []
                    m = {str(a): b for a, b in zip(per, val) if isinstance(b, (int, float))}
                    if c and m: res[c] = m
                off += len(dd)
                if not dd or off >= (ser.get('num_found') or 0): break
            if res:
                imf[code] = res
                log('DBnomics', code, len(res), 'стран')
        if imf:
            m_, y_ = ed.split(':')[1].split('-')
            os.environ.setdefault('WEO_EDITION', ('апрель' if m_ == '04' else 'октябрь') + ' ' + y_)
    except Exception as e:
        log('DBnomics:', e)

last_year = max([int(y) for s in imf.values() for c in s.values() for y in c] or [now.year])
LAST = min(max(last_year, now.year), now.year + 6)
YEARS = list(range(FIRST, LAST + 1))

# ---- Всемирный банк: показатели, которых нет у МВФ, и страны, которых нет у МВФ ----
wb, wb_dead, wfails = {}, False, 0
for code, (_, _, wcode, k) in IND.items():
    if wb_dead: break
    try:
        j = get(WB % (wcode, now.year), 60)
        rows = j[1] if isinstance(j, list) and len(j) > 1 and j[1] else []
        if not rows: raise ValueError('пустой ответ')
        d = {}
        for r in rows:
            c = r.get('countryiso3code') or ''
            if r.get('value') is None or len(c) != 3 or (GEO and c not in GEO): continue
            d.setdefault(c, {})[str(r['date'])] = r['value'] * k
        wb[code] = d; wfails = 0
    except Exception as e:
        log('WB', wcode, e); wfails += 1
        if wfails >= 3: wb_dead = True; log('Всемирный банк не отвечает')

if not imf and not wb:
    print('Нет связи ни с МВФ, ни со Всемирным банком — world.json не трогаю'); sys.exit(0)


def arr(series):
    return [rnd(series.get(str(y))) for y in YEARS]


def is_country(k):
    if k in AGG: return False
    if countries: return k in countries or k in GEO
    return len(k) == 3 and (not GEO or k in GEO)


data, agg, src, filled = {}, {}, {}, set()
old_years = (old or {}).get('years') or []
for code in IND:
    if code in imf:
        src[code] = 'IMF'
        for k, s in imf[code].items():
            if k in AGG: agg.setdefault(AGG[k][0], {})[code] = arr(s)
            elif is_country(k) and any(s.get(str(y)) is not None for y in YEARS): data.setdefault(k, {})[code] = arr(s)
        for k, s in wb.get(code, {}).items():   # страны, которых у МВФ нет
            if k not in data or code not in data[k]:
                data.setdefault(k, {})[code] = arr(s); filled.add(k)
    elif code in wb:
        src[code] = 'WB'
        for k, s in wb[code].items(): data.setdefault(k, {})[code] = arr(s)
    elif old and code in (old.get('ind') or {}):   # показатель не пришёл ниоткуда — берём из прошлого файла
        src[code] = 'old'
        for k, row in (old.get('data') or {}).items():
            if row.get(code):
                m = dict(zip(old_years, row[code])); data.setdefault(k, {})[code] = [m.get(y) for y in YEARS]
        for k, row in (old.get('agg') or {}).items():
            if row.get(code):
                m = dict(zip(old_years, row[code])); agg.setdefault(k, {})[code] = [m.get(y) for y in YEARS]

if not data:
    print('Данные пришли пустыми — world.json не трогаю'); sys.exit(0)
if 'WORLD' not in agg:   # нет мирового агрегата МВФ — считаем сумму по странам
    w = {}
    for code in ('NGDPD', 'PPPGDP', 'LP'):
        if code in src:
            w[code] = [rnd(sum(r[code][i] for r in data.values() if r.get(code) and r[code][i] is not None) or None) for i in range(len(YEARS))]
    if w: agg['WORLD'] = w

# выпуск WEO: апрельский выходит в середине апреля, октябрьский — в середине октября (можно задать WEO_EDITION)
d = now.date()
if (d.month, d.day) >= (10, 14): ed_m, ed_y = 'октябрь', d.year
elif (d.month, d.day) >= (4, 14): ed_m, ed_y = 'апрель', d.year
else: ed_m, ed_y = 'октябрь', d.year - 1
weo = os.environ.get('WEO_EDITION') or '%s %d' % (ed_m, ed_y)
last_actual = ed_y - 1
srcs = set(src.values())
out = {
    'updated': now.strftime('%Y-%m-%dT%H:%M:%SZ'),
    'source': ('МВФ, World Economic Outlook' if 'IMF' in srcs else 'Всемирный банк, WDI') + (' + Всемирный банк (WDI)' if 'IMF' in srcs and ('WB' in srcs or filled) else ''),
    'weo': weo if 'IMF' in srcs else None,
    'last_actual': last_actual if 'IMF' in srcs else min(now.year - 1, LAST),
    'ind': {k: {'name': v[0], 'unit': v[1], 'src': src[k]} for k, v in IND.items() if k in src},
    'years': YEARS,
    'data': {k: data[k] for k in sorted(data)},
    'agg': agg,
    'agg_names': {v[0]: v[1] for v in AGG.values() if v[0] in agg} or {'WORLD': 'Мир'},
}
if filled: out['wb_fill'] = sorted(filled)
tmp = OUT + '.tmp'
json.dump(out, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
os.replace(tmp, OUT)
print('world.json: %d стран, %d показателей (%s), годы %d–%d, %d КБ' % (len(data), len(src), ', '.join('%s:%s' % kv for kv in src.items()), FIRST, LAST, os.path.getsize(OUT) // 1024))
