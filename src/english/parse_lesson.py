#!/usr/bin/env python3
"""Разбор и проверка уроков английского (src/english/lessons/NN_slug.md) и справочников (src/english/ref/NN_slug.md).
Проверка одного файла: python3 src/english/parse_lesson.py src/english/lessons/01_xxx.md   (код выхода 1 — есть ошибки)
Формат описан в src/english/FORMAT.md."""
import re, sys, os, json

SECT = ['Цели', 'Теория', 'Слова', 'Диалог', 'Упражнения', 'Вместе', 'Запомни', 'Мини-тест']


def _split(md, level):
    pat = re.compile(r'^' + '#' * level + r' (.+)$', re.M)
    ms = list(pat.finditer(md))
    out = []
    for i, m in enumerate(ms):
        out.append((m.group(1).strip(), md[m.end():ms[i + 1].start() if i + 1 < len(ms) else len(md)].strip('\n')))
    pre = md[:ms[0].start()] if ms else md
    return pre, out


def parse_items(body, errs, where):
    """пункты вида '1. текст => ответ / ответ' или '1. текст :: вар | вар* | вар'; '// пояснение' — строкой ниже"""
    items = []
    intro = []
    for ln in body.split('\n'):
        s = ln.strip()
        if not s:
            continue
        m = re.match(r'^(\d+)\.\s+(.*)$', s)
        if m:
            t = m.group(2)
            if ' :: ' in t:
                q, o = t.split(' :: ', 1)
                opts = [x.strip() for x in o.split(' | ')]
                ok = [i for i, x in enumerate(opts) if x.endswith('*')]
                opts = [x.rstrip('*').strip() for x in opts]
                if len(ok) != 1 or len(opts) < 3 or any(not x for x in opts):
                    errs.append('%s п.%s: нужен ровно один вариант со * и не меньше 3 вариантов' % (where, m.group(1)))
                    continue
                items.append({'t': 'c', 'q': q.strip(), 'o': opts, 'a': ok[0]})
            elif ' => ' in t:
                q, a = t.split(' => ', 1)
                ans = [x.strip() for x in a.split(' / ') if x.strip()]
                if not ans:
                    errs.append('%s п.%s: пустой ответ' % (where, m.group(1))); continue
                items.append({'t': 'f', 'q': q.strip(), 'a': ans})
            else:
                errs.append('%s п.%s: нет «=>» и «::»' % (where, m.group(1)))
        elif s.startswith('//'):
            if items:
                items[-1]['e'] = (items[-1].get('e', '') + ' ' + s[2:].strip()).strip()
            else:
                errs.append(where + ': пояснение без пункта')
        else:
            if not items:
                intro.append(s)
            else:
                errs.append('%s: лишняя строка после пунктов: %s' % (where, s[:50]))
    return ' '.join(intro), items


