#!/usr/bin/env python3
"""Шифрует данные сайта паролем. python3 encrypt.py ПАРОЛЬ [src/index.src.html] [index.html]
Берёт открытый исходник, прячет три блока данных (data, sched, tickets) и код приложения
в AES-256-GCM (ключ из пароля, PBKDF2-SHA256), добавляет окно ввода пароля."""
import sys,re,json,os,base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
pw=sys.argv[1]; src=sys.argv[2] if len(sys.argv)>2 else 'src/index.src.html'; out=sys.argv[3] if len(sys.argv)>3 else 'index.html'
t=open(src).read()
ITER=250000
bundle={}
for i in ('data','sched','tickets'):
    m=re.search(r'<script type="application/json" id="%s">(.*?)</script>\n?'%i,t,re.S)
    bundle[i]=m.group(1); t=t.replace(m.group(0),'',1)
scripts=[m for m in re.finditer(r'<script>(.*?)</script>',t,re.S)]
app=scripts[-1]; assert 'function renderHome' in app.group(1)
bundle['app']=app.group(1); t=t.replace(app.group(0),'',1)
salt=os.urandom(16); iv=os.urandom(12)
key=PBKDF2HMAC(algorithm=hashes.SHA256(),length=32,salt=salt,iterations=ITER).derive(pw.encode())
ct=AESGCM(key).encrypt(iv,json.dumps(bundle,ensure_ascii=False).encode(),None)
b=lambda x:base64.b64encode(x).decode()
enc=json.dumps({'s':b(salt),'v':b(iv),'i':ITER,'c':b(ct)})
gate_css='''<style>
#gate{position:fixed;inset:0;z-index:9999;display:flex;align-items:center;justify-content:center;padding:24px;background:#F4F1E8;color:#25221C;font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
@media (prefers-color-scheme:dark){#gate{background:#171611;color:#E8E4D8}#gate input{background:#22211A!important;color:#E8E4D8!important;border-color:#4a463a!important}}
#gate form{width:100%;max-width:320px;text-align:center}
#gate h1{margin:0 0 20px;font:600 26px/1.2 Georgia,serif}
#gate h1 span{color:#A93D28}
#gate input{box-sizing:border-box;width:100%;height:48px;padding:0 14px;border:1px solid #bdb6a3;border-radius:12px;background:#fff;font:inherit;font-size:17px;text-align:center}
#gate button{margin-top:12px;width:100%;height:48px;border:0;border-radius:12px;background:#A93D28;color:#fff;font:600 16px system-ui,sans-serif;cursor:pointer}
#gate p{min-height:1.5em;margin:12px 0 0;color:#B3261E;font-size:14px}
</style>'''
gate_html='<div id="gate" hidden><form id="gf"><h1><span>§</span> Конспекты</h1><input id="gp" type="password" placeholder="Пароль" autocomplete="current-password" autofocus><button type="submit">Войти</button><p id="ge"></p></form></div>'
gate_js='''<script type="application/json" id="enc">%s</script>
<script>
(function(){
var enc=JSON.parse(document.getElementById('enc').textContent),g=document.getElementById('gate');
function b64(s){return Uint8Array.from(atob(s),function(c){return c.charCodeAt(0)})}
function save(k,v){try{localStorage.setItem(k,v)}catch(e){}}
function load(k){try{return localStorage.getItem(k)}catch(e){return null}}
function open(k){return crypto.subtle.decrypt({name:'AES-GCM',iv:b64(enc.v)},k,b64(enc.c)).then(function(p){return JSON.parse(new TextDecoder().decode(p))})}
function start(b){
  ['data','sched','tickets'].forEach(function(id){var s=document.createElement('script');s.type='application/json';s.id=id;s.textContent=b[id];document.body.appendChild(s)});
  g.hidden=true;var a=document.createElement('script');a.textContent=b.app;document.body.appendChild(a);
}
function fromRaw(raw){return crypto.subtle.importKey('raw',raw,'AES-GCM',true,['decrypt'])}
function fromPw(pw){
  return crypto.subtle.importKey('raw',new TextEncoder().encode(pw),'PBKDF2',false,['deriveKey']).then(function(m){
    return crypto.subtle.deriveKey({name:'PBKDF2',salt:b64(enc.s),iterations:enc.i,hash:'SHA-256'},m,{name:'AES-GCM',length:256},true,['decrypt'])})
}
function ask(){
  g.hidden=false;var f=document.getElementById('gf'),i=document.getElementById('gp'),e=document.getElementById('ge');i.focus();
  f.onsubmit=function(ev){ev.preventDefault();e.textContent='';
    fromPw(i.value.trim()).then(function(k){return open(k).then(function(b){
      crypto.subtle.exportKey('raw',k).then(function(r){save('pk',btoa(String.fromCharCode.apply(null,new Uint8Array(r))))});start(b)})})
    .catch(function(){e.textContent='Неверный пароль';i.select()})}
}
if(!window.crypto||!crypto.subtle){g.hidden=false;document.getElementById('gf').innerHTML='<p>Нужен защищённый адрес (https).</p>';return}
var sk=load('pk');
if(sk){fromRaw(b64(sk)).then(open).then(start).catch(function(){save('pk','');ask()})}else ask();
})();
</script>'''%enc
# вставка: стили в head, окно и скрипт перед </html>/в конец
assert '</html>' in t
t=t.replace('</html>',gate_css+gate_html+'\n'+gate_js+'\n</html>',1) if '</body>' not in t else t.replace('</body>',gate_css+gate_html+'\n'+gate_js+'\n</body>',1)
open(out,'w').write(t); print('ok',len(t.encode()))
