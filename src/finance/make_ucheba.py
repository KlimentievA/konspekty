import sys
src,out=sys.argv[1:3]
t=open(src,encoding='utf-8').read()
# пункт «Финансы» в общем меню разделов (работает во всех темах оформления)
old='<span class="nm">Сессия</span><span class="ct"></span></a>\';'
assert t.count(old)==1
t=t.replace(old,'<span class="nm">Сессия</span><span class="ct"></span></a><a class="subj fin" href="finance.html" data-s="fin" style="--h:160" title="Перейти в раздел «Финансы»"><span class="dot"></span><span class="nm">Финансы →</span><span class="ct"></span></a>\';')
assert t.count('<title>Конспекты семинаров</title>')==1
t=t.replace('<title>Конспекты семинаров</title>','<title>Учёба</title>',1)
open(out,'w',encoding='utf-8').write(t);print('ok',len(t.encode()))
