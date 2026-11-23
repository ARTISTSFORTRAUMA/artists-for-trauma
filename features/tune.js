/* Live tuning panel for feature articles. Opens only when the URL ends in ?tune.
   Adjusts the opening-box variables on the real page; "Copy settings" puts them on the clipboard. */
(function(){
  if(!/[?&]tune\b/.test(location.search))return;
  var hero=document.querySelector('.hero');if(!hero)return;
  var cs=getComputedStyle(hero);if(!cs.getPropertyValue('--gap-name').trim())return;
  var C=[
    ['Space above profile line','--gap-top',0,200,1,'px'],
    ['Space under profile line','--gap-eyebrow',0,120,1,'px'],
    ['Name size','--name-size',3,12,.1,'rem'],
    ['Name line spacing','--name-lh',.6,1.3,.01,''],
    ['Space under name','--gap-name',0,120,1,'px'],
    ['Title size','--deck-size',1,5,.05,'rem'],
    ['Title line spacing','--deck-lh',.8,1.6,.01,''],
    ['Space between title lines','--deck-gap',0,60,1,'px'],
    ['Space above credits','--gap-deck',0,140,1,'px']
  ];
  var K=[['First name','.hero h1','color'],['Last name','.hero h1 span','color'],['Title line 1','.hero .deck b','color'],['Title line 2','.hero .deck','color'],['Profile line & credits','.hero .eyebrow, .hero .credits','color']];
  var st=document.createElement('style');document.head.appendChild(st);var col={};
  function css(){st.textContent=Object.keys(col).map(function(s){return s+'{color:'+col[s]+' !important}'}).join('\n')}
  var p=document.createElement('div');p.id='tune';
  p.innerHTML='<style>#tune{position:fixed;right:12px;bottom:12px;z-index:9999;width:300px;max-height:80vh;overflow:auto;background:#fff;color:#000;font:14px/1.3 -apple-system,Helvetica,Arial,sans-serif;border:1px solid #ccc;border-radius:8px;box-shadow:0 8px 30px rgba(0,0,0,.25);padding:12px}#tune h4{margin:0 0 8px;font-size:15px;display:flex;justify-content:space-between}#tune label{display:block;margin:8px 0 2px}#tune input[type=range]{width:100%}#tune .row{display:flex;justify-content:space-between;align-items:center;margin:6px 0}#tune button{font:600 13px -apple-system,Helvetica,Arial;padding:8px 10px;border:0;border-radius:6px;background:#000;color:#fff;cursor:pointer;margin-top:10px;width:100%}#tune .min{background:none;color:#000;width:auto;margin:0;padding:0 4px;font-size:18px}#tune.c>:not(h4){display:none}</style><h4>Opening box <button class="min" title="Hide">–</button></h4>';
  C.forEach(function(c){
    var v=parseFloat(cs.getPropertyValue(c[1]))||c[2];
    var l=document.createElement('label');l.innerHTML=c[0]+': <b>'+v+c[5]+'</b>';
    var r=document.createElement('input');r.type='range';r.min=c[2];r.max=c[3];r.step=c[4];r.value=v;r.dataset.v=c[1];r.dataset.u=c[5];
    r.oninput=function(){hero.style.setProperty(c[1],r.value+c[5]);l.querySelector('b').textContent=r.value+c[5]};
    p.appendChild(l);p.appendChild(r);
  });
  K.forEach(function(k){
    var el=document.querySelector(k[1].split(',')[0]);var rgb=getComputedStyle(el).color.match(/\d+/g).slice(0,3);
    var hex='#'+rgb.map(function(x){return(+x).toString(16).padStart(2,'0')}).join('');
    var d=document.createElement('div');d.className='row';d.innerHTML='<span>'+k[0]+'</span>';
    var i=document.createElement('input');i.type='color';i.value=hex;i.oninput=function(){col[k[1]]=i.value;css()};
    d.appendChild(i);p.appendChild(d);
  });
  var b=document.createElement('button');b.textContent='Copy settings to send to Claude';
  b.onclick=function(){
    var out=['Opening box settings for '+location.pathname];
    p.querySelectorAll('input[type=range]').forEach(function(r){out.push(r.previousSibling.textContent)});
    Object.keys(col).forEach(function(s){out.push(K.filter(function(k){return k[1]===s})[0][0]+' colour: '+col[s])});
    var t=out.join('\n');
    (navigator.clipboard?navigator.clipboard.writeText(t):Promise.reject()).then(function(){b.textContent='Copied. Paste it in the chat.'},function(){prompt('Copy these settings:',t)});
  };
  p.appendChild(b);
  var r=document.createElement('button');r.textContent='Reset';r.style.background='#777';r.onclick=function(){location.reload()};p.appendChild(r);
  p.querySelector('.min').onclick=function(){p.classList.toggle('c')};
  document.body.appendChild(p);
})();
