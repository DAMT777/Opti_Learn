// CSRF helper
function getCookie(name){
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}
const csrftoken = getCookie('csrftoken');

const el = (sel)=>document.querySelector(sel);
let chatRef = null; const getChat = () => (chatRef || (chatRef = document.getElementById('chat')));
const historyBox = el('#history');
let collapseBtn = null;
let expandBtn = null;
let heroRef = null; const getHero = () => (heroRef || (heroRef = document.getElementById('hero')));

// Markdown rendering helpers (Marked + DOMPurify via CDN)
function renderMarkdownToHTML(text){
  try{
    if(window.marked){
      const raw = window.marked.parse(String(text||''), { breaks: true });
      if(window.DOMPurify){
        return window.DOMPurify.sanitize(raw, { USE_PROFILES: { html: true } });
      }
      return raw;
    }
  }catch{}
  // Fallback: escape basic
  return String(text||'').replace(/</g,'&lt;');
}

function attachPlotForPayload(payload, bubble){
  if(!payload || !payload.plot || !bubble) return;
  const iterations = Array.isArray(payload.plot.iterations) ? payload.plot.iterations : [];
  if(!iterations.length) return;
  const bubbleEl = bubble.closest('.bubble') || bubble;
  if(!bubbleEl) return;
  const existingChart = bubbleEl.querySelector('.assistant-plot');
  if(existingChart){
    existingChart.remove();
  }
  const chart = document.createElement('div');
  chart.className = 'assistant-plot';
  chart.dataset.plotMethod = payload.plot.method || 'graph';
  const md = bubbleEl.querySelector('.md');
  if(md){
    md.insertAdjacentElement('afterend', chart);
  } else {
    bubbleEl.appendChild(chart);
  }
  if(window.Plotly){
    const varNames = Array.isArray(payload.plot.variables) ? payload.plot.variables : [];
    const data = [];
    if(varNames.length >= 2){
      const xs = iterations.map(it => Array.isArray(it.x_k) ? it.x_k[0] : null);
      const ys = iterations.map(it => Array.isArray(it.x_k) ? it.x_k[1] : null);
      if(xs.some(v=>v !== null) && ys.some(v=>v !== null)){
        data.push({
          x: xs,
          y: ys,
          mode: 'lines+markers',
          name: 'Trayectoria',
          marker: { color: '#6bc8ff' },
          line: { color: '#6bc8ff', width: 2 },
        });
      }
    }
    const fkValues = iterations.map(it => (typeof it.f_k === 'number' ? it.f_k : null));
    if(fkValues.some(v=>v !== null)){
      data.push({
        y: fkValues,
        mode: 'lines+markers',
        name: 'Objetivo f(x)',
        marker: { color: '#ffe066' },
        line: { color: '#ffe066', dash: 'dash' },
      });
    }
    if(!data.length){
      chart.textContent = 'Sin datos numéricos para graficar.';
      return;
    }
    const layout = {
      title: payload.plot.title || `Método ${payload.plot.method || 'desconocido'}`,
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
      margin: { t: 28, b: 28, l: 40, r: 16 },
      font: { color: 'rgba(30,40,70,0.85)' },
      legend: { orientation: 'h', y: -0.25 },
      height: 280,
      width: 520,
      dragmode: 'pan',
    };
    const config = {
      responsive: true,
      displayModeBar: true,
      scrollZoom: true,
      modeBarButtonsToRemove: ['sendDataToCloud', 'hoverCompareCartesian'],
    };
    Plotly.newPlot(chart, data, layout, config);
  } else {
    chart.textContent = 'Gráfica disponible (Plotly no cargado).';
  }
}

function addMsg(role, text){
  const wrap = document.createElement('div');
  wrap.className = `msg ${role}`;
  let inner = '';
  if(role === 'assistant'){
    const html = renderMarkdownToHTML(text);
    inner = `<div class="bubble"><div class="md">${html}</div></div>`;
  } else {
    const safe = String(text).replace(/</g,'&lt;');
    inner = `<div class="bubble">${safe}</div>`;
  }
  wrap.innerHTML = inner;
  (getChat()||document.body).appendChild(wrap);
  const _c=getChat(); if(_c){ _c.scrollTop = _c.scrollHeight; }
  { const h=getHero(); if(h){ h.style.display='none'; } }
  // Render LaTeX si agregamos directamente un mensaje del asistente
  if(role === 'assistant'){
    try{
      if(window.MathJax && window.MathJax.typesetPromise){
        window.requestAnimationFrame(()=> window.MathJax.typesetPromise([wrap]));
      }
    }catch{}
  }
  updateEmptyState();
}

