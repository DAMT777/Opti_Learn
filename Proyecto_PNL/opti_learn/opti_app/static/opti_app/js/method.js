const el = (s)=>document.querySelector(s);
const csrftoken = (document.cookie.match(/csrftoken=([^;]+)/)||[])[1]||'';
const sections = {
  resultMain: el('#resultMain'),
  resultDetails: el('#resultDetails'),
  resultInterpretation: el('#resultInterpretation'),
  errors: el('#methodErrors'),
  iterations: el('#iters'),
  plots: {
    contour: el('#plotContour'),
    surface: el('#plotSurface'),
    fx: el('#plotFx'),
  },
};
let lastPlotData = null;

function initTheme(){
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
      renderMethodPlots(lastPlotData);
    });
  }
  const menuBtn = el('#menuBtn');
  const menuClose = el('#menuClose');
  const backdrop = el('#sideBackdrop');
  const openMenu = ()=> document.body.classList.add('menu-open');
  const closeMenu = ()=> document.body.classList.remove('menu-open');
  if(menuBtn){ menuBtn.addEventListener('click', openMenu); }
  if(menuClose){ menuClose.addEventListener('click', closeMenu); }
  if(backdrop){ backdrop.addEventListener('click', closeMenu); }
  document.addEventListener('keydown', (ev)=>{ if(ev.key==='Escape'){ closeMenu(); }});
  document.addEventListener('click', (ev)=>{
    if(!document.body.classList.contains('menu-open')) return;
    const inside = ev.target.closest && ev.target.closest('#sidePanel');
    const onBtn = ev.target.closest && ev.target.closest('#menuBtn');
    if(!inside && !onBtn){ closeMenu(); }
  }, true);
}

function parseConstraints(txt){
  if(!txt || !txt.trim()) return [];
  try{
    return JSON.parse(txt);
  }catch{
    showMethodError('No se pudo interpretar el JSON de restricciones. Revisa comillas y llaves.');
    return [];
  }
}

function parseVectorInput(raw){
  if(!raw || !raw.trim()) return null;
  try{
    const value = JSON.parse(raw);
    if(Array.isArray(value)) return value.map(Number);
    if(typeof value === 'number') return [value];
  }catch{
    const parts = raw.replace(/[\[\]\(\)\{\}]/g,'').split(/[,;\s]+/).filter(Boolean);
    if(parts.length){
      const parsed = parts.map(Number);
      if(parsed.every(v=>!Number.isNaN(v))) return parsed;
    }
  }
  showMethodError('Formato de x₀ inválido. Usa notación como [0.5, -1].');
  return null;
}

function collectOptionalParams(){
  const x0Raw = el('#x0')?.value || '';
  const tolRaw = el('#tol')?.value || '';
  const maxIterRaw = el('#maxIter')?.value || '';
  const result = {};
  if(x0Raw.trim()){
    const parsed = parseVectorInput(x0Raw);
    if(parsed) result.x0 = parsed;
  }
  if(tolRaw.trim()){
    const tol = parseFloat(tolRaw);
    if(!Number.isNaN(tol)) result.tol = tol;
  }
  if(maxIterRaw.trim()){
    const maxIter = parseInt(maxIterRaw, 10);
    if(!Number.isNaN(maxIter)) result.max_iter = maxIter;
  }
  return result;
}

function showMethodError(message){
  if(!sections.errors) return;
  if(message){
    sections.errors.textContent = message;
    sections.errors.classList.add('has-error');
  }else{
    sections.errors.textContent = 'Sin errores. Completa los campos y ejecuta el método.';
    sections.errors.classList.remove('has-error');
  }
}

function setResultSections(mainHtml, detailsHtml, interpretationHtml){
  if(sections.resultMain) sections.resultMain.innerHTML = mainHtml || '<div class="text-muted">Sin resultados.</div>';
  if(sections.resultDetails) sections.resultDetails.innerHTML = detailsHtml || '';
  if(sections.resultInterpretation) sections.resultInterpretation.innerHTML = interpretationHtml || '';
}

