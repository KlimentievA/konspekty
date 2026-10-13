import sys
src,out=sys.argv[1:3]
t=open(src,encoding='utf-8').read()
# маленькая стрелка в левом верхнем углу → главная (выбор «Учёба / Финансы»); вёрстку конспектов не трогает
btn=('<a id="hubfix" href="./" aria-label="Все разделы" title="Учёба / Финансы">'
     '<svg viewBox="0 0 24 24" width="16" height="16"><path d="M15 6l-6 6 6 6" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg></a>')
css=('<style>#hubfix{position:fixed;z-index:200;top:calc(env(safe-area-inset-top,0px) + 12px);left:0;width:16px;height:32px;display:grid;place-items:center;'
     'border-radius:0 8px 8px 0;background:var(--accent,#A93D28);color:#fff;text-decoration:none;box-shadow:0 2px 8px rgba(0,0,0,.25)}'
     '#hubfix svg{width:14px;height:14px}#hubfix:active{filter:brightness(1.15)}'
     '@media (min-width:900px){#hubfix{top:calc(env(safe-area-inset-top,0px) + 4px);left:4px;width:28px;height:28px;border-radius:50%}'
     '#hubfix svg{width:16px;height:16px}#hubfix:hover{filter:brightness(1.15);transform:translateX(-1px)}}</style>')
assert t.count('<title>Конспекты семинаров</title>')==1
t=t.replace('<title>Конспекты семинаров</title>','<title>Учёба</title>'+css,1)
assert t.count('<div class="app">')==1
t=t.replace('<div class="app">',btn+'<div class="app">',1)
open(out,'w',encoding='utf-8').write(t);print('ok',len(t.encode()))
