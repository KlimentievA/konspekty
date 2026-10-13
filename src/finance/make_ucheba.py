import sys
src,out=sys.argv[1:3]
t=open(src,encoding='utf-8').read()
# стрелка в левом верхнем углу → главная «Учёба / Финансы». Цвета берутся из переменных темы, поэтому подходит к любому оформлению.
btn=('<a id="hubfix" href="./" aria-label="Учёба / Финансы" title="Учёба / Финансы">'
     '<svg viewBox="0 0 24 24"><path d="M14.5 6l-6 6 6 6" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg></a>')
css=('<style>'
     '#hubfix{position:fixed;z-index:200;top:calc(env(safe-area-inset-top,0px) + 13px);left:0;width:17px;height:30px;display:grid;place-items:center;'
     'background:var(--surface,#FBF9F3);color:var(--fg,#25221C);border:1px solid var(--line,#D9D3C2);border-left:0;border-radius:0 9px 9px 0;'
     'text-decoration:none;box-shadow:0 1px 4px rgba(0,0,0,.08);transition:background .15s,color .15s}'
     '#hubfix svg{width:14px;height:14px}'
     '#hubfix:hover,#hubfix:active{background:var(--fg,#25221C);color:var(--bg,#F4F1E8);border-color:var(--fg,#25221C)}'
     '@media (min-width:900px){#hubfix{top:calc(env(safe-area-inset-top,0px) + 6px);left:6px;width:30px;height:30px;border-left:1px solid var(--line,#D9D3C2);border-radius:50%}'
     '#hubfix svg{width:16px;height:16px}}'
     'html:root[data-skin=c] #hubfix{border-radius:0;box-shadow:none;border-color:var(--fg)}'
     'html:root[data-skin=k] #hubfix{border-width:2px;border-color:var(--fg)}'
     '</style>')
assert t.count('<title>Конспекты семинаров</title>')==1
t=t.replace('<title>Конспекты семинаров</title>','<title>Учёба</title>'+css,1)
assert t.count('<div class="app">')==1
t=t.replace('<div class="app">',btn+'<div class="app">',1)
open(out,'w',encoding='utf-8').write(t);print('ok',len(t.encode()))