function resetOutputs(){
  setResultSections('', '', '');
  if(sections.iterations) sections.iterations.innerHTML = '';
  renderMethodPlots(null);
  showMethodError('');
}

function parseConstraintsField(){
  const field = el('#constraints');
  if(!field) return [];
  return parseConstraints(field.value||'') || [];
}

async function analyze(){
  resetOutputs();
  const objective = el('#objective')?.value.trim() || '';
  const variables = (el('#variables')?.value || '').split(',').map(s=>s.trim()).filter(Boolean);
  if(!objective || !variables.length){
    showMethodError('Debes ingresar una función y al menos una variable.');
    return;
  }
  const payload = {
    objective_expr: objective,
    variables,
    constraints: parseConstraintsField(),
  };
  try{
    const res = await fetch('/api/problems/parse', {
      method:'POST',
      headers:{'Content-Type':'application/json','X-CSRFToken':csrftoken},
      body: JSON.stringify(payload)
    });
    const meta = await res.json();
    if(!res.ok){
      showMethodError(meta.detail || meta.message || 'Error al analizar el problema.');
      return;
    }
    const summary = `
      <div><strong>Variables detectadas:</strong> ${meta.variables?.join(', ') || '-'}</div>
      <div><strong>Igualdades:</strong> ${meta.has_equalities ? 'Sí' : 'No'} • <strong>Desigualdades:</strong> ${meta.has_inequalities ? 'Sí' : 'No'}</div>
      <div><strong>¿Cuadrática?</strong> ${meta.is_quadratic ? 'Sí' : 'No'}</div>
    `;
    setResultSections('<div class="text-success">Análisis completado. Puedes resolver el método.</div>', summary, 'Revisa los campos opcionales antes de resolver para ajustar tolerancia o iteraciones.');
    showMethodError('');
  }catch(err){
    showMethodError('No se pudo analizar el problema. Revisa tu conexión.');
  }
}

async function solve(){
  showMethodError('');
  const method = window.OPTI?.METHOD || 'gradient';
  const objective = el('#objective')?.value.trim() || '';
  const variables = (el('#variables')?.value || '').split(',').map(s=>s.trim()).filter(Boolean);
  if(!objective || !variables.length){
    showMethodError('Debes ingresar la función objetivo y las variables.');
    return;
  }
  const problemPayload = {
    title: `Problema ${method}`,
    objective_expr: objective,
    variables,
    constraints_raw: parseConstraintsField(),
  };
  let problem;
  try{
    const create = await fetch('/api/problems/', {
      method:'POST',
      headers:{'Content-Type':'application/json','X-CSRFToken':csrftoken},
      body: JSON.stringify(problemPayload)
    });
    if(!create.ok){
      const data = await create.json();
      showMethodError(data.detail || 'No se pudo crear el problema.');
      return;
    }
    problem = await create.json();
  }catch(err){
    showMethodError('No se pudo crear el problema. Verifica la conexión.');
    return;
  }

  const optional = collectOptionalParams();
  try{
    const solRes = await fetch(`/api/problems/${problem.id}/solve`, {
      method:'POST',
      headers:{'Content-Type':'application/json','X-CSRFToken':csrftoken},
      body: JSON.stringify({
        method,
        x0: optional.x0,
        tol: optional.tol,
        max_iter: optional.max_iter,
      })
    });
    const sol = await solRes.json();
    if(!solRes.ok){
      showMethodError(sol.explanation_final || sol.message || 'El solver no pudo converger.');
      setResultSections('<div class="text-danger">No se obtuvo resultado.</div>', '', '');
      return;
    }
    const metrics = `
      <div class="metric">
        <div class="metric__label">f*</div>
        <div class="metric__value">${typeof sol.f_star === 'number' ? sol.f_star.toFixed(6) : (sol.f_star ?? '-')}</div>
      </div>
      <div class="metric">
        <div class="metric__label">x*</div>
        <div class="metric__value small">${JSON.stringify(sol.x_star)}</div>
      </div>
    `;
    const details = `
      <div><strong>Método:</strong> ${sol.method}</div>
      <div><strong>Estado:</strong> ${sol.status}</div>
      <div><strong>Iteraciones:</strong> ${sol.iterations_count ?? '-'}</div>
      <div><strong>Tiempo:</strong> ${sol.runtime_ms ?? '-'} ms</div>
    `;
    const interpretation = sol.explanation_final
      ? sol.explanation_final
      : `Después de ${sol.iterations_count ?? '-'} iteraciones se alcanzó el punto óptimo reportado.`;
    setResultSections(metrics, details, interpretation);
    renderMethodIterations(sol.iterations || []);
    renderMethodPlots(sol.plot_data || null);
    showMethodError('');
  }catch(err){
    showMethodError('No se pudo ejecutar el solver. Intenta nuevamente.');
  }
}

