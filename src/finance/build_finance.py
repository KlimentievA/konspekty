#!/usr/bin/env python3
"""Сборка finance.html: python3 build_finance.py CONTENT_DIR MARKED_JS OUT_HTML"""
import sys, os, re, json, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import static_data as S

cdir, marked_path, out = sys.argv[1:4]
IDS = {'01':'ib','02':'otchetnost','03':'npv-irr','04':'wacc','05':'dcf','06':'multiplikatory','07':'metody','08':'sektory',
       '09':'koeffitsienty','10':'ma-lbo','11':'rynki-kapitala','12':'rossiya','13':'sobesedovanie','14':'excel','15':'makro','16':'kpi','17':'struktura-kapitala','18':'praktikum','19':'karera','20':'project-black','21':'stazhirovka','22':'keysy','98':'glossariy','99':'istochniki'}

def qa(md):
    # «**N. Вопрос**\nОтвет…» → <details>
    out, lines, i = [], md.split('\n'), 0
    while i < len(lines):
        m = re.match(r'^\*\*(\d+)\.\s+(.+?)\*\*\s*$', lines[i])
        if m:
            ans = []
            i += 1
            while i < len(lines) and lines[i].strip() and not lines[i].startswith('#') and not re.match(r'^\*\*\d+\.', lines[i]):
                ans.append(lines[i]); i += 1
            out.append('<details class="qa"><summary><span>%s</span>%s</summary><div>\n\n%s\n\n</div></details>\n' % (m.group(1), m.group(2), '\n'.join(ans)))
            continue
        out.append(lines[i]); i += 1
    return '\n'.join(out)

chs = []
for f in sorted(glob.glob(os.path.join(cdir, '*.md'))):
    b = os.path.basename(f)[:2]
    t = open(f, encoding='utf-8').read().strip().split('\n')
    title = t[0].lstrip('# ').strip()
    assert t[1].startswith('short:'), f
    short = t[1][6:].strip()
    md = '\n'.join(t[2:]).strip() + '\n'
    if b in ('13', '18', '20', '21'): md = qa(md)
    chs.append({'id': IDS[b], 'title': title, 'short': short, 'md': md})

import terms as TM
gl = open(os.path.join(cdir, '98_glossary.md'), encoding='utf-8').read()
TERMS = TM.build(gl)
for x in TERMS:
    x['p'] = [re.sub(r'(?<!\\)\((?!\?)', '(?:', s.replace('\\w', '[а-яёА-ЯЁa-zA-Z]')) for s in x['p']]
static = {'ru': S.RU, 'ru_asof': S.RU_ASOF, 'ru_sect': S.RU_SECT, 'ru_sect_asof': S.RU_SECT_ASOF,
          'us': S.US, 'us_asof': S.US_ASOF, 'us_sect': S.US_SECT, 'us_sect_asof': S.US_SECT_ASOF,
          'macro': S.MACRO, 'kbd': S.KBD, 'keyrate': S.KEYRATE, 'cal': S.CAL, 'events': json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'events.json'), encoding='utf-8'))}
data = json.dumps({'chapters': chs, 'static': static, 'terms': TERMS}, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
tpl = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'finance_template.html'), encoding='utf-8').read()
assert '<!--DATA-->' in tpl and '<!--MARKED-->' in tpl
tpl = tpl.replace('<!--ZOOM-->', '<script>' + open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'zoom.js'), encoding='utf-8').read() + '</script>')
html = tpl.replace('<!--DATA-->', '<script type="application/json" id="fdata">' + data + '</script>') \
          .replace('<!--MARKED-->', '<script>' + open(marked_path, encoding='utf-8').read() + '</script>')
open(out, 'w', encoding='utf-8').write(html)
print('ok', len(chs), 'chapters', len(TERMS), 'terms', len(html.encode()), 'bytes')
