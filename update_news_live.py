#!/usr/bin/env python3
"""Быстрая лента новостей: заголовки из RSS изданий (без Google-поиска и без пересказов) → news-live.json.
Файл кладётся в ветку data и обновляется каждую минуту (scripts/live_news.sh в цикле «Автообновление данных»);
страница подмешивает его к полному news.json (который собирает update_news.py раз в час).
В файл попадают только сюжеты, которых ещё нет в news.json; после полного обновления они из него уходят сами.
Запуск: python3 update_news_live.py путь/к/news-live.json  (рядом с ним создаётся .changed: 1, если набор заголовков изменился)"""
import os, sys, json, re, hashlib, datetime
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else 'news-live.json'
# берём список лент, pull(), tags_of(), keep() из update_news.py — исполняем только его «библиотечную» часть (до загрузки лент)
src = open(os.path.join(HERE, 'update_news.py'), encoding='utf-8').read()
cut = src.index('with ThreadPoolExecutor(8) as ex:')
ns = {'__name__': 'news_lib', '__file__': os.path.join(HERE, 'update_news.py')}
sys.path.insert(0, HERE)
exec(compile(src[:cut], 'update_news.py', 'exec'), ns)
FEEDS, pull, tags_of, ago, CYR, tr = ns['FEEDS'], ns['pull'], ns['tags_of'], ns['ago'], ns['CYR'], ns['tr']

def ntitle(t): return re.sub(r'[^a-zа-яё0-9]+', ' ', t.lower()).strip()[:80]
def key(x): return x['u'].split('?')[0]

feeds = [f for f in FEEDS if f[0] is not None]      # только ленты изданий: поиск Google Новостей слишком тяжёл для минутного цикла
with ThreadPoolExecutor(16) as ex:
    got = [x for part in ex.map(pull, feeds) for x in part]

try: base = json.load(open(os.path.join(HERE, 'news.json'), encoding='utf-8')).get('items', [])
except Exception: base = []
bid = {x.get('id') or hashlib.md5(key(x).encode()).hexdigest()[:10] for x in base}
btl = set()
for x in base:
    btl.add(ntitle(x['t']))
    if x.get('to'): btl.add(ntitle(x['to']))

try: prev = {x['id']: x for x in json.load(open(OUT, encoding='utf-8')).get('items', [])}
except Exception: prev = {}

cut_d = ago(hours=10)
out, seen, seent = [], set(), set()
for x in sorted(got, key=lambda x: x['d'], reverse=True):
    if x['d'] < cut_d: continue
    i = hashlib.md5(key(x).encode()).hexdigest()[:10]
    nt = ntitle(x['t'])
    if i in bid or nt in btl or i in seen or nt in seent: continue
    seen.add(i); seent.add(nt)
    y = {'id': i, 't': x['t'], 'u': x['u'], 's': x['s'], 'cat': x['cat'], 'd': x['d'], 'tags': x.get('tags', []), 'imp': 0, 'live': 1}
    if x.get('ft'): y['ft'] = x['ft']
    p = prev.get(i)
    if p and p.get('tr'): y['to'], y['t'], y['tr'] = p['to'], p['t'], 1; y['tags'] = sorted(set(y['tags']) | set(tags_of(y['t'])))
    out.append(y)
    if len(out) >= 250: break

# перевод англоязычных заголовков (до 3 пакетов за минуту; перевод хранится в файле и не повторяется)
todo = [y for y in out if not y.get('tr') and not CYR.search(y['t'])][:90]
for k in range(0, len(todo), 30):
    part = todo[k:k + 30]
    try:
        res = tr('\n'.join(y['t'].replace('\n', ' ') for y in part)).split('\n')
        if len(res) != len(part): raise ValueError('mismatch')
        for y, t_ in zip(part, res):
            if t_.strip():
                y['to'], y['t'], y['tr'] = y['t'], t_.strip(), 1
                y['tags'] = sorted(set(y['tags']) | set(tags_of(y['t'])))
    except Exception as e:
        print('translate', str(e)[:80], file=sys.stderr)

old_ids = [x['id'] for x in prev.values()]
changed = sorted(old_ids) != sorted(y['id'] for y in out)
js = {'updated': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'items': out}
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
tmp = OUT + '.tmp'
json.dump(js, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
os.replace(tmp, OUT)
open(os.path.join(os.path.dirname(os.path.abspath(OUT)), '.changed'), 'w').write('1' if changed else '0')
print('live: лент %d, заголовков получено %d, в файле %d, изменился: %s' % (len(feeds), len(got), len(out), changed))
