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

try:
    out['fx'] = get('https://www.cbr-xml-daily.ru/daily_json.js')
except Exception as e:
    print('cbr', e, file=sys.stderr); out['fx'] = old.get('fx')

try:
    a = get('https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=25&page=1&price_change_percentage=24h,7d')
    out['crypto'] = [{'s': x['symbol'].upper(), 'n': x['name'], 'p': x['current_price'], 'c24': x.get('price_change_percentage_24h_in_currency'),
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

# ---------------- новости (RSS) → news.json ----------------
import re, html, email.utils
import xml.etree.ElementTree as ET
FEEDS = [
    ('Интерфакс', 'ru', 'https://www.interfax.ru/rss.asp'),
    ('РБК', 'ru', 'https://rssexport.rbc.ru/rbcnews/news/30/full.rss'),
    ('Ведомости', 'ru', 'https://www.vedomosti.ru/rss/news'),
    ('Коммерсантъ', 'ru', 'https://www.kommersant.ru/RSS/news.xml'),
    ('ТАСС', 'ru', 'https://tass.ru/rss/v2.xml'),
    ('Банк России', 'cbr', 'https://www.cbr.ru/rss/RssPress'),
    ('CNBC', 'world', 'https://www.cnbc.com/id/10000664/device/rss/rss.html'),
    ('MarketWatch', 'world', 'https://feeds.content.dowjones.io/public/rss/mw_topstories'),
]
NAMES = {'SBER': ['Сбербанк', 'Сбер'], 'GAZP': ['Газпром'], 'LKOH': ['ЛУКОЙЛ', 'Лукойл'], 'ROSN': ['Роснефть', 'Роснефти'],
         'NVTK': ['НОВАТЭК', 'Новатэк'], 'GMKN': ['Норникел', '«Норильский никель»'], 'PLZL': ['«Полюс»', 'Полюса', 'Полюс '],
         'TATN': ['Татнефть', 'Татнефти'], 'SNGS': ['Сургутнефтегаз'], 'SIBN': ['Газпром нефть', 'Газпром нефти'],
         'YDEX': ['Яндекс'], 'X5': ['X5', 'Пятёрочк', 'Пятерочк'], 'MGNT': ['Магнит'], 'MTSS': ['МТС'], 'CHMF': ['Северстал'],
         'NLMK': ['НЛМК'], 'VTBR': ['ВТБ'], 'T': ['Т-Технологи', 'Т-Банк'], 'OZON': ['Ozon', 'Озон'], 'ALRS': ['АЛРОСА', 'Алроса'],
         'PHOR': ['ФосАгро'], 'AFLT': ['Аэрофлот'], 'MOEX': ['Мосбирж', 'Московская биржа', 'Московской бирж'], 'IRAO': ['Интер РАО'],
         'RUAL': ['Русал', 'РУСАЛ'], 'TRNFP': ['Транснефт'], 'POSI': ['Positive Technologies', 'Позитив'], 'HEAD': ['HeadHunter', 'Хэдхантер', 'hh.ru']}
FIN = re.compile(r'(?<![А-Яа-яЁёA-Za-z])(акци[йияюе](?! протест)(?! памяти)(?! в поддержку)|бирж|рубл[ья]|ставк|ЦБ|Банк[а-я]* России|нефт|газа?(?![а-я])|дивиденд|облигац|ОФЗ|инфляц|бюджет|IPO|SPO|санкц|прибыль|чист[а-я]+ прибыл|выручк|МСФО|сделк|ВВП|курс[аеу]? (?:доллар|рубл|юан|евро)|доллар|юан|индекс[а-я]* Мосбирж|Мосбирж|экспорт|налог|Минфин|ФРС|Brent|Urals|золот[оа](?![а-я])|инвест|капитализац|госдолг|ипотек|котировк|размещени|эмисси|банкротств|M&A|слияни|поглощени)', re.I)
def keep(x):
    if x['cat'] == 'world':
        return not re.search(r"\bMy \b|^‘|\bI \b|\bwife\b|\bhusband\b|\bsister\b|\bbrother\b", x['t'])
    return x['cat'] != 'ru' or x.get('tags') or FIN.search(x['t'])
def txt(el, tag):
    x = el.find(tag)
    return html.unescape(re.sub(r'<[^>]+>', ' ', x.text or '')).strip() if x is not None and x.text else ''
def when(s):
    try: return email.utils.parsedate_to_datetime(s).astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    except Exception: return None
items = []
for src, cat, url in FEEDS:
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20).read()
        root = ET.fromstring(r)
        for it in root.iter('item'):
            title, link = txt(it, 'title'), txt(it, 'link')
            desc = txt(it, 'description')[:400]
            d = when(txt(it, 'pubDate'))
            if not title or not link or not d: continue
            blob = title + ' ' + desc
            tags = [k for k, v in NAMES.items() if any(n in blob for n in v)]
            tags = [k for k, v in NAMES.items() if any(n in title for n in v)]
            x = {'t': title, 'u': link, 's': src, 'cat': cat, 'd': d, 'x': desc[:220], 'tags': tags}
            if keep(x): items.append(x)
    except Exception as e:
        print('rss', src, e, file=sys.stderr)
try: oldn = json.load(open('news.json')).get('items', [])
except Exception: oldn = []
seen, merged = set(), []
now_ = datetime.datetime.now(datetime.timezone.utc)
cut = (now_ - datetime.timedelta(days=10)).strftime('%Y-%m-%dT%H:%M:%SZ')
cut_tag = (now_ - datetime.timedelta(days=400)).strftime('%Y-%m-%dT%H:%M:%SZ')  # новости о компаниях храним год — по ним объясняются скачки на графиках
oldby = {x['u'].split('?')[0]: x for x in oldn}
for x in sorted(items + oldn, key=lambda x: x['d'], reverse=True):
    k = x['u'].split('?')[0]
    if k in seen or not keep(x) or x['d'] < (cut_tag if x.get('tags') else cut): continue
    seen.add(k)
    if 'sum' not in x and k in oldby and 'sum' in oldby[k]: x['sum'] = oldby[k]['sum']
    merged.append(x)
merged = merged[:1500]

# ---- суть статьи: 2–3 первых содержательных предложения (не полный текст), со ссылкой на источник ----
import hashlib
from html.parser import HTMLParser
class P(HTMLParser):
    def __init__(s):
        super().__init__(); s.ps = []; s.cur = None; s.skip = 0; s.meta = {}
    def handle_starttag(s, tag, a):
        a = dict(a)
        if tag in ('script', 'style', 'noscript', 'figcaption', 'aside', 'nav', 'footer'): s.skip += 1
        if tag == 'meta' and (a.get('property') in ('og:description',) or a.get('name') in ('description',)): s.meta.setdefault('d', a.get('content') or '')
        if tag == 'p' and not s.skip: s.cur = []
    def handle_endtag(s, tag):
        if tag in ('script', 'style', 'noscript', 'figcaption', 'aside', 'nav', 'footer') and s.skip: s.skip -= 1
        if tag == 'p' and s.cur is not None:
            txt_ = re.sub(r'\s+', ' ', ''.join(s.cur)).strip()
            if txt_: s.ps.append(txt_)
            s.cur = None
    def handle_data(s, d):
        if s.cur is not None and not s.skip: s.cur.append(d)
JUNK = re.compile(r'Фото|Читайте также|Подписывайтесь|подписаться|Реклама|cookie|Telegram|Читать далее|Все права|©|Нашли ошибку|Sign up|Subscribe|newsletter|Advertisement', re.I)
SPLIT = re.compile(r'(?<=[.!?…])\s+(?=[«"А-ЯЁA-Z0-9])')
def summarize(url, title, desc):
    sents = []
    try:
        raw = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=12).read().decode('utf-8', 'ignore')
        pp = P(); pp.feed(raw)
        cands = ([html.unescape(pp.meta.get('d', ''))] if pp.meta.get('d') else []) + [html.unescape(x) for x in pp.ps]
    except Exception:
        cands = [desc] if desc else []
    tw = set(re.findall(r'\w+', title.lower()))
    def same(s_):
        w = set(re.findall(r'\w+', s_.lower()))
        return w and len(w & tw) / len(w) > 0.6
    for para in cands:
        para = para.strip()
        if len(para) < 50 or JUNK.search(para): continue
        for snt in SPLIT.split(para):
            snt = snt.strip()
            if len(snt) < 40 or len(snt) > 320 or same(snt): continue
            if any(snt[:50] == q[:50] for q in sents): continue
            sents.append(snt)
            if len(sents) >= 3 or sum(len(q) for q in sents) > 520: return sents
    return sents
done = 0
for x in merged:
    x['id'] = hashlib.md5(x['u'].split('?')[0].encode()).hexdigest()[:10]
    if 'sum' in x or done >= 90: continue
    x['sum'] = summarize(x['u'], x['t'], x.get('x', '')); done += 1
    time.sleep(0.3)
print('summaries', done)
json.dump({'updated': out['updated'], 'items': merged}, open('news.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print('news', len(items), 'new,', len(merged), 'kept')
