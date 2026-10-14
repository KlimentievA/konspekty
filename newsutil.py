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
def fetch(url, t=12):
    r = urllib.request.urlopen(urllib.request.Request(url, headers=dict(UA, **{'Accept-Language': 'ru,en;q=0.8', 'Accept': 'text/html,application/xhtml+xml'})), timeout=t)
    raw = r.read(3_000_000)
    cs = r.headers.get_content_charset() or ('windows-1251' if b'windows-1251' in raw[:3000].lower() else 'utf-8')
    return raw.decode(cs, 'ignore'), r.geturl()

def _paras_from_html(raw):
    """Абзацы основного текста: trafilatura → articleBody из JSON-LD → теги <p>."""
    try:
        import trafilatura
        t = trafilatura.extract(raw, include_comments=False, include_tables=False, favor_precision=True, deduplicate=True)
        if t and len(t) > 300: return [q.strip() for q in t.split('\n') if q.strip()]
    except Exception:
        pass
    for m in re.finditer(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', raw, re.S | re.I):
        try:
            j = json.loads(m.group(1).strip())
            for o in (j if isinstance(j, list) else j.get('@graph', [j]) if isinstance(j, dict) else []):
                if isinstance(o, dict) and len(o.get('articleBody') or '') > 300:
                    return [q.strip() for q in re.split(r'\n+', html.unescape(o['articleBody'])) if q.strip()]
        except Exception:
            pass
    pp = P(); pp.feed(raw)
    return ([html.unescape(pp.meta['d'])] if pp.meta.get('d') else []) + [html.unescape(x) for x in pp.ps]

def clean_desc(d):
    d = re.sub(r'\s*\|\s*\d{1,2}\.\d{1,2}\.\d{2,4},?.*$', '', d or '')
    return re.sub(r'\s*(?:Читать далее|Read more|Continue reading)\W*$', '', d).strip()

def article(url, title, desc='', limit=2300):
    """Пересказ статьи: первые содержательные абзацы (до ~limit знаков, обычно 1500–2300), без мусора и повтора заголовка."""
    try:
        raw, _ = fetch(url)
        cands = _paras_from_html(raw)
    except Exception:
        cands = []
    if not cands and desc: cands = [clean_desc(desc)]
    tw = set(re.findall(r'\w+', (title or '').lower()))
    def same(s_):
        w = set(re.findall(r'\w+', s_.lower()))
        return w and len(w & tw) / len(w) > 0.7 and len(s_) < 200
    out, total = [], 0
    for para in cands:
        para = re.sub(r'^[A-ZА-ЯЁ.\-]{3,}\.(?:RU|COM)\s*[-–—]\s*', '', para.strip())
        para = re.sub(r'\s+[A-ZА-ЯЁ]{3,}\.RU\s*[-–—]\s*', '. ', para)
        para = re.sub(r'\s+', ' ', para)
        if len(para) < 60 or JUNK.search(para[:200]) or same(para): continue
        have = ' '.join(out)
        if para[:60] in have or any(q[:60] in para for q in out if len(q) >= 60): continue
        if total + len(para) > limit:
            rest = limit - total
            if rest > 150:
                cut = ''
                for snt in SPLIT.split(para):
                    if len(cut) + len(snt) > rest: break
                    cut += (' ' if cut else '') + snt
                if cut: out.append(cut)
            break
        out.append(para); total += len(para)
    return out

def lead(paras, n=260):
    """Короткий анонс: 1–2 первых предложения."""
    if not paras: return ''
    s_ = ''
    for snt in SPLIT.split(' '.join(paras)):
        if s_ and len(s_) + len(snt) > n: break
        s_ += (' ' if s_ else '') + snt
        if len(s_) > n * 0.6: break
    return s_[:n + 120]

def summarize(url, title, desc):
    return article(url, title, desc)

CYR = re.compile('[А-Яа-яЁё]')
def tr(text):
    """Автоперевод англоязычных новостей на русский (публичный эндпоинт Google Translate)."""
    j = json.loads(urllib.request.urlopen(urllib.request.Request('https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=ru&dt=t',
        data=urllib.parse.urlencode({'q': text[:4800]}).encode(), headers=dict(UA, **{'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'})), timeout=20).read().decode('utf-8'))
    out = ''.join(seg[0] for seg in j[0] if seg and seg[0])
    if not out.strip(): raise ValueError('empty')
    return out
def tr_list(a):
    """Перевод списка абзацев (кусками до ~4500 знаков)."""
    if not a: return a
    out, chunk = [], []
    for q in a + [None]:
        if q is None or (chunk and sum(len(c) + 1 for c in chunk) + len(q) > 4500):
            if chunk:
                t_ = [w.strip() for w in tr('\n'.join(chunk)).split('\n') if w.strip()]
                out += t_ if t_ else chunk
            chunk = []
        if q is not None: chunk.append(q.replace('\n', ' '))
    return out

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
