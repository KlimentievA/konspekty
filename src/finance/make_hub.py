#!/usr/bin/env python3
"""Главная Hub с профилями. Из шаблона src/finance/hub.html (стили, масштаб, подсказка об установке) собирает:
  index.html         — выбор профиля (Артем / Настя) и ввод пароля;
  artem.html         — разделы Артема: Учёба и Финансы;
  nastya.html        — разделы Насти: Учёба;
  nastya-ucheba.html — Учёба Насти (пока пусто).
Пароль сверяется по SHA-256 (в коде лежит только хэш), после ввода запоминается в localStorage и куки на год.
Это замок от случайных посетителей: файлы сайта всё равно лежат в открытом репозитории.
Запуск из корня репозитория: python3 src/finance/make_hub.py"""
import hashlib, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TPL = open(os.path.join(ROOT, 'src', 'finance', 'hub.html'), encoding='utf-8').read()
PROF = {'artem': ('Артем', '11231', 'artem.html'), 'nastya': ('Настя', '1591', 'nastya.html')}
TOK = {p: hashlib.sha256(('hub:%s:%s' % (p, v[1])).encode()).hexdigest()[:24] for p, v in PROF.items()}

head = TPL[:TPL.index('<body>')]
tail_js = TPL[TPL.index('<script>\ntry{var t=localStorage.getItem'):TPL.index('</body>')]
foot = re.search(r'<div class="zmr">.*?</p>', TPL, re.S).group(0)


def gate(p):
    """Скрипт в самом начале <head>: без пароля — на главную, к вводу пароля, потом обратно."""
    return ("<script>(function(){var P='%s',T='%s';function ok(){try{if(localStorage.getItem('hub:auth:'+P)===T)return true}catch(e){}"
            "return document.cookie.indexOf('hub_'+P+'='+T)>=0}"
            "if(!ok()){document.documentElement.style.visibility='hidden';var f=location.pathname.slice(location.pathname.lastIndexOf('/')+1)||'index.html';"
            "location.replace('index.html?login='+P+'&next='+encodeURIComponent(f+location.search+location.hash))}"
            "else{try{localStorage.setItem('hub:auth:'+P,T)}catch(e){}}})();</script>") % (p, TOK[p])


EXTRA_CSS = """<style>
.top{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:-28px 0 26px}
.top a,.top button{display:inline-flex;align-items:center;gap:6px;height:36px;padding:0 14px;border:1px solid var(--line);border-radius:999px;background:var(--surface);color:var(--muted);font:500 13.5px/1 'IBM Plex Sans',system-ui,sans-serif;text-decoration:none;cursor:pointer}
.top a:hover,.top button:hover{color:var(--fg);border-color:var(--faint)}
.prof .card{font:inherit;text-align:left;cursor:pointer;color:inherit;min-height:170px}
.av{width:54px;height:54px;border-radius:50%;display:grid;place-items:center;font:600 24px/1 'Literata',Georgia,serif;color:var(--surface)}
.av.a{background:var(--a1)}.av.n{background:#7A5CC2}
:root[data-theme="dark"] .av.n{background:#A58BE8}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]) .av.n{background:#A58BE8}}
.lock{position:absolute;top:18px;right:18px;display:inline-flex;align-items:center;gap:6px;color:var(--faint);font-size:12.5px}
.lock svg{width:16px;height:16px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.lock.open{color:var(--a2)}
.empty{margin-top:30px;padding:38px 24px;border:1px dashed var(--line);border-radius:18px;text-align:center;color:var(--muted)}
.empty .ic{font:600 34px/1 'Literata',Georgia,serif;color:var(--faint);margin-bottom:10px}
/* окно ввода пароля */
.pin{position:fixed;inset:0;z-index:60;display:flex;align-items:flex-end;justify-content:center;background:rgba(0,0,0,.35);opacity:0;transition:opacity .2s}
.pin[hidden]{display:none}.pin.on{opacity:1}
.pin .sh{width:100%;max-width:420px;margin:0 12px calc(env(safe-area-inset-bottom,0px) + 12px);padding:22px 22px 18px;border:1px solid var(--line);border-radius:24px;background:var(--surface);
  box-shadow:0 20px 60px rgba(0,0,0,.25);transform:translateY(30px);transition:transform .35s cubic-bezier(.2,.9,.25,1);text-align:center}
.pin.on .sh{transform:none}
@media (min-width:700px){.pin{align-items:center}}
.pin .av{margin:0 auto 10px}
.pin b{display:block;font:600 21px/1.2 'Literata',Georgia,serif}
.pin small{display:block;margin-top:4px;color:var(--muted);font-size:14px}
.pin input{display:block;width:100%;margin:18px 0 6px;height:56px;border:1px solid var(--line);border-radius:16px;background:var(--bg);color:var(--fg);
  font:600 26px/1 'IBM Plex Sans',system-ui,sans-serif;letter-spacing:.45em;text-align:center;padding:0 0 0 .45em;outline:none}
.pin input:focus{border-color:var(--a2);box-shadow:0 0 0 3px color-mix(in srgb,var(--a2) 22%,transparent)}
.pin .err{min-height:20px;color:var(--a1);font-size:13.5px}
.pin .go{display:flex;width:100%;align-items:center;justify-content:center;height:50px;margin-top:6px;border:0;border-radius:999px;background:var(--a2);color:var(--surface);font:600 16px/1 'IBM Plex Sans',system-ui,sans-serif;cursor:pointer}
.pin .cancel{margin-top:6px;height:42px;width:100%;border:0;background:none;color:var(--muted);font:500 14.5px/1 'IBM Plex Sans',system-ui,sans-serif;cursor:pointer}
.pin.ok input{border-color:var(--a2);color:var(--a2)}
@keyframes shake{10%,90%{transform:translateX(-2px)}20%,80%{transform:translateX(4px)}30%,50%,70%{transform:translateX(-8px)}40%,60%{transform:translateX(8px)}}
.pin.bad input{animation:shake .45s}
@media (prefers-reduced-motion:reduce){.pin,.pin .sh{transition:none}.pin.bad input{animation:none}}
</style>"""

