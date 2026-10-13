import sys
src,out=sys.argv[1:3]
t=open(src,encoding='utf-8').read()
# стрелка в левом верхнем углу → главная «Учёба / Финансы». Цвета берутся из переменных темы, поэтому подходит к любому оформлению.
btn=('<a id="hubfix" href="./" aria-label="Учёба / Финансы" title="Учёба / Финансы">'
     '<svg viewBox="0 0 24 24"><path d="M19 12H5.5M11 6l-6 6 6 6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></a>')
# Стрелка живёт в шапке перед «§ Конспекты». В «Газете» и «Книге» (заголовок по центру) на компьютере —
# зеркальная пара к круглой кнопке «Aa» справа, на телефоне — слева в строке заголовка.
css=('<style>'
     '#hubfix{flex:none;display:grid;place-items:center;text-decoration:none;color:var(--fg,#25221C);width:34px;height:34px;margin:0 8px 0 -4px;'
     'background:color-mix(in srgb,var(--bg,#F4F1E8) 86%,transparent);border:1px solid var(--line,#D9D3C2);border-radius:999px;'
     'transition:background .15s,color .15s}'
     '#hubfix svg{width:16px;height:16px;transition:transform .15s}'
     '#hubfix:hover,#hubfix:active{background:var(--fg,#25221C);color:var(--bg,#F4F1E8);border-color:var(--fg,#25221C)}#hubfix:hover svg{transform:translateX(-2px)}'
     'html:root[data-skin=c] #hubfix,html:root[data-skin=f] #hubfix{position:absolute;left:4px;top:50%;margin:-18px 0 0;width:36px;height:36px}'
     '@media (min-width:900px){'
     'html:root[data-skin=c] #hubfix,html:root[data-skin=f] #hubfix{position:fixed;z-index:70;top:12px;left:18px;margin:0;width:42px;height:42px;'
     '-webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px);box-shadow:0 2px 10px rgba(0,0,0,.08)}'
     'html:root[data-skin=c] #hubfix svg,html:root[data-skin=f] #hubfix svg{width:19px;height:19px}}'
     '</style>')
assert t.count('<title>Конспекты семинаров</title>')==1
t=t.replace('<title>Конспекты семинаров</title>','<title>Учёба</title>'+css,1)
old='<a class="brand" href="#" data-go="" aria-label="Все предметы">'
assert t.count(old)==1
t=t.replace(old,btn+old,1)
open(out,'w',encoding='utf-8').write(t);print('ok',len(t.encode()))
