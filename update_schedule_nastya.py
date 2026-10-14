#!/usr/bin/env python3
"""Расписание группы Насти → schedule_nastya.json (+ schedule_nastya_debug.txt с диагностикой).
Источник — публичный API расписания ВШЭ (ruz.hse.ru), тот же, что показывает pleh.tech. Запускает GitHub Actions."""
import datetime, json, os, re, sys, urllib.parse, urllib.request

GROUP = os.environ.get('NASTYA_GROUP') or '15.24Д-ЭМ01/25с'
HERE = os.path.dirname(os.path.abspath(__file__))
OUT, DBG = os.path.join(HERE, 'schedule_nastya.json'), os.path.join(HERE, 'schedule_nastya_debug.txt')
BASES = ['https://ruz.hse.ru/api', 'https://www.hse.ru/api']
DIAG = []
KINDS = (('лекц', 'Лекция'), ('семин', 'Семинар'), ('практ', 'Практика'))


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (hub schedule bot)', 'Accept': 'application/json', 'Accept-Language': 'ru'})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.status, r.read().decode('utf-8', 'replace')


def find_group():
    for base in BASES:
        url = base + '/search?' + urllib.parse.urlencode({'term': GROUP, 'type': 'group'})
        try:
            st, body = get(url)
            DIAG.append(f'{url} -> {st}: {re.sub(chr(10), " ", body[:300])}')
            for g in json.loads(body):
                if str(g.get('label', '')).strip().lower() == GROUP.lower() or len(json.loads(body)) == 1:
                    return base, g['id']
        except Exception as e:
            DIAG.append(f'{url} -> ОШИБКА {e!r}')
    return None, None


def conv(x):
    if not x.get('date') or not x.get('beginLesson'):
        return None
    kd = str(x.get('kindOfWork', '')).lower()
    return {'d': str(x['date']).replace('.', '-'), 'b': x['beginLesson'], 'e': x['endLesson'],
            'n': re.sub(r'\s*\((рус|анг)\)\s*$', '', str(x.get('discipline', ''))),
            'k': next((v for k, v in KINDS if k in kd), str(x.get('kindOfWork', ''))),
            'r': str(x.get('auditorium', '')), 't': x.get('lecturer_title') or x.get('lecturer') or '',
            'bd': x.get('building') or '', 'u': x.get('url1') or ''}


def main():
    base, gid = find_group()
    if not gid:
        open(DBG, 'w', encoding='utf-8').write('\n'.join(DIAG) + '\nгруппа не найдена\n'); print('группа не найдена'); return 0
    today = datetime.date.today(); mon = today - datetime.timedelta(days=today.weekday())
    out = []
    for w in range(-1, 26):
        a = mon + datetime.timedelta(days=7 * w); b = a + datetime.timedelta(days=6)
        url = f"{base}/schedule/group/{gid}?start={a:%Y.%m.%d}&finish={b:%Y.%m.%d}&lng=1"
        try:
            st, body = get(url); data = json.loads(body)
            if w == -1: DIAG.append(f'{url} -> {st}, {len(body)} байт: {body[:300]}')
            out += [c for c in map(conv, data if isinstance(data, list) else []) if c]
        except Exception as e:
            DIAG.append(f'{url} -> ОШИБКА {e!r}')
    open(DBG, 'w', encoding='utf-8').write('\n'.join(DIAG) + f'\nгруппа id={gid}, пар: {len(out)}\n')
    if not out:
        print('пар нет — файл не меняю'); return 0
    seen, uniq = set(), []
    for l in sorted(out, key=lambda l: (l['d'], l['b'], l['n'])):
        k = (l['d'], l['b'], l['n'], l['r'])
        if k not in seen: seen.add(k); uniq.append(l)
    try: old = json.load(open(OUT, encoding='utf-8')).get('list')
    except Exception: old = None
    if uniq != old:
        json.dump({'group': GROUP, 'updated': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'list': uniq}, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('пар:', len(uniq)); return 0


if __name__ == '__main__':
    sys.exit(main())
