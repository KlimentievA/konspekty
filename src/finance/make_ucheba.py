import sys
src,out=sys.argv[1:3]
t=open(src,encoding='utf-8').read()
# маленькая стрелка в левом верхнем углу → главная (выбор «Учёба / Финансы»); вёрстку конспектов не трогает
btn=('<a id="hubfix" href="./" aria-label="Все разделы" title="Учёба / Финансы">'
     '<svg viewBox="0 0 24 24" width="16" height="16"><path d="M15 6l-6 6 6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></a>')
css=('<style>#hubfix{position:fixed;z-index:200;top:calc(env(safe-area-inset-top,0px) + 14px);left:0;width:15px;height:28px;display:grid;place-items:center;'
     'color:var(--fg,#25221C);opacity:.4;text-decoration:none;transition:opacity .15s}#hubfix svg{width:14px;height:14px}'
     '#hubfix:hover,#hubfix:focus-visible{opacity:1}'
     '@media (min-width:900px){#hubfix{top:calc(env(safe-area-inset-top,0px) + 4px);left:4px;width:26px;height:26px;border-radius:50%;'
     'background:color-mix(in srgb,var(--bg,#F4F1E8) 70%,transparent)}#hubfix svg{width:16px;height:16px}}</style>')
assert t.count('<title>Конспекты семинаров</title>')==1
t=t.replace('<title>Конспекты семинаров</title>','<title>Учёба</title>'+css,1)
assert t.count('<div class="app">')==1
t=t.replace('<div class="app">',btn+'<div class="app">',1)
open(out,'w',encoding='utf-8').write(t);print('ok',len(t.encode()))