// Estado de escritura del asistente
let typingBubble = null; // apunta al elemento .bubble de la última burbuja de asistente en escritura
function showTyping(){
  // Si ya existe, no duplicar
  if(typingBubble && typingBubble.isConnected) return typingBubble;
  const wrap = document.createElement('div');
  wrap.className = 'msg assistant';
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  const dots = document.createElement('span');
  dots.className = 'typing-dots';
  dots.innerHTML = '<i></i><i></i><i></i>';
  bubble.appendChild(dots);
  wrap.appendChild(bubble);
  (getChat()||document.body).appendChild(wrap);
  const _c=getChat(); if(_c){ _c.scrollTop = _c.scrollHeight; }
  typingBubble = bubble;
  { const h=getHero(); if(h){ h.style.display='none'; } }
  updateEmptyState();
  return typingBubble;
}
function clearTyping(){ if(typingBubble && typingBubble.isConnected){ typingBubble.parentElement?.remove(); } typingBubble=null; }

// Escribe texto en la burbuja con efecto "typewriter"
function streamIntoBubble(text, onComplete){
  const bubble = typingBubble || showTyping();
  // Usar textContent para evitar HTML injection y preservar con CSS white-space
  bubble.textContent = '';
  // Velocidad: ~150 pasos máx (~3 s). Ajuste por longitud
  const total = String(text||'');
  const steps = Math.min(150, Math.max(30, Math.ceil(total.length/4)));
  const chunk = Math.max(1, Math.ceil(total.length / steps));
  let i = 0;
  const timer = setInterval(()=>{
    i += chunk;
    if(i >= total.length){
      // Al terminar el tipeo, renderizamos como Markdown seguro
      const html = renderMarkdownToHTML(total);
      bubble.innerHTML = `<div class="md">${html}</div>`;
      // Render LaTeX si MathJax está disponible
      try{
        if(window.MathJax && window.MathJax.typesetPromise){
          window.MathJax.typesetPromise([bubble]);
        }
      }catch{}
      clearInterval(timer);
      typingBubble = null; // finalizado
      const _c=getChat(); if(_c){ _c.scrollTop = _c.scrollHeight; }
      if(typeof onComplete === 'function'){ window.requestAnimationFrame(()=> onComplete(bubble)); }
      return;
    }
    bubble.textContent = total.slice(0, i);
    const _c=getChat(); if(_c){ _c.scrollTop = _c.scrollHeight; }
  }, 20);
}

// WebSocket chat
let ws;
function connectWS(){
  const sid = (window.OPTI && window.OPTI.CHAT_SESSION_ID) ? window.OPTI.CHAT_SESSION_ID : '';
  if(!sid) return;
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  setConnStatus('connecting');
  ws = new WebSocket(`${proto}://${location.host}/ws/chat/${sid}/`);
  ws.onopen = ()=> setConnStatus('online');
  ws.onclose = ()=> setConnStatus('offline');
  ws.onerror = ()=> setConnStatus('offline');
  ws.onmessage = (e)=>{
    try {
      const msg = JSON.parse(e.data);
      if(msg.type==='assistant_message'){
        streamIntoBubble(msg.text||'', (bubble)=> attachPlotForPayload(msg.payload, bubble));
      }
    } catch{}
  };
}