LOCK_CLOSED = '<svg viewBox="0 0 24 24"><rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/></svg>'
LOCK_OPEN = '<svg viewBox="0 0 24 24"><rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 0 1 7.5-2"/></svg>'


OLDLINK = "<script>\n/* старые ссылки вида …/#civil-1 ведут в конспекты */\n(function(){var h=location.hash;if(h&&h.length>1)location.replace('ucheba.html'+h)})();\n</script>"
assert OLDLINK in head, 'oldlink'

def page(title, body, gate_p=None, apple_title='Hub'):
    h = head.replace('<title>Hub</title>', '<title>%s</title>' % title)
    if gate_p: h = h.replace(OLDLINK, '')
    if gate_p:
        h = h.replace('<meta charset="utf-8">', '<meta charset="utf-8">' + gate(gate_p), 1)
    h = h.replace('</head>', EXTRA_CSS + '</head>', 1)
    return h + '<body>\n' + body + '\n' + tail_js + '</body></html>\n'


def topbar(back_href, back_text, logout=None):
    lo = ('<button type="button" data-logout="%s">Выйти</button>' % logout) if logout else ''
    return ('<div class="top"><a href="%s"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" '
            'stroke-linecap="round" stroke-linejoin="round"><path d="M15 6l-6 6 6 6"/></svg>%s</a>%s</div>') % (back_href, back_text, lo)


LOGOUT_JS = ("<script>document.addEventListener('click',function(e){var b=e.target.closest&&e.target.closest('[data-logout]');if(!b)return;"
             "var p=b.getAttribute('data-logout');try{localStorage.removeItem('hub:auth:'+p)}catch(x){}"
             "document.cookie='hub_'+p+'=; max-age=0; path=/';location.href='index.html'});</script>")

# ---------------- index.html: выбор профиля ----------------
cards = ''.join(
    '<button type="button" class="card pf" data-p="%s"><span class="lock" data-lock="%s">%s<em>пароль</em></span>'
    '<div class="av %s">%s</div><b>%s</b><span>%s</span></button>' % (p, p, LOCK_CLOSED, 'a' if p == 'artem' else 'n', v[0][0], v[0],
                                                                      'Учёба и финансы' if p == 'artem' else 'Учёба')
    for p, v in PROF.items())
