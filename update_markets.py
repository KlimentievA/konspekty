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
    ('ПРАЙМ', 'ru', 'https://1prime.ru/export/rss2/index.xml'),
    ('ForkLog', 'crypto', 'https://forklog.com/feed'),
    ('Cointelegraph', 'crypto', 'https://cointelegraph.com/rss'),
    ('CoinDesk', 'crypto', 'https://www.coindesk.com/arc/outboundfeeds/rss/'),
]
# новости по каждой американской компании (лента Yahoo Finance по тикеру) — помечаются этим тикером
FEEDS += [('Yahoo Finance', 'us:' + t, 'https://feeds.finance.yahoo.com/rss/2.0/headline?s=' + t + '&region=US&lang=en-US') for t in US if not t.startswith('^')]
NAMES = {'SBER': ['Сбербанк', 'Сбер'], 'GAZP': ['Газпром'], 'LKOH': ['ЛУКОЙЛ', 'Лукойл'], 'ROSN': ['Роснефть', 'Роснефти'],
         'NVTK': ['НОВАТЭК', 'Новатэк'], 'GMKN': ['Норникел', '«Норильский никель»'], 'PLZL': ['«Полюс»', 'Полюса', 'Полюс '],
         'TATN': ['Татнефть', 'Татнефти'], 'SNGS': ['Сургутнефтегаз'], 'SIBN': ['Газпром нефть', 'Газпром нефти'],
         'YDEX': ['Яндекс'], 'X5': ['X5', 'Пятёрочк', 'Пятерочк'], 'MGNT': ['Магнит'], 'MTSS': ['МТС'], 'CHMF': ['Северстал'],
         'NLMK': ['НЛМК'], 'VTBR': ['ВТБ'], 'T': ['Т-Технологи', 'Т-Банк'], 'OZON': ['Ozon', 'Озон'], 'ALRS': ['АЛРОСА', 'Алроса'],
         'PHOR': ['ФосАгро'], 'AFLT': ['Аэрофлот'], 'MOEX': ['Мосбирж', 'Московская биржа', 'Московской бирж'], 'IRAO': ['Интер РАО'],
         'RUAL': ['Русал', 'РУСАЛ'], 'TRNFP': ['Транснефт'], 'POSI': ['Positive Technologies', 'Позитив'], 'HEAD': ['HeadHunter', 'Хэдхантер', 'hh.ru']}
# американские компании и крипта: ищем по словам целиком (латиница и русские названия)
NAMES_RX = {'AAPL': r'Apple|Эппл', 'MSFT': r'Microsoft|Майкрософт', 'NVDA': r'Nvidia|NVIDIA|Nvidia\'s|Нвидиа|Nvidia’s', 'AMZN': r'Amazon|Амазон',
    'GOOGL': r'Alphabet|Google|Гугл', 'META': r'Meta Platforms|Meta(?=\s|’|\'|,)|Facebook', 'TSLA': r'Tesla|Тесла', 'BRK-B': r'Berkshire|Баффет|Buffett',
    'AVGO': r'Broadcom', 'JPM': r'JPMorgan|JP Morgan|Dimon', 'LLY': r'Eli Lilly|Lilly', 'V': r'Visa(?! Waiver)', 'XOM': r'Exxon',
    'WMT': r'Walmart', 'MA': r'Mastercard', 'UNH': r'UnitedHealth', 'JNJ': r'Johnson & Johnson|J&J', 'PG': r'Procter', 'COST': r'Costco',
    'NFLX': r'Netflix', 'KO': r'Coca-Cola|Coca Cola', 'CVX': r'Chevron', 'BAC': r'Bank of America', 'AMD': r'AMD|Advanced Micro', 'ORCL': r'Oracle',
    'BTC': r'Bitcoin|биткоин|Биткоин|BTC', 'ETH': r'Ethereum|эфириум|Эфириум|ether(?:eum)?\b', 'SOL': r'Solana', 'XRP': r'XRP|Ripple', 'TON': r'Toncoin|TON\b',
    'DOGE': r'Dogecoin|DOGE', 'BNB': r'BNB|Binance Coin', 'USDT': r'Tether|USDT',
    '^GSPC': r'S&P 500|S&P|Wall Street|Уолл-стрит|американск[а-я]+ (?:рын|бирж|акци)', '^IXIC': r'Nasdaq|Насдак', '^DJI': r'Dow Jones|Dow(?= )|Доу-Джонс'}