function renderMethodIterations(items){
  if(!sections.iterations) return;
  sections.iterations.innerHTML = '';
  const rows = Array.isArray(items) ? items : [];
  rows.forEach(it=>{
    const tr=document.createElement('tr');
    const fmt = (val)=> typeof val === 'number' ? val.toFixed(6) : (val ?? '');
    tr.innerHTML = `<td>${it.k ?? ''}</td><td>${fmt(it.f_k)}</td><td>${fmt(it.grad_norm)}</td><td>${fmt(it.step ?? it.alpha)}</td>`;
    sections.iterations.appendChild(tr);
  });
}

function getPlotTheme(){
  const dark = document.body.classList.contains('theme-dark');
  return dark ? {
    paper: 'rgba(0,0,0,0)',
    plot: 'rgba(0,0,0,0)',
    axis: 'rgba(236,242,255,0.9)',
    grid: 'rgba(255,255,255,0.25)',
    zero: 'rgba(255,255,255,0.6)',
    contourScale: 'Portland',
    surfaceScale: [
      [0, '#6da2ff'],
      [0.5, '#3c6df2'],
      [1, '#162b6a'],
    ],
  } : {
    paper: 'rgba(0,0,0,0)',
    plot: 'rgba(0,0,0,0)',
    axis: 'rgba(12,23,45,0.9)',
    grid: 'rgba(0,0,0,0.25)',
    zero: 'rgba(0,0,0,0.45)',
    contourScale: 'Portland',
    surfaceScale: [
      [0, '#dce9ff'],
      [0.5, '#76a7ff'],
      [1, '#0d55ce'],
    ],
  };
}

function renderMethodPlots(plotData){
  lastPlotData = plotData || null;
  const nodes = sections.plots;
  const placeholders = {
    contour: 'Curvas de nivel disponibles tras resolver.',
    surface: 'Superficie 3D disponible tras resolver.',
    fx: 'Evolución de f(xₖ) disponible tras resolver.',
  };
  Object.entries(nodes).forEach(([key,node])=>{
    if(!node) return;
    node.innerHTML = `<span>${placeholders[key]}</span>`;
  });
  if(!plotData || !window.Plotly){
    return;
  }
  const theme = getPlotTheme();
  if(nodes.contour){
    renderContourPlot(nodes.contour, plotData, theme);
  }
  if(nodes.surface){
    renderSurfacePlot(nodes.surface, plotData, theme);
  }
  if(nodes.fx){
    renderFxPlot(nodes.fx, plotData, theme);
  }
}

function renderContourPlot(node, plotData, theme){
  const mesh = plotData.mesh;
  if(!mesh || !mesh.x || !mesh.y || !mesh.z){
    node.innerHTML = '<span>No hay datos para curvas de nivel.</span>';
    return;
  }
  const heatTrace = {
    type: 'contour',
    x: mesh.x,
    y: mesh.y,
    z: mesh.z,
    colorscale: theme.contourScale,
    contours: {
      coloring: 'heatmap',
      showlines: false,
    },
    showscale: false,
    opacity: 0.75,
  };
  const lineTrace = {
    type: 'contour',
    x: mesh.x,
    y: mesh.y,
    z: mesh.z,
    contours: {
      coloring: 'lines',
      showlabels: false,
    },
    line: { width: 1.3, color: theme.axis },
    showscale: false,
    opacity: 1,
  };
  const trail = plotData.trajectory || { x: [], y: [] };
  const trajectoryTrace = {
    x: trail.x,
    y: trail.y,
    mode: 'lines+markers',
    name: 'Trayectoria',
    marker: { size: 6, color: '#1f77b4' },
    line: { color: '#1f77b4', width: 3 },
  };
  const layout = {
    title: 'Curvas de nivel',
    height: 260,
    paper_bgcolor: theme.paper,
    plot_bgcolor: theme.plot,
    xaxis: { color: theme.axis, gridcolor: theme.grid },
    yaxis: { color: theme.axis, gridcolor: theme.grid },
    margin: { t: 50, b: 40, l: 40, r: 16 },
  };
  Plotly.newPlot(node, [heatTrace, lineTrace, trajectoryTrace], layout, {responsive:true, displayModeBar:false});
}

