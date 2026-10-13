import sys
src,out=sys.argv[1:3]
t=open(src,encoding='utf-8').read()
# кнопка «₽» рядом с «Поиск» и «Aa»: оформлена как остальные кнопки шапки, поэтому подходит к любой теме
old='<button class="ibtn" id="btn-search"'
assert t.count(old)==1
btn='<a class="ibtn" id="btn-fin" href="finance.html" aria-label="Финансы" title="Финансы" style="font:600 18px/1 var(--serif);text-decoration:none">₽</a>'
t=t.replace(old,btn+old,1)
css=('<style>html:root[data-skin=c] #btn-fin,html:root[data-skin=f] #btn-fin{left:4px;right:auto}'
     'html:root[data-skin=c] #btn-fin{font-family:var(--head)!important;font-weight:900!important}'
     'html:root[data-skin=f] #btn-fin{font-weight:500!important;font-size:19px!important}</style>')
assert t.count('<title>Конспекты семинаров</title>')==1
t=t.replace('<title>Конспекты семинаров</title>','<title>Учёба</title>'+css,1)
open(out,'w',encoding='utf-8').write(t);print('ok',len(t.encode()))
