#!/usr/bin/env python3
"""Снимок рынков → markets.json (запускается GitHub Action'ом).
Страница finance.html берёт живые данные прямо из браузера, а этот файл —
запасной вариант и единственный источник цен по США (у бесплатных американских
котировок нет доступа из браузера)."""
import json, urllib.request, urllib.parse, datetime, time, sys

UA = {'User-Agent': 'Mozilla/5.0 (konspekty markets snapshot)'}
RU = ['SBER','LKOH','ROSN','NVTK','SIBN','GAZP','GMKN','TATN','PLZL','YDEX','TRNFP','SNGS','T','VTBR','OZON','PHOR',
      'CHMF','X5','NLMK','RUAL','MOEX','MTSS','IRAO','MGNT','ALRS','HEAD','AFLT','POSI']
US = ['NVDA','AAPL','GOOGL','MSFT','AMZN','META','AVGO','TSLA','BRK-B','LLY','AMD','WMT','JPM','V','XOM','JNJ','MA',
      'COST','CVX','ORCL','KO','BAC','PG','UNH','NFLX','^GSPC','^IXIC','^DJI']

def get(url, t=20):
    r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=t)
    return json.loads(r.read().decode('utf-8'))

def iss(block):
    return {row[block['columns'].index('SECID')]: dict(zip(block['columns'], row)) for row in block['data']}

out = {'updated': datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).strftime('%d.%m.%Y %H:%M МСК')}
old = {}
try: old = json.load(open('markets.json'))
except Exception: pass

try:
    j = get('https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities.json?iss.meta=off'
            '&iss.only=securities,marketdata&securities.columns=SECID,PREVPRICE&marketdata.columns=SECID,LAST,LASTTOPREVPRICE,UPDATETIME'
            '&securities=' + ','.join(RU))
    s, m = iss(j['securities']), iss(j['marketdata'])
    out['ru'] = {}
    for k, a in s.items():
        b = m.get(k, {}); p = b.get('LAST') or a.get('PREVPRICE')
        out['ru'][k] = {'p': p, 'ch': b.get('LASTTOPREVPRICE') if b.get('LAST') else None, 'tm': b.get('UPDATETIME')}
except Exception as e:
    print('moex shares', e, file=sys.stderr); out['ru'] = old.get('ru')

try:
    j = get('https://iss.moex.com/iss/engines/stock/markets/index/securities.json?iss.meta=off&iss.only=marketdata'
            '&marketdata.columns=SECID,CURRENTVALUE,LASTCHANGEPRC,UPDATETIME&securities=IMOEX,RTSI,RGBI,MOEXOG,MOEXFN,MOEXMM,MOEXIT')
    out['idx'] = {k: {'v': v['CURRENTVALUE'], 'ch': v['LASTCHANGEPRC'], 'tm': v['UPDATETIME']} for k, v in iss(j['marketdata']).items()}
except Exception as e:
    print('moex idx', e, file=sys.stderr); out['idx'] = old.get('idx')

out['bonds'] = {}
for kind, board in (('ofz', 'TQOB'), ('corp', 'TQCB')):
    try:
        j = get('https://iss.moex.com/iss/engines/stock/markets/bonds/boards/' + board + '/securities.json?iss.meta=off&iss.only=securities,marketdata'
                '&securities.columns=SECID,SHORTNAME,MATDATE,OFFERDATE,COUPONPERCENT,COUPONPERIOD,PREVPRICE,FACEUNIT,FACEVALUE,YIELDATPREVWAPRICE,LISTLEVEL'
                '&marketdata.columns=SECID,LAST,YIELD,DURATION,VALTODAY,UPDATETIME', 40)
        s, m = iss(j['securities']), iss(j['marketdata'])
        a_ = []
        for k, x in s.items():
            if kind == 'ofz' and not k.startswith(('SU24', 'SU25', 'SU26')): continue
            y = m.get(k, {})
            a_.append({'id': k, 'n': x.get('SHORTNAME'), 'mat': x.get('MATDATE'), 'off': x.get('OFFERDATE'), 'c': x.get('COUPONPERCENT'), 'per': x.get('COUPONPERIOD'),
                       'p': y.get('LAST') or x.get('PREVPRICE'), 'y': y.get('YIELD') or x.get('YIELDATPREVWAPRICE'), 'd': (y.get('DURATION') or 0) / 365 or None,
                       'vol': y.get('VALTODAY') or 0, 'cur': x.get('FACEUNIT'), 'fv': x.get('FACEVALUE'), 'lvl': x.get('LISTLEVEL')})
        if kind == 'corp': a_ = sorted(a_, key=lambda z: z['vol'] or 0, reverse=True)[:600]
        out['bonds'][kind] = a_
    except Exception as e:
        print('bonds', kind, e, file=sys.stderr)
        out['bonds'][kind] = (old.get('bonds') or {}).get(kind)
try:
    j = get('https://iss.moex.com/iss/engines/stock/zcyc.json?iss.meta=off&iss.only=yearyields&yearyields.columns=tradedate,tradetime,period,value')
    last = {}
    for r in j['yearyields']['data']: last[r[2]] = r
    pts = [[p_, last[p_][3]] for p_ in sorted(last) if p_ >= 0.5]
    r0 = j['yearyields']['data'][-1]
    out['kbd'] = {'date': r0[0] + ' ' + str(r0[1] or '')[:5] + ' (снимок)', 'pts': pts}
except Exception as e:
    print('kbd', e, file=sys.stderr); out['kbd'] = old.get('kbd')

try:
    out['fx'] = get('https://www.cbr-xml-daily.ru/daily_json.js')
except Exception as e:
    print('cbr', e, file=sys.stderr); out['fx'] = old.get('fx')

try:
    a = get('https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=25&page=1&price_change_percentage=24h,7d')
    out['crypto'] = [{'s': x['symbol'].upper(), 'id': x['id'], 'n': x['name'], 'p': x['current_price'], 'c24': x.get('price_change_percentage_24h_in_currency'),
                      'c7': x.get('price_change_percentage_7d_in_currency'), 'cap': x.get('market_cap'), 'vol': x.get('total_volume')} for x in a]
except Exception as e:
    print('coingecko', e, file=sys.stderr); out['crypto'] = old.get('crypto')

us = {}
for t in US:
    try:
        j = get('https://query1.finance.yahoo.com/v8/finance/chart/' + urllib.parse.quote(t) + '?range=5d&interval=1d')
        meta = j['chart']['result'][0]['meta']
        p, pc = meta.get('regularMarketPrice'), meta.get('chartPreviousClose') or meta.get('previousClose')
        us[t] = {'p': p, 'ch': (p / pc - 1) * 100 if p and pc else None}
    except Exception as e:
        print('yahoo', t, e, file=sys.stderr)
    time.sleep(0.4)
out['us'] = us or old.get('us') or {}

json.dump(out, open('markets.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print('ok', {k: (len(v) if hasattr(v, '__len__') else v) for k, v in out.items()})
