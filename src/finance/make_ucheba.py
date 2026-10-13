import sys
src,out=sys.argv[1:3]
t=open(src,encoding='utf-8').read()
old='<a class="brand" href="#" data-go="" aria-label="Все предметы">'
assert t.count(old)==1
btn='<a class="ibtn hubb" href="./" aria-label="Все разделы" title="Все разделы"><svg viewBox="0 0 24 24"><path d="M15 6l-6 6 6 6"/></svg></a>'
t=t.replace(old,btn+old)
css='<style>.hubb{margin-left:-8px;margin-right:2px;flex:none;text-decoration:none}@media (min-width:900px){.hubb{margin-left:-12px}}</style>'
assert t.count('<title>Конспекты семинаров</title>')==1
t=t.replace('<title>Конспекты семинаров</title>','<title>Учёба</title>'+css,1)
open(out,'w',encoding='utf-8').write(t);print('ok',len(t.encode()))