index_body = ('<div class="w">\n  <h1>Hub</h1>\n  <p class="lead">Выбери профиль.</p>\n  <div class="cards prof">' + cards + '</div>\n  ' + foot + '\n</div>\n'
              '<div class="pin" hidden><div class="sh" role="dialog" aria-modal="true"><div class="av" id="pav"></div><b id="pname"></b><small>Введи пароль</small>'
              '<input id="pin" type="password" inputmode="numeric" autocomplete="off" maxlength="12" aria-label="Пароль"><div class="err" id="perr"></div>'
              '<button type="button" class="go" id="pgo">Войти</button><button type="button" class="cancel" id="pcancel">Отмена</button></div></div>\n'
              "<script>\n(function(){\n"
              "var PROF={" + ','.join("%s:{n:'%s',t:'%s',home:'%s',c:'%s'}" % (p, v[0], TOK[p], v[2], 'a' if p == 'artem' else 'n') for p, v in PROF.items()) + "};\n"
              "var OPEN='" + LOCK_OPEN.replace("'", "\\'") + "';\n"
              r"""function authed(p){try{if(localStorage.getItem('hub:auth:'+p)===PROF[p].t)return true}catch(e){}return document.cookie.indexOf('hub_'+p+'='+PROF[p].t)>=0}
function remember(p){try{localStorage.setItem('hub:auth:'+p,PROF[p].t)}catch(e){}document.cookie='hub_'+p+'='+PROF[p].t+'; max-age=31536000; path=/; SameSite=Lax'}
function sha(s){if(!(window.crypto&&crypto.subtle))return Promise.resolve('');return crypto.subtle.digest('SHA-256',new TextEncoder().encode(s)).then(function(b){return Array.prototype.map.call(new Uint8Array(b),function(x){return ('0'+x.toString(16)).slice(-2)}).join('').slice(0,24)})}
Object.keys(PROF).forEach(function(p){if(authed(p)){var l=document.querySelector('[data-lock="'+p+'"]');l.className='lock open';l.innerHTML=OPEN+'<em>открыто</em>'}});
var q=new URLSearchParams(location.search),nextUrl=q.get('next')||'';if(!/^[a-z][a-z0-9\-]*\.html([?#].*)?$/i.test(nextUrl))nextUrl='';
var box=document.querySelector('.pin'),inp=document.getElementById('pin'),err=document.getElementById('perr'),cur=null,busy=false;
function go(p){location.href=(nextUrl&&cur===p&&q.get('login')===p)?nextUrl:PROF[p].home}
function open(p){cur=p;var av=document.getElementById('pav');av.className='av '+PROF[p].c;av.textContent=PROF[p].n.charAt(0);document.getElementById('pname').textContent=PROF[p].n;
  err.textContent='';inp.value='';box.classList.remove('ok','bad');box.hidden=false;requestAnimationFrame(function(){box.classList.add('on');setTimeout(function(){inp.focus()},60)})}
function close(){box.classList.remove('on');setTimeout(function(){box.hidden=true},220);cur=null}
function check(final){var p=cur,v=inp.value.trim();if(!p||!v||busy)return;busy=true;
  sha('hub:'+p+':'+v).then(function(h){busy=false;if(h===PROF[p].t){remember(p);box.classList.add('ok');err.textContent='';setTimeout(function(){go(p)},180)}
    else if(final){box.classList.remove('bad');void inp.offsetWidth;box.classList.add('bad');err.textContent='Неверный пароль';inp.select()}})}
document.querySelectorAll('.pf').forEach(function(b){b.addEventListener('click',function(){var p=b.getAttribute('data-p');if(authed(p)){cur=p;go(p)}else open(p)})});
inp.addEventListener('input',function(){err.textContent='';box.classList.remove('bad');check(false)});
inp.addEventListener('keydown',function(e){if(e.key==='Enter')check(true);if(e.key==='Escape')close()});
document.getElementById('pgo').onclick=function(){check(true)};
document.getElementById('pcancel').onclick=close;
box.addEventListener('click',function(e){if(e.target===box)close()});
var lp=q.get('login');if(lp&&PROF[lp]){if(authed(lp)){cur=lp;go(lp)}else open(lp)}
})();
</script>
""")
# старые ссылки вида …/#civil-1 по-прежнему ведут в конспекты (через проверку пароля Артема)
index_html = page('Hub', index_body)

# ---------------- artem.html ----------------
cards_artem = re.search(r'<div class="cards">.*?\n  </div>', TPL, re.S).group(0)
artem_body = ('<div class="w">\n  ' + topbar('index.html', 'Профили', 'artem') + '\n  <h1>Артем</h1>\n  <p class="lead">Учёба и финансы. Выбери раздел.</p>\n  '
              + cards_artem + '\n  ' + foot + '\n</div>\n' + LOGOUT_JS)
artem_html = page('Hub · Артем', artem_body, 'artem')

# ---------------- nastya.html ----------------
nastya_cards = ('<div class="cards">\n    <div class="card u"><a class="cover" href="nastya-ucheba.html" aria-label="Учёба"></a>\n'
                '      <div class="ic">§</div><b>Учёба</b><span>Конспекты и материалы — скоро</span>\n'
                '      <div class="links"><a href="nastya-ucheba.html">Открыть</a></div>\n    </div>\n  </div>')
nastya_body = ('<div class="w">\n  ' + topbar('index.html', 'Профили', 'nastya') + '\n  <h1>Настя</h1>\n  <p class="lead">Выбери раздел.</p>\n  '
               + nastya_cards + '\n  ' + foot + '\n</div>\n' + LOGOUT_JS)
nastya_html = page('Hub · Настя', nastya_body, 'nastya')

nu_body = ('<div class="w">\n  ' + topbar('nastya.html', 'Настя') + '\n  <h1>Учёба</h1>\n  <p class="lead">Раздел Насти.</p>\n'
           '  <div class="empty"><div class="ic">§</div>Здесь пока ничего нет.<br>Скоро появятся конспекты и материалы.</div>\n</div>\n')
nu_html = page('Учёба · Настя', nu_body, 'nastya')

# замок для страниц Артема (ucheba.html, finance.html) — его вставляют make_ucheba.py и build_finance.py
open(os.path.join(ROOT, 'src', 'finance', 'gate_artem.html'), 'w', encoding='utf-8').write(gate('artem'))

for name, html in (('index.html', index_html), ('artem.html', artem_html), ('nastya.html', nastya_html), ('nastya-ucheba.html', nu_html)):
    open(os.path.join(ROOT, name), 'w', encoding='utf-8').write(html)
    print('ok', name, len(html))
