/* Live tuning panel for feature articles. Opens only when the URL ends in ?tune.
   Adjusts the opening-box variables on the real page; "Copy settings" puts them on the clipboard. */
(function(){
  if(!/[?&]tune\b/.test(location.search))return;
  var hero=document.querySelector('.hero');if(!hero)return;
  var cs=getComputedStyle(hero);var heroTune=!!cs.getPropertyValue('--gap-name').trim();
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
  p.innerHTML='<style>#tune{position:fixed;right:12px;bottom:12px;z-index:9999;width:300px;max-height:80vh;overflow:auto;background:#fff;color:#000;font:14px/1.3 -apple-system,Helvetica,Arial,sans-serif;border:1px solid #ccc;border-radius:8px;box-shadow:0 8px 30px rgba(0,0,0,.25);padding:12px}#tune h4{margin:0 0 8px;font-size:15px;display:flex;justify-content:space-between}#tune label{display:block;margin:8px 0 2px}#tune input[type=range]{width:100%}#tune .row{display:flex;justify-content:space-between;align-items:center;margin:6px 0}#tune button{font:600 13px -apple-system,Helvetica,Arial;padding:8px 10px;border:0;border-radius:6px;background:#000;color:#fff;cursor:pointer;margin-top:10px;width:100%}#tune .min{background:none;color:#000;width:auto;margin:0;padding:0 4px;font-size:18px}#tune.c>:not(h4){display:none}</style><h4>Tune <button class="min" title="Hide">–</button></h4>';
  if(!heroTune){C=[];K=[];}
  if(C.length){var hb=document.createElement('h4');hb.textContent='Opening box';hb.style.cssText='margin:14px 0 0;border-top:1px solid #ddd;padding-top:10px';p.appendChild(hb)}
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
    var out=['Settings for '+location.pathname];
    p.querySelectorAll('input[type=range][data-v]').forEach(function(r){out.push(r.previousSibling.textContent)});
    Object.keys(col).forEach(function(s){out.push(K.filter(function(k){return k[1]===s})[0][0]+' colour: '+col[s])});
    Object.keys(done).forEach(function(n){var v=done[n];out.push('Photo '+n+': zoom '+v.z+', left/right '+v.x+'%, up/down '+v.y+'%')});
    var t=out.join('\n');
    (navigator.clipboard?navigator.clipboard.writeText(t):Promise.reject()).then(function(){b.textContent='Copied. Paste it in the chat.'},function(){prompt('Copy these settings:',t)});
  };
  p.appendChild(b);

  /* ---- Photos: click a photo, then zoom and move it inside its box ---- */
  var ph=document.createElement('div');
  ph.innerHTML='<h4 style="margin:0 0 4px">Photos</h4><p class="hint" style="margin:0;color:#666">Click a photo on the page to select it.</p><div class="pc" hidden><p class="nm" style="margin:6px 0;font-weight:600"></p><label>Zoom: <b>1</b></label><input type=range min=1 max=3 step=.01 data-k=z><label>Left / right: <b>50</b>%</label><input type=range min=0 max=100 step=.5 data-k=x><label>Up / down: <b>50</b>%</label><input type=range min=0 max=100 step=.5 data-k=y></div>';
  p.insertBefore(ph,p.querySelector('h4').nextSibling);
  var sel=null,done={};
  var st2=document.createElement('style');st2.textContent='.tunewrap{display:block;overflow:hidden;border-radius:2px}.tunesel{outline:4px solid #f567af;outline-offset:-4px}main img{cursor:crosshair}';document.head.appendChild(st2);
  function nameOf(img){return img.getAttribute('src').split('/').pop()}
  function state(img){var o=(img.style.objectPosition||getComputedStyle(img).objectPosition).split(' ');
    var px=function(v){return /%$/.test(v)?parseFloat(v):(v==='left'||v==='top'?0:v==='right'||v==='bottom'?100:50)};
    var m=(img.style.transform||'').match(/scale\(([\d.]+)\)/);return{z:m?+m[1]:1,x:px(o[0]),y:px(o[1]||o[0])}}
  function wrap(img){if(img.closest('.ph,.tunewrap'))return;var w=document.createElement('span');w.className='tunewrap';img.parentNode.insertBefore(w,img);w.appendChild(img)}
  function apply(img,v){wrap(img);img.style.objectPosition=v.x+'% '+v.y+'%';img.style.transformOrigin=v.x+'% '+v.y+'%';img.style.transform='scale('+v.z+')';done[nameOf(img)]=v}
  var pc=ph.querySelector('.pc'),rs=pc.querySelectorAll('input');
  document.querySelector('main').addEventListener('click',function(e){
    var img=e.target.closest('img');if(!img||img.closest('.rack,#tune,header'))return;e.preventDefault();e.stopPropagation();
    if(sel)sel.classList.remove('tunesel');sel=img;img.classList.add('tunesel');
    var v=done[nameOf(img)]||state(img);pc.hidden=false;ph.querySelector('.hint').hidden=true;pc.querySelector('.nm').textContent=nameOf(img);
    rs.forEach(function(r){r.value=v[r.dataset.k];r.previousElementSibling.querySelector('b').textContent=v[r.dataset.k]});
    p.classList.remove('c');
  },true);
  rs.forEach(function(r){r.oninput=function(){if(!sel)return;var v={};rs.forEach(function(q){v[q.dataset.k]=+q.value;q.previousElementSibling.querySelector('b').textContent=q.value});apply(sel,v)}});
  var r=document.createElement('button');r.textContent='Reset';r.style.background='#777';r.onclick=function(){location.reload()};p.appendChild(r);
  p.querySelector('.min').onclick=function(){p.classList.toggle('c')};
  document.body.appendChild(p);
})();
