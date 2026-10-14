(function(){
var Z=[0.8,0.9,1,1.1,1.2,1.3,1.45,1.6];
function g(){try{var v=parseFloat(localStorage.getItem('siteZoom'));return v>0?v:1}catch(e){return 1}}
function ap(v){document.documentElement.style.zoom=(v===1?'':String(v))}
ap(g());
window.siteZoomGet=g;
window.siteZoom=function(d){var v=g(),i=Z.indexOf(v);if(i<0)i=2;i=d===0?2:Math.max(0,Math.min(Z.length-1,i+d));v=Z[i];try{localStorage.setItem('siteZoom',String(v))}catch(e){}ap(v);
  document.querySelectorAll('.szv').forEach(function(o){o.textContent=Math.round(v*100)+'%'});try{window.dispatchEvent(new Event('resize'))}catch(e){}return v};
document.addEventListener('click',function(e){var b=e.target.closest&&e.target.closest('[data-sz]');if(!b)return;e.preventDefault();e.stopPropagation();siteZoom(+b.getAttribute('data-sz'))},true);
window.addEventListener('storage',function(e){if(e.key==='siteZoom')ap(g())});
document.addEventListener('DOMContentLoaded',function(){var v=g();document.querySelectorAll('.szv').forEach(function(o){o.textContent=Math.round(v*100)+'%'})});
})();
/* Hub: service worker (мгновенная загрузка из кэша), тихое обновление до новой версии, фоновая подгрузка соседних разделов */
(function(){
  if(!('serviceWorker' in navigator)||!/^https?:$/.test(location.protocol))return;
  try{navigator.serviceWorker.register('sw.js').catch(function(){})}catch(e){}
  var t0=Date.now(),touched=false,shown=false;
  ['pointerdown','keydown','scroll','touchstart'].forEach(function(ev){window.addEventListener(ev,function(){touched=true},{passive:true,once:true})});
  function page(u){u=(u||'').replace(/[?#].*$/,'');var f=u.slice(u.lastIndexOf('/')+1);return f||'index.html'}
  navigator.serviceWorker.addEventListener('message',function(e){
    if(!e.data||e.data.t!=='hub-updated'||shown||page(e.data.url)!==page(location.href))return;
    shown=true;
    var rk='hubReload:'+page(location.href),last=0;try{last=+sessionStorage.getItem(rk)||0}catch(er){}
    if(Date.now()-last<30000)return;                                  // эта страница только что перезагрузилась на свежую версию
    if(!touched&&Date.now()-t0<3000){try{sessionStorage.setItem(rk,String(Date.now()))}catch(er){}location.reload();return}      // ещё ничего не трогали — просто подменяем на свежую версию
    var d=document.createElement('div');
    d.setAttribute('role','status');
    d.style.cssText='position:fixed;left:50%;bottom:calc(env(safe-area-inset-bottom,0px) + 16px);transform:translate(-50%,140%);z-index:9999;display:flex;align-items:center;gap:12px;padding:8px 8px 8px 16px;border-radius:999px;border:1px solid var(--line,#D9D3C2);background:var(--surface,#FBF9F3);color:var(--fg,#25221C);box-shadow:0 10px 30px rgba(0,0,0,.18);font:500 14px/1.2 system-ui,sans-serif;white-space:nowrap;transition:transform .4s cubic-bezier(.2,.9,.25,1)';
    d.innerHTML='<span>Hub обновился</span><button type="button" style="border:0;border-radius:999px;padding:9px 14px;background:var(--a2,var(--accent,#1F6B57));color:#fff;font:600 14px/1 system-ui,sans-serif;cursor:pointer">Обновить</button>';
    d.querySelector('button').onclick=function(){try{sessionStorage.setItem(rk,String(Date.now()))}catch(er){}location.reload()};
    document.body.appendChild(d);requestAnimationFrame(function(){requestAnimationFrame(function(){d.style.transform='translate(-50%,0)'})});
  });
  function ask(){var c=navigator.serviceWorker.controller;if(c)c.postMessage({t:'hub-check',url:location.href})}
  ask();setTimeout(ask,1500);setTimeout(ask,4000);
  window.addEventListener('load',function(){setTimeout(function(){
    try{if(navigator.connection&&navigator.connection.saveData)return}catch(e){}
    ['index.html','finance.html','ucheba.html'].forEach(function(p){if(page(location.href)!==p)fetch(p).catch(function(){})});
  },5000)});
})();