function renderSurfacePlot(node, plotData, theme){
  const mesh = plotData.mesh;
  if(!mesh || !mesh.x || !mesh.y || !mesh.z){
    node.innerHTML = '<span>No hay datos para la superficie.</span>';
    return;
  }
  const surface = {
    type: 'surface',
    x: mesh.x,
    y: mesh.y,
    z: mesh.z,
    colorscale: theme.surfaceScale,
    showscale: false,
    opacity: 0.9,
  };
  const trail = plotData.trajectory || { x: [], y: [], f: [] };
  const trajectoryTrace = {
    type: 'scatter3d',
    mode: 'lines+markers',
    x: trail.x,
    y: trail.y,
    z: trail.f,
    line: { width: 4, color: '#1f77b4' },
    marker: { size: 3, color: '#ffe066' },
    name: 'Trayectoria',
  };
  const layout = {
    title: 'Superficie 3D',
    paper_bgcolor: theme.paper,
    scene: {
      xaxis: { color: theme.axis, gridcolor: theme.grid },
      yaxis: { color: theme.axis, gridcolor: theme.grid },
      zaxis: { color: theme.axis, gridcolor: theme.grid },
    },
    margin: { t: 40, b: 10, l: 10, r: 10 },
  };
  Plotly.newPlot(node, [surface, trajectoryTrace], layout, {responsive:true, displayModeBar:false});
}

function renderFxPlot(node, plotData, theme){
  const fx = plotData.fx_curve;
  if(!fx || !Array.isArray(fx.f) || !fx.f.length){
    node.innerHTML = '<span>No hay datos de f(xₖ).</span>';
    return;
  }
  const trace = {
    x: fx.iter || fx.f.map((_,idx)=>idx),
    y: fx.f,
    mode: 'lines+markers',
    line: { color: '#ff7f0e', width: 3 },
    marker: { size: 5 },
    name: 'f(xₖ)',
  };
  const layout = {
    title: 'Evolución f(xₖ)',
    paper_bgcolor: theme.paper,
    plot_bgcolor: theme.plot,
    xaxis: { title: 'Iteración', color: theme.axis, gridcolor: theme.grid },
    yaxis: { title: 'f(xₖ)', color: theme.axis, gridcolor: theme.grid },
    margin: { t: 40, b: 40, l: 50, r: 20 },
  };
  Plotly.newPlot(node, [trace], layout, {responsive:true, displayModeBar:false});
}

function resetForm(){
  document.querySelectorAll('#objective, #variables, #constraints, #x0, #tol, #maxIter').forEach(input=>{
    if(input) input.value = '';
  });
  resetOutputs();
}

document.addEventListener('DOMContentLoaded', ()=>{
  initTheme();
  const analyzeBtn = el('#analyzeBtn');
  const solveBtn = el('#solveBtn');
  const resetBtn = el('#resetBtn');
  if(analyzeBtn) analyzeBtn.addEventListener('click', analyze);
  if(solveBtn) solveBtn.addEventListener('click', solve);
  if(resetBtn) resetBtn.addEventListener('click', resetForm);
  document.querySelectorAll('.form-control').forEach(inp=>{
    inp.addEventListener('focus', ()=> inp.scrollIntoView({block:'center', behavior:'smooth'}));
  });
});
