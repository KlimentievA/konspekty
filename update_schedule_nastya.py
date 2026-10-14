#!/usr/bin/env python3
"""Расписание Насти (РЭУ им. Плеханова, группа 15.24Д-ЭБ01/25с) → schedule_nastya.json.
Источник — официальный «Живой календарь» pleh.tech (iCalendar), ссылка для подписки на группу. Запускает GitHub Actions."""
import datetime, json, os, re, sys, urllib.request

GROUP = '15.24Д-ЭБ01/25с'
BASE = 'https://feed.pleh.tech/functions/v1/calendar-export?type=group&id=bc015d5f-ffdc-11ef-bedb-005056912e01&period='
PERIODS = ['year', 'semester', 'month']   # пробуем длинные периоды, если сервер их знает; месяц — всегда
HERE = os.path.dirname(os.path.abspath(__file__))
OUT, DBG = os.path.join(HERE, 'schedule_nastya.json'), os.path.join(HERE, 'schedule_nastya_debug.txt')
DIAG = []
KIND = {'практическое занятие': 'Практика', 'лекция': 'Лекция', 'семинар': 'Семинар'}


def fetch(period):
    req = urllib.request.Request(BASE + period, headers={'User-Agent': 'Mozilla/5.0 (hub schedule bot)'})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode('utf-8', 'replace')


def unesc(v):
    return v.replace('\\n', '\n').replace('\\,', ',').replace('\\;', ';').replace('\\\\', '\\')


def events(ics):
    ics = re.sub(r'\r?\n[ \t]', '', ics)   # склеиваем «сложенные» строки
    for blk in re.findall(r'BEGIN:VEVENT(.*?)END:VEVENT', ics, re.S):
        p = {}
        for ln in blk.strip().splitlines():
            if ':' in ln:
                k, v = ln.split(':', 1); p[k.split(';')[0].upper()] = v.strip()
        yield p


def stamp(v):
    m = re.match(r'(\d{4})(\d\d)(\d\d)T(\d\d)(\d\d)', v or '')
    return (f'{m[1]}-{m[2]}-{m[3]}', f'{m[4]}:{m[5]}') if m else (None, None)


def convert(p):
    d, b = stamp(p.get('DTSTART')); _, e = stamp(p.get('DTEND'))
    if not d or not b:
        return None
    summ = unesc(p.get('SUMMARY', '')).replace('[pleh.tech]', '').strip()
    m = re.match(r'^(.*?)\s*\((.*)\)\s*$', summ)
    name, kind = (m[1], m[2]) if m else (summ, '')
    kind = KIND.get(kind.lower(), kind)
    loc = unesc(p.get('LOCATION', ''))
    room, bd = '', ''
    mm = re.match(r'^(?:ауд\.\s*)?(.+?),\s*(\d+\s*корпус.*)$', loc)
    if mm: room, bd = mm[1], mm[2]
    else: room = re.sub(r'^ауд\.\s*', '', loc)
    desc = unesc(p.get('DESCRIPTION', ''))
    t = re.search(r'Преподавател[ьи]\s*:\s*([^\n]+)', desc)
    return {'d': d, 'b': b, 'e': e or b, 'n': name, 'k': kind, 'r': room, 'bd': bd, 't': (t[1].strip() if t else '')}


def main():
    got = {}
    for per in PERIODS:
        try:
            ics = fetch(per)
            ev = [c for c in map(convert, events(ics)) if c]
            DIAG.append(f'period={per}: {len(ics)} байт, событий {len(ev)}' + (f', {min(x["d"] for x in ev)}…{max(x["d"] for x in ev)}' if ev else ''))
            for c in ev: got[(c['d'], c['b'], c['n'], c['k'], c['r'])] = c
        except Exception as e:
            DIAG.append(f'period={per}: ОШИБКА {e!r}')
    open(DBG, 'w', encoding='utf-8').write('\n'.join(DIAG) + f'\nпар всего: {len(got)}\n')
    if not got:
        print('пар нет — файл не меняю'); return 0
    # старые пары прошедших дней не нужны; будущее перезаписываем свежим
    today = datetime.date.today().isoformat()
    lst = sorted(got.values(), key=lambda l: (l['d'], l['b'], l['n'], l['k']))
    try: old = json.load(open(OUT, encoding='utf-8')).get('list')
    except Exception: old = None
    if lst != old:
        json.dump({'group': GROUP, 'updated': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'list': lst}, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('пар:', len(lst)); return 0


if __name__ == '__main__':
    sys.exit(main())