def parse_lesson(path):
    errs = []
    md = open(path, encoding='utf-8').read().replace('\r', '')
    m = re.match(r'^# Урок (\d+)\. (.+)\n((?:[a-z]+: .*\n)+)', md)
    if not m:
        return None, ['нет заголовка «# Урок N. Название» и строк short/level/unit/theme/minutes']
    meta = dict(re.findall(r'^([a-z]+): (.*)$', m.group(3), re.M))
    for k in ('short', 'level', 'unit', 'theme', 'minutes'):
        if k not in meta:
            errs.append('нет поля ' + k)
    L = {'n': int(m.group(1)), 'title': m.group(2).strip(), 'short': meta.get('short', ''), 'level': meta.get('level', ''),
         'unit': int(meta.get('unit', '0') or 0), 'theme': meta.get('theme', 'no').strip() == 'yes', 'min': int(meta.get('minutes', '60') or 60)}
    L['id'] = re.sub(r'^\d+_', '', os.path.splitext(os.path.basename(path))[0])
    _, secs = _split(md[m.end():], 2)
    S = dict(secs)
    for k in SECT:
        if k not in S:
            errs.append('нет раздела «## %s»' % k)
    if errs:
        return L, errs
    # цели
    L['goals'] = [re.sub(r'^[-*] ', '', x).strip() for x in S['Цели'].split('\n') if x.strip().startswith(('-', '*'))]
    if not (3 <= len(L['goals']) <= 8): errs.append('Цели: нужно 3–8 пунктов')
    L['theory'] = S['Теория'].strip()
    nw = len(re.findall(r'[А-Яа-яЁёA-Za-z]+', L['theory']))
    if nw < 700: errs.append('Теория слишком короткая: %d слов (нужно ≥ 700)' % nw)
    if L['theory'].count('\n### ') + (1 if L['theory'].startswith('### ') else 0) < 3: errs.append('Теория: нужно ≥ 3 подраздела «### …»')
    # слова
    words = []
    for ln in S['Слова'].split('\n'):
        s = ln.strip()
        if not s.startswith('|') or re.match(r'^\|[\s\-:|]+\|$', s): continue
        cells = [c.strip() for c in s.strip('|').split('|')]
        if cells[0].lower() == 'english': continue
        if len(cells) != 4 or not all(cells): errs.append('Слова: строка должна иметь 4 заполненных столбца: ' + s[:60]); continue
        words.append({'w': cells[0], 't': cells[1], 'x': cells[2], 'xr': cells[3]})
    L['words'] = words
    if not (20 <= len(words) <= 32): errs.append('Слова: %d (нужно 20–32)' % len(words))
    if len({w['w'].lower() for w in words}) != len(words): errs.append('Слова: есть повторы')
    # диалог
    dl = []; dtitle = ''
    for ln in S['Диалог'].split('\n'):
        s = ln.strip()
        if not s: continue
        mm = re.match(r'^[-*] ([^:]{1,20}): (.+?) \| (.+)$', s)
        if mm: dl.append({'s': mm.group(1).strip(), 'en': mm.group(2).strip(), 'ru': mm.group(3).strip()})
        elif not dl: dtitle = s.strip('*_ ')
        else: errs.append('Диалог: строка не в формате «- Имя: English | русский»: ' + s[:60])
    L['dialogue'] = {'title': dtitle, 'lines': dl}
    if len(dl) < 10: errs.append('Диалог: %d реплик (нужно ≥ 10)' % len(dl))
    # упражнения
    pre, sets = _split(S['Упражнения'], 3)
    if pre.strip(): errs.append('Упражнения: текст до первого «### »')
    L['sets'] = []
    total = 0
    for title, body in sets:
        intro, items = parse_items(body, errs, 'Упражнение «%s»' % title[:30])
        if not 5 <= len(items) <= 12: errs.append('Упражнение «%s»: %d пунктов (нужно 5–12)' % (title[:30], len(items)))
        total += len(items)
        L['sets'].append({'title': title, 'intro': intro, 'items': items})
    if len(L['sets']) < 5: errs.append('Упражнений: %d (нужно ≥ 5)' % len(L['sets']))
    if total < 40: errs.append('Пунктов в упражнениях: %d (нужно ≥ 40)' % total)
    kinds = {i['t'] for s in L['sets'] for i in s['items']}
    if kinds != {'c', 'f'}: errs.append('Упражнения должны включать и выбор (::), и ввод (=>)')
    # вместе / запомни
    L['together'] = S['Вместе'].strip(); L['recap'] = S['Запомни'].strip()
    if len(L['together']) < 200: errs.append('Вместе: слишком коротко')
    if len([x for x in L['recap'].split('\n') if x.strip().startswith(('-', '*'))]) < 5: errs.append('Запомни: нужно ≥ 5 пунктов')
    # мини-тест
    _, test = parse_items(S['Мини-тест'], errs, 'Мини-тест')
    L['test'] = test
    if len(test) != 10 or any(t['t'] != 'c' for t in test): errs.append('Мини-тест: нужно ровно 10 вопросов с выбором (::), сейчас %d' % len(test))
    # проверка ответов: в fill-пунктах с ___ должен быть ровно один пропуск
    for s in L['sets']:
        for i in s['items']:
            if i['t'] == 'f' and i['q'].count('___') > 1: errs.append('Упражнение «%s»: больше одного ___ : %s' % (s['title'][:25], i['q'][:50]))
    return L, errs


def parse_ref(path):
    errs = []
    md = open(path, encoding='utf-8').read().replace('\r', '').strip().split('\n')
    if not md[0].startswith('# ') or len(md) < 3 or not md[1].startswith('short: '):
        return None, ['нужны строки «# Название» и «short: …»']
    r = {'id': re.sub(r'^\d+_', '', os.path.splitext(os.path.basename(path))[0]), 'title': md[0][2:].strip(), 'short': md[1][7:].strip(), 'md': '\n'.join(md[2:]).strip() + '\n'}
    if len(r['md']) < 800: errs.append('Справочник слишком короткий')
    return r, errs


if __name__ == '__main__':
    bad = 0
    for p in sys.argv[1:]:
        fn = parse_ref if os.sep + 'ref' + os.sep in p else parse_lesson
        L, errs = fn(p)
        print(('✗ ' if errs else '✓ ') + os.path.basename(p))
        for e in errs: print('   -', e)
        bad += bool(errs)
    sys.exit(1 if bad else 0)