NAMES_RX = {k: re.compile(r'(?<![A-Za-zА-Яа-яЁё])(?:' + v + r')(?![a-zа-яё])') for k, v in NAMES_RX.items()}
def tags_of(title):
    return [k for k, v in NAMES.items() if any(n in title for n in v)] + [k for k, r in NAMES_RX.items() if r.search(title)]
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
            ft = [cat[3:]] if cat.startswith('us:') else []
            tags = sorted(set(tags_of(title)) | set(ft))
            x = {'t': title, 'u': link, 's': src, 'cat': cat[:2] if ft else cat, 'd': d, 'x': desc[:220], 'tags': tags}
            if ft: x['ft'] = ft
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
    x['tags'] = sorted(set(tags_of(x['t'])) | set(tags_of(x.get('to', ''))) | set(x.get('ft', [])))
    if 'sum' not in x and k in oldby and 'sum' in oldby[k]: x['sum'] = oldby[k]['sum']
    merged.append(x)
merged = merged[:2000]

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
            if len(sents) >= 7 or sum(len(q) for q in sents) > 1100: return sents
    return sents
CYR = re.compile('[А-Яа-яЁё]')
def tr(text):
    """Автоперевод англоязычных новостей на русский (публичный эндпоинт Google Translate)."""
    j = json.loads(urllib.request.urlopen(urllib.request.Request('https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=ru&dt=t&q=' + urllib.parse.quote(text[:4500]), headers=UA), timeout=15).read().decode('utf-8'))
    out = ''.join(seg[0] for seg in j[0] if seg and seg[0])
    if not out.strip(): raise ValueError('empty')
    return out
def tr_list(a):
    if not a: return a
    t_ = tr('\n'.join(a)).split('\n')
    return [q.strip() for q in t_ if q.strip()] if len(t_) >= 1 else a
cut30 = (now_ - datetime.timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%SZ')
done = 0
for x in merged:
    x['id'] = hashlib.md5(x['u'].split('?')[0].encode()).hexdigest()[:10]
    if done >= 160: continue
    if x.get('sv', 1) >= 2 and (x.get('sum') or x.get('st', 0) >= 3): continue
    if x.get('sum') and x.get('sv', 1) < 2 and (x['d'] < cut30 or x.get('st2', 0) >= 2): continue   # старые короткие не трогаем
    s_ = summarize(x['u'], x.get('to') or x['t'], x.get('x', ''))
    if not s_ and x.get('x') and len(x['x']) > 40:   # сайт не отдал статью — берём анонс из RSS
        s_ = [q for q in SPLIT.split(x['x']) if len(q) > 30][:3]
    if x.get('sum') and len(' '.join(s_)) <= len(' '.join(x['sum'])):   # новая версия не подробнее — оставляем старую
        x['st2'] = x.get('st2', 0) + 1; done += 1; continue
    if s_ and x.get('tr'):
        try: s_ = tr_list(s_)
        except Exception: pass
    x['sum'] = s_; x['st'] = x.get('st', 0) + 1; x['sv'] = 2; done += 1
    time.sleep(0.3)
print('summaries', done)
# перевод англоязычных заголовков и сути
nt = 0
for x in merged:
    if nt >= 220: break
    if x.get('tr') or x.get('trt', 0) >= 3 or CYR.search(x['t']): continue
    try:
        t_ = tr(x['t'])
        s_ = tr_list(x['sum']) if x.get('sum') else x.get('sum')
        x['to'] = x['t']; x['t'] = t_; x['sum'] = s_; x['tr'] = 1; nt += 1
        time.sleep(0.15)
    except Exception as e:
        x['trt'] = x.get('trt', 0) + 1
        print('translate', e, file=sys.stderr)
print('translated', nt)
for x in merged:   # старые новости (нужны только для причин на графиках) — суть покороче, чтобы файл не разрастался
    if x['d'] < cut30 and x.get('sum') and len(x['sum']) > 2: x['sum'] = x['sum'][:2]
json.dump({'updated': out['updated'], 'items': merged}, open('news.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print('news', len(items), 'new,', len(merged), 'kept')