document.addEventListener('DOMContentLoaded', ()=>{
  // Theme init
  const saved = localStorage.getItem('theme')||'dark';
  document.body.classList.toggle('theme-dark', saved==='dark');
  document.body.classList.toggle('theme-light', saved==='light');
  const t = el('#themeToggle');
  if(t){
    t.checked = (saved==='dark');
    t.addEventListener('change', ()=>{
      const dark = t.checked;
      document.body.classList.add('theme-transition');
      document.body.classList.toggle('theme-dark', dark);
      document.body.classList.toggle('theme-light', !dark);
      localStorage.setItem('theme', dark ? 'dark' : 'light');
      setTimeout(()=> document.body.classList.remove('theme-transition'), 450);
    });
  }

  // Query buttons now that DOM is ready
  collapseBtn = el('#collapseBtn');
  expandBtn = el('#expandBtn');

  // Sidebar collapse state
  const savedSidebar = localStorage.getItem('sidebar')||'shown';
  if(savedSidebar==='hidden') document.body.classList.add('sidebar-hidden');
  if(collapseBtn){ collapseBtn.addEventListener('click', ()=>{
    document.body.classList.toggle('sidebar-hidden');
    localStorage.setItem('sidebar', document.body.classList.contains('sidebar-hidden') ? 'hidden' : 'shown');
  }); }
  if(expandBtn){ expandBtn.addEventListener('click', ()=>{
    document.body.classList.remove('sidebar-hidden');
    localStorage.setItem('sidebar','shown');
  }); }

  // Connect WS and send messages
  connectWS();
  const sendBtn = el('#sendBtn');
  const input = el('#chatInput');
  // Menú lateral (overlay)
  const menuBtn = el('#menuBtn');
  const menuClose = el('#menuClose');
  const backdrop = el('#sideBackdrop');
  const openMenu = ()=> document.body.classList.add('menu-open');
  const closeMenu = ()=> document.body.classList.remove('menu-open');
  if(menuBtn){ menuBtn.addEventListener('click', openMenu); }
  if(menuClose){ menuClose.addEventListener('click', closeMenu); }
  if(backdrop){ backdrop.addEventListener('click', closeMenu); }
  // Cerrar al hacer click fuera del panel aunque el backdrop no capture eventos
  document.addEventListener('click', (ev)=>{
    const t = ev.target;
    if(!document.body.classList.contains('menu-open')) return;
    if(!t) return;
    const insidePanel = (t.closest && t.closest('#sidePanel'));
    const onMenuBtn = (t.id === 'menuBtn' || (t.closest && t.closest('#menuBtn')));
    if(!insidePanel && !onMenuBtn){ closeMenu(); }
  }, true);
  document.addEventListener('keydown', (ev)=>{ if(ev.key==='Escape'){ closeMenu(); }});
  const doSend = ()=>{
    if(!input) return;
    const text = (input.value || '').trim();
    if(!text) return;
    addMsg('user', text);
    showTyping();
    if(ws && ws.readyState === 1){
      try { ws.send(JSON.stringify({type:'user_message', text})); } catch {}
    } else {
      // Fallback HTTP cuando WS no está conectado
      const sid = (window.OPTI && window.OPTI.CHAT_SESSION_ID) ? window.OPTI.CHAT_SESSION_ID : '';
      fetch('/api/ai/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrftoken || ''
        },
        body: JSON.stringify({ text, session_id: sid })
      }).then(r=>r.json()).then(data=>{
        if(data && data.text){ streamIntoBubble(data.text); } else { clearTyping(); }
      }).catch(()=>{ clearTyping(); });
    }
    input.value = '';
  };
  if(sendBtn){ sendBtn.addEventListener('click', doSend); }
  if(input){
    input.addEventListener('keydown', (ev)=>{
      if(ev.key === 'Enter' && !ev.shiftKey){ ev.preventDefault(); doSend(); }
    });
  }
  // Delegación por si el DOM re-renderiza elementos
  document.addEventListener('click', (ev)=>{
    const target = ev.target;
    if(!target) return;
    if(target.id === 'sendBtn' || target.closest && target.closest('#sendBtn')){
      ev.preventDefault();
      doSend();
    }
  });

  try{ if(historyBox) renderHistory(JSON.parse(localStorage.getItem('opti_hist')||'[]')); }catch{}
  updateEmptyState();
});

function renderHistory(items){
  if(!historyBox) return;
  historyBox.innerHTML = items.map(i=>`<div class="small">#${i.id.slice(0,8)} · f*=${i.f}</div>`).join('');
}

function updateEmptyState(){
  if(!getChat()) return;
  const hasMessages = getChat().querySelector('.msg') !== null;
  if(hasMessages){
    document.body.classList.remove('is-empty');
  } else {
    { const h=getHero(); if(h){ h.style.display='block'; } }
    document.body.classList.add('is-empty');
  }
}

function setConnStatus(state){
  const el = document.getElementById('connStatus');
  if(!el) return;
  el.classList.remove('online','offline','connecting');
  el.classList.add(state);
  const label = el.querySelector('.label');
  if(label){
    label.textContent = state === 'online' ? 'Conectado' : state === 'connecting' ? 'Conectando...' : 'Desconectado';
  }
}
