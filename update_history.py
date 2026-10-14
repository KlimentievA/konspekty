#!/usr/bin/env python3
"""История цен для карточек (США, индексы США, крипта) → папка OUT/hist/*.json.
Запускается GitHub Action'ом; файлы уходят в отдельную ветку `data` (перезаписывается, история не копится).
Обновляет файл, если он старше 20 часов. Формат: {"name", "updated", "d": [[день, цена], …] (1 год по дням), "w": [[день, цена], …] (5 лет по неделям)}; день = дни с 1970-01-01."""
import json, os, sys, time, urllib.request, urllib.parse, datetime

OUT = sys.argv[1] if len(sys.argv) > 1 else 'hist_out'
os.makedirs(os.path.join(OUT, 'hist'), exist_ok=True)
UA = {'User-Agent': 'Mozilla/5.0 (konspekty history)'}
US = ['NVDA', 'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META', 'AVGO', 'TSLA', 'BRK-B', 'LLY', 'AMD', 'WMT', 'JPM', 'V', 'XOM', 'JNJ', 'MA',
      'COST', 'CVX', 'ORCL', 'KO', 'BAC', 'PG', 'UNH', 'NFLX', '^GSPC', '^IXIC', '^DJI']
CR = {'BTC': 'bitcoin', 'ETH': 'ethereum', 'SOL': 'solana', 'XRP': 'ripple', 'BNB': 'binancecoin', 'DOGE': 'dogecoin',
      'TON': 'the-open-network', 'ADA': 'cardano', 'TRX': 'tron', 'USDT': 'tether'}
YCR = {'TON': 'TON11419-USD'}

def get(url, t=25):
    return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=t).read().decode('utf-8'))
def fname(key): return os.path.join(OUT, 'hist', key.replace('^', '_') + '.json')
def fresh(key):
    try:
        u = json.load(open(fname(key))).get('updated', '')
        return (datetime.datetime.utcnow() - datetime.datetime.strptime(u, '%Y-%m-%dT%H:%MZ')).total_seconds() < 6 * 3600
    except Exception:
        return False
def day(ts): return int(ts // 86400)
def stamp(): return datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%MZ')

def yahoo(t):
    res = {}
    for rng, iv, k in (('1y', '1d', 'd'), ('5y', '1wk', 'w')):
        j = get('https://query1.finance.yahoo.com/v8/finance/chart/' + urllib.parse.quote(t) + '?range=' + rng + '&interval=' + iv)
        r = j['chart']['result'][0]
        ts, cl = r['timestamp'], r['indicators']['quote'][0]['close']
        res[k] = [[day(a), round(b, 6 if b < 1 else 2)] for a, b in zip(ts, cl) if b is not None]
        res['name'] = r['meta'].get('longName') or r['meta'].get('shortName') or t
        time.sleep(0.4)
    res['updated'] = stamp()
    return res

changed = 0
for t in US:
    key = 'us-' + t
    if fresh(key): continue
    try:
        json.dump(yahoo(t), open(fname(key), 'w'), separators=(',', ':')); changed += 1
    except Exception as e:
        print('yahoo', t, e, file=sys.stderr)

for sym, cid in CR.items():
    key = 'cr-' + sym
    if fresh(key): continue
    try:
        j = get('https://api.coingecko.com/api/v3/coins/' + cid + '/market_chart?vs_currency=usd&days=1825&interval=daily')
        pr = [[day(a / 1000), round(b, 6 if b < 1 else 2)] for a, b in j['prices']]
        res = {'name': sym, 'd': pr[-366:], 'w': pr[::7] + ([pr[-1]] if pr and (len(pr) - 1) % 7 else []), 'updated': stamp()}
        json.dump(res, open(fname(key), 'w'), separators=(',', ':')); changed += 1
        time.sleep(3)
    except Exception as e:
        print('coingecko', sym, e, file=sys.stderr)
        try:  # запасной источник — Yahoo (BTC-USD и т.п.)
            res = yahoo(YCR.get(sym, sym + '-USD')); res['name'] = sym
            json.dump(res, open(fname(key), 'w'), separators=(',', ':')); changed += 1
        except Exception as e2:
            print('yahoo crypto', sym, e2, file=sys.stderr)

print('history updated', changed)
open(os.path.join(OUT, '.changed'), 'w').write(str(changed))
