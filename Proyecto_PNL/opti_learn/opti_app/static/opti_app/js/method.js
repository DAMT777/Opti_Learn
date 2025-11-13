const el = (s)=>document.querySelector(s);
const csrftoken = (document.cookie.match(/csrftoken=([^;]+)/)||[])[1]||'';

// Theme toggle
function initTheme(){
  const saved = localStorage.getItem('theme')||'dark';
  document.body.classList.toggle('theme-dark', saved==='dark');
  document.body.classList.toggle('theme-light', saved==='light');
  const t = el('#themeToggle'); if(t){
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
  // Sidebar collapse
  const collapseBtn = el('#collapseBtn');
  const expandBtn = el('#expandBtn');
  const savedSidebar = localStorage.getItem('sidebar')||'shown';
  if(savedSidebar==='hidden') document.body.classList.add('sidebar-hidden');
  if(collapseBtn){ collapseBtn.addEventListener('click', ()=>{
    const hidden = document.body.classList.toggle('sidebar-hidden');
    localStorage.setItem('sidebar', hidden ? 'hidden' : 'shown');
  }); }
  if(expandBtn){ expandBtn.addEventListener('click', ()=>{
    document.body.classList.remove('sidebar-hidden');
    localStorage.setItem('sidebar','shown');
  }); }
}

function parseConstraints(txt){ if(!txt?.trim()) return []; try{ return JSON.parse(txt);}catch{ return [] } }

async function analyze(){
  const payload = {
    objective_expr: el('#objective').value.trim(),
    variables: el('#variables').value.split(',').map(s=>s.trim()).filter(Boolean),
    constraints: parseConstraints(el('#constraints')?.value||'')
  };
  const res = await fetch('/api/problems/parse', {
    method:'POST', headers:{'Content-Type':'application/json','X-CSRFToken':csrftoken}, body: JSON.stringify(payload)
  });
  if(!res.ok){ alert('Error de análisis'); return; }
  const meta = await res.json();
  alert(`Análisis: vars=${meta.variables?.join(',')||'-'} | eq=${meta.has_equalities} | ineq=${meta.has_inequalities} | quad=${meta.is_quadratic}`);
}

async function solve(){
  const method = window.OPTI?.METHOD || 'gradient';
  const create = await fetch('/api/problems/', {
    method:'POST', headers:{'Content-Type':'application/json','X-CSRFToken':csrftoken},
    body: JSON.stringify({
      title: `Problema ${method}`,
      objective_expr: el('#objective').value.trim(),
      variables: el('#variables').value.split(',').map(s=>s.trim()).filter(Boolean),
      constraints_raw: parseConstraints(el('#constraints')?.value||'')
    })
  });
  if(!create.ok){ alert('Error creando problema'); return; }
  const prob = await create.json();
  const solRes = await fetch(`/api/problems/${prob.id}/solve`, {
    method:'POST', headers:{'Content-Type':'application/json','X-CSRFToken':csrftoken},
    body: JSON.stringify({ method })
  });
  const sol = await solRes.json();
  const resultBox = el('#result'); const itersBody = el('#iters');
  if(!solRes.ok){ resultBox.innerHTML = `<div class="text-danger">${sol.explanation_final||'Error'}</div>`; return; }
  resultBox.innerHTML = `
    <div class="small">Método: <b>${sol.method}</b> • Estado: <b>${sol.status}</b></div>
    <div class="mt-1">f* = <code>${sol.f_star}</code></div>
    <div>x* = <code>${JSON.stringify(sol.x_star)}</code></div>
    <div class="text-dark-50 small">Iteraciones: ${sol.iterations_count} • ${sol.runtime_ms||'-'} ms</div>
  `;
  itersBody.innerHTML='';
  (sol.iterations||[]).forEach(it=>{
    const tr=document.createElement('tr');
    tr.innerHTML=`<td>${it.k}</td><td>${it.f_k??''}</td><td>${it.grad_norm??''}</td><td>${it.step??''}</td>`;
    itersBody.appendChild(tr);
  });
}

document.addEventListener('DOMContentLoaded', ()=>{
  initTheme();
  const a=el('#analyzeBtn'); if(a) a.addEventListener('click', analyze);
  const s=el('#solveBtn'); if(s) s.addEventListener('click', solve);
  // Dark inputs visibility tweak
  document.querySelectorAll('.form-control').forEach(inp=>{
    inp.addEventListener('focus', ()=> inp.scrollIntoView({block:'center', behavior:'smooth'}));
  });
});
