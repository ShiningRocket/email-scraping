"""
Browser arcade games embedded via Streamlit components (works offline, no iframe blocks).
Inspired by classic arcade mechanics — colorful for kids & teens.
"""

from __future__ import annotations

import streamlit.components.v1 as components

ARCADE_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<style>
  * { box-sizing: border-box; }
  body {
    margin: 0; font-family: 'Segoe UI', system-ui, sans-serif;
    background: linear-gradient(160deg, #1e1b4b 0%, #312e81 40%, #4c1d95 100%);
    color: #e0e7ff; padding: 10px; min-height: 480px;
  }
  h2 { margin: 0 0 8px 0; font-size: 1.1rem; text-align: center; }
  .tabs { display: flex; gap: 6px; flex-wrap: wrap; justify-content: center; margin-bottom: 10px; }
  .tabs button {
    padding: 8px 14px; border: none; border-radius: 999px; cursor: pointer;
    font-weight: 700; font-size: 0.85rem;
    background: #6366f1; color: white; transition: transform .1s, background .2s;
  }
  .tabs button:hover { transform: scale(1.05); background: #818cf8; }
  .tabs button.on { background: #f472b6; color: #1e1b4b; }
  .panel { display: none; text-align: center; }
  .panel.on { display: block; }
  canvas {
    display: block; margin: 8px auto; border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0,0,0,.4); background: #0f172a;
    touch-action: none;
  }
  .score { font-size: 1.25rem; font-weight: 800; margin: 6px 0; color: #fde047; }
  .hint { font-size: 0.78rem; opacity: .85; margin-top: 6px; }
  .btn { padding: 6px 16px; margin: 4px; border-radius: 8px; border: none;
    background: #22d3ee; color: #0f172a; font-weight: 700; cursor: pointer; }
</style>
</head>
<body>
<h2>🎮 Mini arcade</h2>
<div class="tabs">
  <button type="button" class="on" data-p="p1">🐍 Snake</button>
  <button type="button" data-p="p2">🍎 Fruit catch</button>
  <button type="button" data-p="p3">🎯 Tap targets</button>
</div>

<div id="p1" class="panel on">
  <div class="score" id="s1">Score: 0</div>
  <canvas id="c1" width="380" height="380"></canvas>
  <p class="hint">Arrows or WASD · Eat dots · Don't hit walls or yourself</p>
  <button class="btn" onclick="resetSnake()">Restart</button>
</div>
<div id="p2" class="panel">
  <div class="score" id="s2">Score: 0 · Lives: ❤️❤️❤️</div>
  <canvas id="c2" width="380" height="400"></canvas>
  <p class="hint">← → or A D · Catch fruits · Avoid rocks</p>
  <button class="btn" onclick="resetCatch()">Restart</button>
</div>
<div id="p3" class="panel">
  <div class="score" id="s3">Score: 0 · Time left: 30s</div>
  <canvas id="c3" width="380" height="400"></canvas>
  <p class="hint">Click / tap the colorful targets before they shrink!</p>
  <button class="btn" onclick="resetTap()">Restart</button>
</div>

<script>
(function(){
  document.querySelectorAll('.tabs button').forEach(function(b){
    b.addEventListener('click', function(){
      document.querySelectorAll('.tabs button').forEach(x=>x.classList.remove('on'));
      document.querySelectorAll('.panel').forEach(x=>x.classList.remove('on'));
      b.classList.add('on');
      document.getElementById(b.dataset.p).classList.add('on');
    });
  });

  /* ---- SNAKE ---- */
  var W=20,H=20,cell=19, cx=document.getElementById('c1'), g1=cx.getContext('2d');
  var snake, dir, food, score1, tick, go1;
  function randFood(){
    do { food = [Math.floor(Math.random()*W), Math.floor(Math.random()*H)]; }
    while(snake.some(function(s){ return s[0]===food[0]&&s[1]===food[1]; }));
  }
  function resetSnake(){
    clearInterval(tick); go1=true;
    snake=[[10,10],[9,10],[8,10]]; dir=[1,0]; score1=0;
    randFood(); document.getElementById('s1').textContent='Score: 0';
    draw1();
    tick=setInterval(step1, 110);
  }
  function step1(){
    if(!go1) return;
    var h=[snake[0][0]+dir[0], snake[0][1]+dir[1]];
    if(h[0]<0||h[0]>=W||h[1]<0||h[1]>=H||snake.some(function(s,i){return i&&s[0]===h[0]&&s[1]===h[1];})){
      go1=false; clearInterval(tick); return;
    }
    snake.unshift(h);
    if(h[0]===food[0]&&h[1]===food[1]){ score1++; document.getElementById('s1').textContent='Score: '+score1; randFood(); }
    else snake.pop();
    draw1();
  }
  function draw1(){
    g1.fillStyle='#0f172a'; g1.fillRect(0,0,cx.width,cx.height);
    for(var i=0;i<snake.length;i++){
      var s=snake[i];
      g1.fillStyle = i===0 ? '#a7f3d0' : '#34d399';
      g1.fillRect(s[0]*cell+1,s[1]*cell+1,cell-2,cell-2);
    }
    g1.fillStyle='#f472b6';
    g1.beginPath();
    g1.arc(food[0]*cell+cell/2, food[1]*cell+cell/2, cell/2-2, 0, 6.283);
    g1.fill();
  }
  document.addEventListener('keydown', function(e){
    if(!document.getElementById('p1').classList.contains('on')) return;
    var k=e.key.toLowerCase();
    if((k==='arrowup'||k==='w')&&dir[1]!==1) dir=[0,-1];
    if((k==='arrowdown'||k==='s')&&dir[1]!==-1) dir=[0,1];
    if((k==='arrowleft'||k==='a')&&dir[0]!==1) dir=[-1,0];
    if((k==='arrowright'||k==='d')&&dir[0]!==-1) dir=[1,0];
  });
  resetSnake();

  /* ---- FRUIT CATCH ---- */
  var c2=document.getElementById('c2'), g2=c2.getContext('2d');
  var bx, items, score2, lives, anim2, em=['🍎','🍌','🍇','🍊','🍓'], bad='🪨';
  function resetCatch(){
    cancelAnimationFrame(anim2); bx=190; items=[]; score2=0; lives=3; go2=true; last2=0;
    loop2();
  }
  var go2, last2;
  function loop2(t){
    if(!document.getElementById('p2').classList.contains('on')){ anim2=requestAnimationFrame(loop2); return; }
    if(!go2){ anim2=requestAnimationFrame(loop2); return; }
    if(!last2) last2=t;
    var dt=t-last2; last2=t;
    if(Math.random()<0.018) items.push({x:40+Math.random()*300,y:-30,v:1.5+Math.random()*2.5,bad:Math.random()<0.22});
    g2.fillStyle='#1e293b'; g2.fillRect(0,0,c2.width,c2.height);
    g2.fillStyle='#334155'; for(var i=0;i<8;i++) g2.fillRect(i*50, (i*37)%400, 3, 400);
    items=items.filter(function(it){
      it.y+=it.v*(dt/16);
      if(it.y>c2.height+20) return false;
      if(it.y>340 && it.y<370 && Math.abs(it.x-bx)<42){
        if(it.bad){ lives--; if(lives<=0) go2=false; }
        else score2+=10;
        return false;
      }
      return true;
    });
    items.forEach(function(it){
      g2.font='28px serif'; g2.textAlign='center';
      g2.fillText(it.bad?bad:em[Math.floor(it.x)%em.length], it.x, it.y);
    });
    g2.fillStyle='#6366f1'; g2.fillRect(bx-42, 358, 84, 32);
    g2.fillStyle='#c4b5fd'; g2.fillRect(bx-38, 363, 76, 22);
    var h='❤️'.repeat(Math.max(0,lives))+'🖤'.repeat(3-Math.max(0,lives));
    document.getElementById('s2').textContent='Score: '+score2+' · Lives: '+h+(go2?'':' GAME OVER');
    anim2=requestAnimationFrame(loop2);
  }
  document.addEventListener('keydown', function(e){
    if(!document.getElementById('p2').classList.contains('on')) return;
    if(e.key==='ArrowLeft'||e.key==='a') bx=Math.max(45,bx-18);
    if(e.key==='ArrowRight'||e.key==='d') bx=Math.min(335,bx+18);
  });
  c2.addEventListener('mousemove', function(ev){
    if(!document.getElementById('p2').classList.contains('on')) return;
    var r=c2.getBoundingClientRect(); bx=Math.max(45, Math.min(335, ev.clientX-r.left));
  });
  c2.addEventListener('touchmove', function(ev){
    ev.preventDefault();
    if(!document.getElementById('p2').classList.contains('on')) return;
    var r=c2.getBoundingClientRect();
    bx=Math.max(45, Math.min(335, ev.touches[0].clientX-r.left));
  }, {passive:false});
  resetCatch();

  /* ---- TAP TARGETS ---- */
  var c3=document.getElementById('c3'), g3=c3.getContext('2d');
  var targets, score3, tleft, tapInt, go3;
  var cols=['#f472b6','#22d3ee','#a3e635','#fbbf24','#c084fc'];
  function resetTap(){
    clearInterval(tapInt); score3=0; tleft=30; go3=true; targets=[];
    tapInt=setInterval(function(){
      if(!document.getElementById('p3').classList.contains('on')) return;
      if(!go3) return;
      tleft-=0.1;
      if(tleft<=0){ go3=false; return; }
      if(Math.random()<0.45) spawnT();
      targets.forEach(function(t){ t.r-=1.2; });
      targets=targets.filter(function(t){ return t.r>4; });
      draw3();
      document.getElementById('s3').textContent='Score: '+Math.floor(score3)+' · Time: '+Math.max(0,tleft).toFixed(1)+'s';
    }, 100);
  }
  function spawnT(){
    targets.push({
      x:50+Math.random()*280, y:50+Math.random()*300,
      r:38+Math.random()*15, c:cols[Math.floor(Math.random()*cols.length)]
    });
  }
  function draw3(){
    g3.fillStyle='#0c4a6e'; g3.fillRect(0,0,c3.width,c3.height);
    targets.forEach(function(t){
      g3.beginPath(); g3.arc(t.x,t.y,t.r,0,7);
      g3.fillStyle=t.c; g3.globalAlpha=0.9; g3.fill(); g3.globalAlpha=1;
      g3.strokeStyle='#fff'; g3.lineWidth=3; g3.stroke();
    });
  }
  c3.addEventListener('click', function(ev){
    if(!go3) return;
    var r=c3.getBoundingClientRect(), x=ev.clientX-r.x, y=ev.clientY-r.y;
    targets=targets.filter(function(t){
      var d=Math.hypot(x-t.x,y-t.y);
      if(d<t.r){ score3+=100/t.r; return false; }
      return true;
    });
  });
  c3.addEventListener('touchstart', function(ev){
    if(!go3) return;
    ev.preventDefault();
    var r=c3.getBoundingClientRect(), x=ev.touches[0].clientX-r.x, y=ev.touches[0].clientY-r.y;
    targets=targets.filter(function(t){
      var d=Math.hypot(x-t.x,y-t.y);
      if(d<t.r){ score3+=100/t.r; return false; }
      return true;
    });
  }, {passive:false});
  resetTap();
})();
</script>
</body>
</html>
"""


def render_arcade(height: int = 540) -> None:
    components.html(ARCADE_HTML, height=height, scrolling=False)


def render_external_game_links() -> None:
    """Curated kid-friendly / casual games that open in a new tab (external sites)."""
    import streamlit as st

    st.markdown("##### 🌐 More games online (opens in new tab)")
    st.caption("Parental guidance suggested — these are popular public game sites.")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.link_button("🧩 Poki (1000+ games)", "https://poki.com/", use_container_width=True)
    with c2:
        st.link_button("🎲 CrazyGames", "https://www.crazygames.com/", use_container_width=True)
    with c3:
        st.link_button("♟️ Coolmath Games", "https://www.coolmathgames.com/", use_container_width=True)
