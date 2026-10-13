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
