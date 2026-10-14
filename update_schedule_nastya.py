#!/usr/bin/env python3
"""Расписание группы Насти (РЭУ им. Плеханова) → schedule_nastya.json. Источник — pleh.tech/timetable (robots.txt разрешает).
Каждая неделя — отдельный запрос ?group=…&week=YYYY-MM-DD (понедельник). Диагностика → schedule_nastya_debug.txt."""
import datetime, html, json, os, re, sys, urllib.parse, urllib.request

GROUP = os.environ.get('NASTYA_GROUP') or '15.24Д-ЭБ01/25с'
HERE = os.path.dirname(os.path.abspath(__file__))
OUT, DBG = os.path.join(HERE, 'schedule_nastya.json'), os.path.join(HERE, 'schedule_nastya_debug.txt')
DIAG = []
KIND = {'практическое занятие': 'Практика', 'лекция': 'Лекция', 'семинар': 'Семинар'}
DAY = re.compile(r'^(пн|вт|ср|чт|пт|сб|вс), (\d\d)\.(\d\d)$')
TIME = re.compile(r'^(\d\d:\d\d)\s*-\s*(\d\d:\d\d)$')
ROOM = re.compile(r'^(.+?),\s*(\d+\s*корпус.*)$')


def fetch(week):
    url = 'https://pleh.tech/timetable?' + urllib.parse.urlencode({'group': GROUP, 'week': week})
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (hub schedule bot)', 'Accept-Language': 'ru'})
    with urllib.request.urlopen(req, timeout=40) as r:
        return url, r.read().decode('utf-8', 'replace')


def lines(page):
    t = re.sub(r'<(script|style)\b.*?</\1>', '', page, flags=re.S)
    t = re.sub(r'<[^>]+>', '\n', t)
    return [html.unescape(x).strip() for x in t.split('\n') if x.strip()]


def parse(page, year):
    L, out, i, day = lines(page), [], 0, None
    while i < len(L):
        m = DAY.match(L[i])
        if m:
            day = '%d-%s-%s' % (year, m.group(3), m.group(2)); i += 1; continue
        # пара: номер, время, предмет, вид, дальше аудитория/преподаватель
        if day and L[i].isdigit() and i + 3 < len(L) and TIME.match(L[i + 1]):
            tm = TIME.match(L[i + 1]); name, kind = L[i + 2], L[i + 3]; i += 4
            rest = []
            while i < len(L) and not (DAY.match(L[i]) or (L[i].isdigit() and i + 1 < len(L) and TIME.match(L[i + 1])) or L[i] in ('Главная', 'Расписание', 'Меню')):
                rest.append(L[i]); i += 1
            k = KIND.get(kind.lower(), kind)
            subs = []   # (подгруппа, аудитория, корпус, преподаватель)
            if rest and rest[0].startswith('Подгруппа'):
                cur = None
                for x in rest:
                    if x.startswith('Подгруппа'): cur = x.rstrip(':'); continue
                    mm = re.match(r'^(.*?),\s*ауд\.\s*(.+?),\s*(\d+\s*корпус.*)$', x)
                    if mm and cur: subs.append((cur, mm.group(2), mm.group(3), mm.group(1)))
            else:
                room, bd = '', ''
                if rest:
                    mm = ROOM.match(rest[0]); room, bd = (mm.group(1), mm.group(2)) if mm else (rest[0], '')
                subs.append(('', room, bd, rest[1] if len(rest) > 1 else ''))
            for sg, room, bd, teacher in subs:
                out.append({'d': day, 'b': tm.group(1), 'e': tm.group(2), 'n': name, 'k': (k + ' · ' + sg.lower()) if sg else k, 'r': room, 'bd': bd, 't': teacher})
            continue
        i += 1
    return out


def discover(page):
    """Страница — пустая оболочка React: ищем в её скриптах адреса API (для диагностики)."""
    for src in re.findall(r'<script[^>]+src="([^"]+)"', page)[:6]:
        u = urllib.parse.urljoin('https://pleh.tech/', src)
        if 'pleh.tech' not in u: continue
        try:
            req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0 (hub schedule bot)'})
            js = urllib.request.urlopen(req, timeout=40).read().decode('utf-8', 'replace')
        except Exception as e:
            DIAG.append(f'JS {u}: ОШИБКА {e!r}'); continue
        urls = sorted(set(re.findall(r'https?://[A-Za-z0-9_.\-]+(?:/[A-Za-z0-9_./\-]*)?', js)))
        urls = [x for x in urls if not re.search(r'w3\.org|reactjs|schema\.org|mozilla|github|google|vk\.com|yandex', x)]
        paths = sorted(set(re.findall(r'["\'`](/?(?:api|functions|rest|v1)/[A-Za-z0-9_/\-?=&.${}]{2,80})["\'`]', js)))
        words = sorted(set(re.findall(r'["\'`]([^"\'`\s]{0,60}(?:timetable|schedule|lessons?)[^"\'`\s]{0,60})["\'`]', js, re.I)))
        if 'lessons_current' in js:
            red = lambda t: re.sub(r'eyJ[A-Za-z0-9_\-.]{20,}', 'JWT…', t)
            for m in list(re.finditer(r'lessons_current', js))[:3]:
                DIAG.append('CTX lessons_current: ' + red(js[max(0, m.start() - 900):m.end() + 500]).replace('\n', ' '))
            for name in re.findall(r'\$\{(\w+)\}/rest/v1/lessons_current', js):
                for m in list(re.finditer(r'[,;\s]' + re.escape(name) + r'=', js))[:2]:
                    DIAG.append(f'DEF {name}: ' + red(js[m.start():m.start() + 200]))
            DIAG.append('supabase-хосты: ' + str(sorted(set(re.findall(r'[a-z0-9]+\.supabase\.co', js)))[:5]) + '; jwt-ключей в коде: ' + str(len(re.findall(r'eyJ[A-Za-z0-9_\-.]{20,}', js))))
        DIAG.append(f'JS {u} ({len(js)} байт): url={urls[:25]} paths={paths[:30]} слова={words[:30]}')


def main():
    today = datetime.date.today(); mon = today - datetime.timedelta(days=today.weekday())
    out, empty = [], 0
    for w in range(-1, 20):
        a = mon + datetime.timedelta(days=7 * w)
        try:
            url, page = fetch(a.isoformat())
            got = parse(page, a.year)
            if w == 0 and not got: discover(page)
            if w <= 0: DIAG.append(f'{url}: {len(page)} байт, пар {len(got)}, «занятий нет» {page.count("занятий нет")}, начало: {re.sub(chr(10)," ",page[:200])}')
            out += got; empty += 0 if got else 1
        except Exception as e:
            DIAG.append(f'{a}: ОШИБКА {e!r}')
    open(DBG, 'w', encoding='utf-8').write('\n'.join(DIAG) + f'\nпар всего: {len(out)}\n')
    if not out:
        print('пар нет — файл не меняю'); return 0
    seen, uniq = set(), []
    for l in sorted(out, key=lambda l: (l['d'], l['b'], l['n'], l['k'])):
        k = (l['d'], l['b'], l['n'], l['k'], l['r'])
        if k not in seen: seen.add(k); uniq.append(l)
    try: old = json.load(open(OUT, encoding='utf-8')).get('list')
    except Exception: old = None
    if uniq != old:
        json.dump({'group': GROUP, 'updated': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'list': uniq}, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('пар:', len(uniq)); return 0


if __name__ == '__main__':
    sys.exit(main())
