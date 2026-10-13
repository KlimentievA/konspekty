#!/usr/bin/env python3
"""Склейка: улучшенные билеты и дополнения к конспектам → src/index.src.html, src/data.json, src/tickets.json.
python3 src/merge.py OUTDIR  (в OUTDIR лежат konst*.json, ugol*.json, grazh*.json, notes_*.json)"""
import sys,re,json,glob
O=sys.argv[1].rstrip('/')+'/'
P='/home/claude/konspekty/src/'
T=json.load(open(P+'tickets.json'))
new={}
for f in glob.glob(O+'*.json'):
    b=f.split('/')[-1]
    if b.startswith('notes_'): continue
    subj=re.match(r'(konst|ugol|grazh)',b).group(1)
    for x in json.load(open(f)): new.setdefault(subj,{})[int(x['n'])]=x['a'].strip()
for s in T:
    miss=[x['n'] for x in T[s] if x['n'] not in new.get(s,{})]
    print(s,'tickets',len(T[s]),'missing',miss)
    for x in T[s]:
        if x['n'] in new.get(s,{}): x['a']=new[s][x['n']]
adds={}
for f in glob.glob(O+'notes_*.json'):
    for x in json.load(open(f)):
        if x.get('add','').strip() and x['add'].strip()!='—': adds[x['id']]=x['add'].strip()
D=json.load(open(P+'data.json')); cnt=0
for s in D['subjects']:
    for n in s['notes']:
        if n['id'] in adds and '### Дополнение' not in n['md']:
            n['md']=n['md'].rstrip()+'\n\n---\n\n'+adds[n['id']]+'\n'; cnt+=1
print('notes with additions',cnt,sorted(adds))
D['tickets']={'const':[[x['n'],x['q'],x['a']] for x in T['konst']],'crim':[[x['n'],x['q'],x['a']] for x in T['ugol']],'civil':[[x['n'],x['q'],x['a']] for x in T['grazh']]}
json.dump(T,open(P+'tickets.json','w'),ensure_ascii=False)
json.dump(D,open(P+'data.json','w'),ensure_ascii=False,separators=(',',':'))
h=open(P+'index.src.html').read()
def esc(o): return json.dumps(o,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
def swap(h,id_,obj):
    m=re.search(r'(<script type="application/json" id="%s">)(.*?)(</script>)'%id_,h,re.S); assert m
    return h[:m.start(2)]+esc(obj)+h[m.end(2):]
h=swap(h,'tickets',D['tickets']); h=swap(h,'data',{'subjects':D['subjects']})
open(P+'index.src.html','w').write(h); print('src updated',len(h.encode()))
