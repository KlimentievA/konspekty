"""Общие функции для новостей: суть статьи, автоперевод, расшифровка ссылок Google Новостей."""
import json, re, html, urllib.request, urllib.parse
from html.parser import HTMLParser
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'}
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
        para = re.sub(r'^[A-ZА-ЯЁ.\-]{3,}\.(?:RU|COM)\s*[-–—]\s*', '', para.strip())
        para = re.sub(r'\s+[A-ZА-ЯЁ]{3,}\.RU\s*[-–—]\s*', '. ', para)
        if len(para) < 50 or JUNK.search(para): continue
        for snt in SPLIT.split(para):
            snt = snt.strip()
            if len(snt) < 40 or len(snt) > 320 or same(snt): continue
            have = ' '.join(sents)
            if any(snt[:50] == q[:50] for q in sents) or snt[:60] in have or (len(snt) > 60 and any(q[:60] in snt for q in sents)): continue
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

# ---- Google Новости: ссылка news.google.com/rss/articles/<id> → настоящий адрес статьи ----
_GCTX = [["X", "X", ["X", "X"], None, None, 1, 1, "US:en", None, 1, None, None, None, None, None, 0, 1], "X", "X", 1, [1, 1, 1], 1, 1, None, 0, 0, None, 0]
def gn_decode(url):
    m = re.search(r'/(?:rss/)?articles/([^?/]+)', url)
    if not m: return url
    aid = m.group(1)
    q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    page = 'https://news.google.com/rss/articles/%s?hl=%s&gl=%s&ceid=%s' % (aid, urllib.parse.quote(q.get('hl', ['en-US'])[0]), q.get('gl', ['US'])[0], urllib.parse.quote(q.get('ceid', ['US:en'])[0]))
    h = urllib.request.urlopen(urllib.request.Request(page, headers=UA), timeout=12).read().decode('utf-8', 'ignore')
    sg = re.search(r'data-n-a-sg="([^"]+)"', h); ts = re.search(r'data-n-a-ts="([^"]+)"', h)
    if not sg or not ts: raise ValueError('no signature')
    inner = ["garturlreq", _GCTX, aid, int(ts.group(1)) if ts.group(1).isdigit() else ts.group(1), sg.group(1)]
    body = 'f.req=' + urllib.parse.quote(json.dumps([[["Fbv4je", json.dumps(inner, separators=(',', ':')), None, "0"]]], separators=(',', ':')))
    r = urllib.request.urlopen(urllib.request.Request('https://news.google.com/_/DotsSplashUi/data/batchexecute', data=body.encode(),
        headers=dict(UA, **{'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'})), timeout=12).read().decode('utf-8', 'ignore')
    t = r.split('\n\n', 1)[1] if '\n\n' in r else r
    t = t.lstrip()
    if t.startswith(")]}'"): t = t.split('\n', 1)[1]
    for row in json.loads(t):
        if isinstance(row, list) and len(row) >= 3 and (row[0] == 'wrb.fr' or row[1] == 'Fbv4je') and row[2]:
            p = json.loads(row[2]) if isinstance(row[2], str) else row[2]
            if p and p[0] == 'garturlres': return p[1]
    raise ValueError('no url')
