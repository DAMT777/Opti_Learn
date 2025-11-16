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

const METHOD_CONFIGS = {
  gradient: {
    title: 'Gradiente descendente',
    subtitle: 'Problemas sin restricciones (o ya parametrizados) resueltos con descenso por iteraciones.',
    placeholderObjective: '(x-1)**2 + (y-2)**2',
    placeholderVars: 'x,y',
    showConstraints: false,
    constraintsHint: '',
    solveLabel: 'Resolver gradiente',
  },
  lagrange: {
    title: 'Método de Lagrange',
    subtitle: 'Optimiza con restricciones de igualdad usando multiplicadores.',
    placeholderObjective: 'x**2 + y**2',
    placeholderVars: 'x,y',
    showConstraints: true,
    constraintsHint: 'Incluye restricciones de igualdad como [{"kind":"eq","expr":"x+y-1"}].',
    solveLabel: 'Resolver Lagrange',
  },
  kkt: {
    title: 'Condiciones KKT',
    subtitle: 'Adecuado cuando hay desigualdades (>= o <=).',
    placeholderObjective: '(x-3)**2 + (y+1)**2',
    placeholderVars: 'x,y',
    showConstraints: true,
    constraintsHint: 'Usa kind "eq" o "ineq": [{"kind":"ineq","expr":"x+y-2"}].',
    solveLabel: 'Resolver KKT',
  },
  qp: {
    title: 'Programación cuadrática',
    subtitle: 'Objetivo cuadrático con restricciones lineales o semidefinidas.',
    placeholderObjective: '0.5*x**2 + 12*y**2 - 6*x + 4*y + 8',
    placeholderVars: 'x,y',
    showConstraints: true,
    constraintsHint: 'Ingresa restricciones lineales en formato JSON. Ej: [{"kind":"ineq","expr":"x>=0"}].',
    solveLabel: 'Resolver QP',
  },
  differential: {
    title: 'Cálculo diferencial',
    subtitle: 'Derivadas clásicas para problemas sin restricciones, útil como repaso teórico.',
    placeholderObjective: 'x**3 - 3*x + 1',
    placeholderVars: 'x',
    showConstraints: false,
    constraintsHint: '',
    solveLabel: 'Resolver cálculo',
  },
};
const defaultMethodKey = 'gradient';
const methodState = { current: defaultMethodKey, busy: false };

function resolvePlotTheme(){
  const dark = document.body?.classList?.contains('theme-dark');
  return dark ? {
    paper: 'rgba(0,0,0,0)',
    plot: 'rgba(0,0,0,0)',
    axis: 'rgba(232,238,255,0.92)',
    grid: 'rgba(255,255,255,0.25)',
    zero: 'rgba(255,255,255,0.75)',
    font: 'rgba(236,242,255,0.96)',
    contourScale: 'Viridis',
    sceneBg: 'rgba(12,18,40,0.85)',
    surfaceScale: [
      [0, '#6da2ff'],
      [0.5, '#3c6df2'],
      [1, '#162b6a'],
    ],
    surfaceOpacity: 0.92,
  } : {
    paper: 'rgba(0,0,0,0)',
    plot: 'rgba(0,0,0,0)',
    axis: 'rgba(12,23,45,0.9)',
    grid: 'rgba(0,0,0,0.25)',
    zero: 'rgba(0,0,0,0.7)',
    font: 'rgba(14,25,54,0.95)',
    contourScale: 'Portland',
    sceneBg: 'rgba(245,249,255,0.95)',
    surfaceScale: [
      [0, '#dce9ff'],
      [0.5, '#76a7ff'],
      [1, '#0d55ce'],
    ],
    surfaceOpacity: 0.9,
  };
}

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

function initMethodPanel(){
  const panel = document.getElementById('methodPanel');
  if(!panel) return;
  const closeBtn = document.getElementById('methodPanelClose');
  const backdrop = panel.querySelector('.method-panel__backdrop');
  const analyzeBtn = document.getElementById('methodAnalyze');
  const solveBtn = document.getElementById('methodSolve');
  document.querySelectorAll('.overlay-sidebar .item-link[data-method]').forEach(link=>{
    link.addEventListener('click', (ev)=>{
      ev.preventDefault();
      const method = link.getAttribute('data-method') || defaultMethodKey;
      openMethodPanel(method);
    });
  });
  panel.querySelectorAll('[data-method-tab]').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      const method = btn.getAttribute('data-method-tab') || defaultMethodKey;
      openMethodPanel(method);
    });
  });
  if(closeBtn){ closeBtn.addEventListener('click', closeMethodPanel); }
  if(backdrop){ backdrop.addEventListener('click', closeMethodPanel); }
  document.addEventListener('keydown', (ev)=>{
    if(ev.key === 'Escape' && panel.classList.contains('is-open')){
      closeMethodPanel();
    }
  });
  if(analyzeBtn){ analyzeBtn.addEventListener('click', ()=> handleMethodAction('analyze')); }
  if(solveBtn){ solveBtn.addEventListener('click', ()=> handleMethodAction('solve')); }
  // Config inicial
  applyMethodConfig(defaultMethodKey);
}

function openMethodPanel(methodKey = defaultMethodKey){
  const panel = document.getElementById('methodPanel');
  if(!panel) return;
  const key = METHOD_CONFIGS[methodKey] ? methodKey : defaultMethodKey;
  methodState.current = key;
  applyMethodConfig(key);
  panel.classList.add('is-open');
  panel.setAttribute('aria-hidden', 'false');
  document.body.classList.add('method-panel-open');
  document.body.classList.remove('menu-open');
}

function closeMethodPanel(){
  const panel = document.getElementById('methodPanel');
  if(!panel) return;
  panel.classList.remove('is-open');
  panel.setAttribute('aria-hidden', 'true');
  document.body.classList.remove('method-panel-open');
}

function applyMethodConfig(methodKey){
  const cfg = METHOD_CONFIGS[methodKey] || METHOD_CONFIGS[defaultMethodKey];
  const titleEl = document.getElementById('methodPanelTitle');
  const subtitleEl = document.getElementById('methodPanelSubtitle');
  const objectiveEl = document.getElementById('methodObjective');
  const varsEl = document.getElementById('methodVariables');
  const constraintsGroup = document.querySelector('[data-field="constraints"]');
  const constraintsInput = document.getElementById('methodConstraints');
  const constraintsHint = document.getElementById('methodConstraintsHint');
  const solveBtn = document.getElementById('methodSolve');
  if(titleEl) titleEl.textContent = cfg.title;
  if(subtitleEl) subtitleEl.textContent = cfg.subtitle;
  if(objectiveEl && cfg.placeholderObjective) objectiveEl.placeholder = cfg.placeholderObjective;
  if(varsEl && cfg.placeholderVars) varsEl.placeholder = cfg.placeholderVars;
  if(constraintsGroup){
    constraintsGroup.classList.toggle('d-none', !cfg.showConstraints);
  }
  if(constraintsHint){
    constraintsHint.textContent = cfg.showConstraints ? (cfg.constraintsHint || '') : '';
  }
  if(!cfg.showConstraints && constraintsInput){
    constraintsInput.value = '';
  }
  if(solveBtn){
    solveBtn.textContent = cfg.solveLabel || `Resolver ${cfg.title}`;
    solveBtn.dataset.baseLabel = solveBtn.textContent;
  }
  document.querySelectorAll('[data-method-tab]').forEach(btn=>{
    const key = btn.getAttribute('data-method-tab');
    btn.classList.toggle('active', key === methodKey);
  });
}

function collectMethodPayload(){
  const objective = (document.getElementById('methodObjective')?.value || '').trim();
  const variables = (document.getElementById('methodVariables')?.value || '')
    .split(',')
    .map(v=>v.trim())
    .filter(Boolean);
  const constraintsRaw = document.getElementById('methodConstraints')?.value || '';
  let constraints = [];
  if(constraintsRaw.trim()){
    try{
      constraints = JSON.parse(constraintsRaw);
    }catch(error){
      throw new Error('Revisa el formato JSON de las restricciones.');
    }
  }
  return {
    objective_expr: objective,
    variables,
    constraints,
  };
}

function setMethodLoading(isLoading, action){
  const analyzeBtn = document.getElementById('methodAnalyze');
  const solveBtn = document.getElementById('methodSolve');
  methodState.busy = isLoading;
  [analyzeBtn, solveBtn].forEach(btn=>{
    if(btn){
      btn.disabled = isLoading;
    }
  });
  if(analyzeBtn){
    const base = analyzeBtn.dataset.baseLabel || analyzeBtn.textContent;
    analyzeBtn.dataset.baseLabel = base;
    analyzeBtn.innerHTML = (isLoading && action === 'analyze')
      ? '<span class="spinner-border spinner-border-sm me-2"></span>Analizando...'
      : base;
  }
  if(solveBtn){
    const base = solveBtn.dataset.baseLabel || solveBtn.textContent;
    solveBtn.dataset.baseLabel = base;
    solveBtn.innerHTML = (isLoading && action === 'solve')
      ? '<span class="spinner-border spinner-border-sm me-2"></span>Resolviendo...'
      : base;
  }
}

function showMethodResult(message, isError = false){
  const box = document.getElementById('methodResult');
  if(!box) return;
  box.innerHTML = message;
  box.classList.toggle('text-danger', isError);
  box.classList.toggle('text-muted', !isError);
  try{
    if(window.MathJax && window.MathJax.typesetPromise){
      window.MathJax.typesetPromise([box]);
    }
  }catch{}
}

function renderMethodIterations(items){
  const container = document.getElementById('methodIterations');
  const counter = document.getElementById('methodIterCount');
  if(!container) return;
  container.innerHTML = '';
  const rows = Array.isArray(items) ? items : [];
  rows.forEach(it=>{
    const tr = document.createElement('tr');
    const col = (val)=> (typeof val === 'number' ? Number(val).toFixed(6) : (val ?? ''));
    tr.innerHTML = `
      <td>${it.k ?? ''}</td>
      <td>${col(it.f_k)}</td>
      <td>${col(it.grad_norm)}</td>
      <td>${col(it.step)}</td>
    `;
    container.appendChild(tr);
  });
  if(counter){
    counter.textContent = `${rows.length} ${rows.length === 1 ? 'registro' : 'registros'}`;
  }
}

async function handleMethodAction(action){
  if(methodState.busy) return;
  const cfg = METHOD_CONFIGS[methodState.current] || METHOD_CONFIGS[defaultMethodKey];
  let payload;
  try{
    payload = collectMethodPayload();
  }catch(err){
    showMethodResult(`<span class="text-danger">${err.message}</span>`, true);
    return;
  }
  if(!payload.objective_expr || !payload.variables.length){
    showMethodResult('<span class="text-danger">Completa la función objetivo y al menos una variable.</span>', true);
    return;
  }
  setMethodLoading(true, action);
  try{
    if(action === 'analyze'){
      const response = await fetch('/api/problems/parse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken || '' },
        body: JSON.stringify({
          objective_expr: payload.objective_expr,
          variables: payload.variables,
          constraints: payload.constraints,
        })
      });
      const meta = await response.json();
      if(!response.ok){
        throw new Error(meta.detail || 'No se pudo analizar el problema.');
      }
      const text = `
        <div><strong>Variables:</strong> ${meta.variables?.join(', ') || '—'}</div>
        <div><strong>Igualdades:</strong> ${meta.has_equalities ? 'Sí' : 'No'} · <strong>Desigualdades:</strong> ${meta.has_inequalities ? 'Sí' : 'No'}</div>
        <div><strong>Cuadrática:</strong> ${meta.is_quadratic ? 'Sí' : 'No'} · <strong>Método sugerido:</strong> ${meta.method || cfg.title}</div>
      `;
      showMethodResult(text, false);
      renderMethodIterations([]);
      return;
    }
    // Crear problema y resolver
    const createRes = await fetch('/api/problems/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken || '' },
      body: JSON.stringify({
        title: `Problema ${methodState.current}`,
        objective_expr: payload.objective_expr,
        variables: payload.variables,
        constraints_raw: payload.constraints,
      })
    });
    const created = await createRes.json();
    if(!createRes.ok){
      throw new Error(created.detail || 'No se pudo guardar el problema.');
    }
    const solveRes = await fetch(`/api/problems/${created.id}/solve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken || '' },
      body: JSON.stringify({ method: methodState.current })
    });
    const sol = await solveRes.json();
    if(!solveRes.ok){
      showMethodResult(`<span class="text-danger">${sol.explanation_final || 'El solver no pudo converger.'}</span>`, true);
      renderMethodIterations(sol.iterations || []);
      return;
    }
    const html = `
      <div class="small text-uppercase text-muted mb-1">${sol.method || cfg.title}</div>
      <div><strong>Estado:</strong> ${sol.status || 'ok'} · <strong>Iteraciones:</strong> ${sol.iterations_count ?? '-'}</div>
      <div>f* = <code>${sol.f_star ?? '-'}</code></div>
      <div>x* = <code>${JSON.stringify(sol.x_star)}</code></div>
      <div class="text-muted small mt-1">${sol.runtime_ms ? `${sol.runtime_ms} ms` : ''}</div>
    `;
    showMethodResult(html, false);
    renderMethodIterations(sol.iterations || []);
  }catch(err){
    showMethodResult(`<span class="text-danger">${err.message || 'Ocurrió un error inesperado.'}</span>`, true);
  }finally{
    setMethodLoading(false, action);
  }
}

function attachPlotForPayload(payload, bubble){
  if(!payload || !payload.plot || !bubble) return;
  const plotData = payload.plot.plot_data;
  const bubbleEl = bubble.closest('.bubble') || bubble;
  if(!bubbleEl) return;
  bubbleEl.querySelectorAll('.assistant-plot').forEach(node => node.remove());
  if(plotData && plotData.mesh && window.Plotly){
    renderGradientPlots(plotData, bubbleEl, { surfaceOnly: false });
    return;
  }
  // Fallback legacy single plot
  const iterations = Array.isArray(payload.plot.iterations) ? payload.plot.iterations : [];
  if(!iterations.length) return;
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
    const theme = resolvePlotTheme();
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
      paper_bgcolor: theme.paper,
      plot_bgcolor: theme.plot,
      margin: { t: 60, b: 28, l: 40, r: 16 },
      font: { color: theme.font },
      legend: { orientation: 'h', y: -0.25 },
      height: 280,
      width: 520,
      dragmode: 'pan',
      xaxis: {
        color: theme.axis,
        gridcolor: theme.grid,
        zerolinecolor: theme.zero,
      },
      yaxis: {
        color: theme.axis,
        gridcolor: theme.grid,
        zerolinecolor: theme.zero,
      },
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

function renderGradientPlots(plotData, bubbleEl, options = { surfaceOnly: false }){
  const md = bubbleEl.querySelector('.md');
  const insertAfter = (el, node) => {
    if(el){
      el.insertAdjacentElement('afterend', node);
    } else {
      bubbleEl.appendChild(node);
    }
  };
  if(options.surfaceOnly){
    const surfaceChart = appendPlotBubble(bubbleEl, md, 'surface');
    renderSurface(surfaceChart, plotData);
    appendPlotInterpretation(surfaceChart, plotData);
    return;
  }
  const contourChart = appendPlotBubble(bubbleEl, md, 'contour');
  renderContour(contourChart, plotData, true);
  const surfaceChart = appendPlotBubble(bubbleEl, contourChart, 'surface');
  renderSurface(surfaceChart, plotData);
  appendPlotInterpretation(surfaceChart, plotData);
}

function appendPlotBubble(parent, refNode, modifier){
  const wrapper = document.createElement('div');
  wrapper.className = `assistant-plot assistant-plot--${modifier}`;
  if(refNode && refNode.parentElement){
    refNode.insertAdjacentElement('afterend', wrapper);
  } else {
    parent.appendChild(wrapper);
  }
  return wrapper;
}

function renderContour(chart, plotData){
  const mesh = plotData.mesh;
  if(!mesh || !mesh.x.length || !mesh.y.length) return;
  const theme = resolvePlotTheme();
  const trajectory = plotData.trajectory || { x: [], y: [] };
  const tx = Array.isArray(trajectory.x) ? trajectory.x.filter((v)=>typeof v === 'number') : [];
  const ty = Array.isArray(trajectory.y) ? trajectory.y.filter((v)=>typeof v === 'number') : [];
  const xMin = tx.length ? Math.min(...tx) : mesh.x[0];
  const xMax = tx.length ? Math.max(...tx) : mesh.x[mesh.x.length - 1];
  const yMin = ty.length ? Math.min(...ty) : mesh.y[0];
  const yMax = ty.length ? Math.max(...ty) : mesh.y[mesh.y.length - 1];
  const padRange = (min, max) => {
    let span = max - min;
    if (span === 0) {
      span = Math.abs(min) > 1 ? Math.abs(min) : 1;
      min -= span * 0.5;
      max += span * 0.5;
    }
    const pad = Math.max(span * 0.25, 2);
    return [min - pad, max + pad];
  };
  const xRange = padRange(xMin, xMax);
  const yRange = padRange(yMin, yMax);
  const zValues = mesh.z.flat ? mesh.z.flat() : [].concat(...mesh.z);
  const zMin = Math.min(...zValues);
  const zMax = Math.max(...zValues);
  const trajZ = Array.isArray(plotData.trajectory?.f)
    ? plotData.trajectory.f.filter((v) => typeof v === 'number')
    : [];
  let zStart = zMin;
  let zEnd = zMax;
  if (trajZ.length) {
    const localMin = Math.min(...trajZ);
    const localMax = Math.max(...trajZ);
    const localSpan = Math.max(localMax - localMin, 1e-3);
    const buffer = Math.max(localSpan * 0.6, 1);
    zStart = Math.max(zMin, localMin - buffer);
    zEnd = Math.min(zMax, localMax + buffer);
  }
  const contourStep = Math.max((zEnd - zStart) / 18, (zMax - zMin) / 40, 1e-3);
  const contourTrace = {
    type: 'contour',
    x: mesh.x,
    y: mesh.y,
    z: mesh.z,
    colorscale: theme.contourScale,
    contours: {
      coloring: 'heatmap',
      showlabels: false,
      start: zStart,
      end: zEnd,
      size: contourStep,
    },
    showscale: false,
    opacity: 0.85,
  };
  const trailTrace = {
    x: trajectory.x,
    y: trajectory.y,
    mode: 'lines+markers',
    name: 'Trayectoria',
    marker: { size: 6, color: '#1f77b4' },
    line: { color: '#1f77b4', width: 3, shape: 'spline' },
  };
  const config = {
    responsive: true,
    displayModeBar: true,
    scrollZoom: false,
    modeBarButtonsToRemove: ['sendDataToCloud', 'pan2d', 'select2d', 'lasso2d'],
  };
  const layout = {
    title: 'Curvas de nivel',
    paper_bgcolor: theme.paper,
    plot_bgcolor: theme.plot,
    margin: { t: 68, b: 28, l: 40, r: 16 },
    height: 260,
    legend: { orientation: 'h', y: -0.2 },
    xaxis: {
      showgrid: true,
      zeroline: true,
      range: xRange,
      gridcolor: theme.grid,
      color: theme.axis,
      zerolinewidth: 1.2,
      zerolinecolor: theme.zero,
      fixedrange: true,
    },
    yaxis: {
      showgrid: true,
      zeroline: true,
      range: yRange,
      gridcolor: theme.grid,
      color: theme.axis,
      zerolinewidth: 1.2,
      zerolinecolor: theme.zero,
      fixedrange: true,
    },
    dragmode: false,
  };
  Plotly.newPlot(chart, [contourTrace, trailTrace], layout, config);
  insertPlotLegend(chart, [
    { label: 'Curvas de nivel f(x,y)', color: '#6c757d' },
    { label: 'Trayectoria del gradiente', color: '#1f77b4' },
  ]);
}
function renderSurface(chart, plotData){
  const mesh = plotData.mesh;
  if(!mesh || ! mesh.x.length ) return;
  const theme = resolvePlotTheme();
  const trajectory = plotData.trajectory || { x: [], y: [], f: [] };
  const padLinear = (min, max) => {
    let span = max - min;
    if (span === 0) {
      span = Math.max(Math.abs(min), Math.abs(max), 1);
      min -= span * 0.5;
      max += span * 0.5;
    }
    const pad = Math.max(span * 0.3, 2);
    return [min - pad, max + pad];
  };
  const tx = Array.isArray(trajectory.x) ? trajectory.x.filter((v)=>typeof v === 'number') : [];
  const ty = Array.isArray(trajectory.y) ? trajectory.y.filter((v)=>typeof v === 'number') : [];
  const tf = Array.isArray(trajectory.f) ? trajectory.f.filter((v)=>typeof v === 'number') : [];
  const xDataMin = tx.length ? Math.min(...tx) : mesh.x[0];
  const xDataMax = tx.length ? Math.max(...tx) : mesh.x[mesh.x.length - 1];
  const yDataMin = ty.length ? Math.min(...ty) : mesh.y[0];
  const yDataMax = ty.length ? Math.max(...ty) : mesh.y[mesh.y.length - 1];
  const xRange = padLinear(xDataMin, xDataMax);
  const yRange = padLinear(yDataMin, yDataMax);
  const zValues = mesh.z.flat ? mesh.z.flat() : [].concat(...mesh.z);
  const zMin = tf.length ? Math.min(...tf) : Math.min(...zValues);
  const zMax = tf.length ? Math.max(...tf) : Math.max(...zValues);
  const zRange = padLinear(zMin, zMax);
  const surfaceTrace = {
    type: 'surface',
    x: mesh.x,
    y: mesh.y,
    z: mesh.z,
    colorscale: theme.surfaceScale,
    showscale: false,
    opacity: theme.surfaceOpacity,
  };
  const pathTrace = {
    type: 'scatter3d',
    mode: 'lines+markers',
    x: trajectory.x,
    y: trajectory.y,
    z: trajectory.f,
    marker: { size: 4, color: '#ffe066' },
    line: { width: 4, color: '#1f77b4' },
    name: 'Camino',
  };
  const layout = {
    title: 'Superficie',
    margin: { t: 70, b: 20, l: 20, r: 20 },
    scene: {
      aspectmode: 'cube',
      camera: { eye: { x: 1.2, y: -1.3, z: 0.9 } },
      xaxis: {
        title: 'x',
        gridcolor: theme.grid,
        zerolinecolor: theme.zero,
        color: theme.axis,
        range: xRange,
      },
      yaxis: {
        title: 'y',
        gridcolor: theme.grid,
        zerolinecolor: theme.zero,
        color: theme.axis,
        range: yRange,
      },
      zaxis: {
        title: 'f(x)',
        gridcolor: theme.grid,
        zerolinecolor: theme.zero,
        color: theme.axis,
        range: zRange,
      },
      backgroundcolor: theme.sceneBg,
    },
    paper_bgcolor: theme.paper,
  };
  const config = {
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ['sendDataToCloud'],
  };
  Plotly.newPlot(chart, [surfaceTrace, pathTrace], layout, config);
  insertPlotLegend(chart, [
    { label: 'Superficie f(x,y)', color: '#4267f5' },
    { label: 'Camino iterativo', color: '#ffe066' },
  ]);
}

function renderFxCurve(chart, plotData){
  const fx = plotData.fx_curve;
  if(!fx || !Array.isArray(fx.f)) return;
  const valid = fx.f.map((value, idx) => ({ idx, value })).filter(item => typeof item.value === 'number');
  if(!valid.length) return;
  const trace = {
    x: valid.map(item => item.idx),
    y: valid.map(item => item.value),
    mode: 'lines+markers',
    line: { shape: 'spline', color: '#ff7f0e', width: 3 },
    marker: { size: 5 },
    name: 'f(x_k)',
  };
  const layout = {
    title: 'Valor objetivo',
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    margin: { t: 28, b: 32, l: 44, r: 16 },
    xaxis: { title: 'Iteración' },
    yaxis: { title: 'f(x_k)' },
    height: 220,
  };
  const config = {
    responsive: true,
    displayModeBar: false,
  };
  Plotly.newPlot(chart, [trace], layout, config);
  insertPlotLegend(chart, [
    { label: 'Evolución f(x_k)', color: '#ff7f0e' },
  ]);
}

function appendPlotInterpretation(anchorChart, plotData){
  if(!anchorChart) return;
  const wrapper = document.createElement('div');
  wrapper.className = 'assistant-plot-note as-message';
  const iterCount = plotData.trajectory && Array.isArray(plotData.trajectory.x) ? plotData.trajectory.x.length : 0;
  const endX = (plotData.trajectory?.x ?? []).slice(-1)[0];
  const endY = (plotData.trajectory?.y ?? []).slice(-1)[0];
  const endF = (plotData.trajectory?.f ?? []).slice(-1)[0];
  const coords = [
    typeof endX === 'number' ? endX.toFixed(6) : '-',
    typeof endY === 'number' ? endY.toFixed(6) : '-',
  ];
  const fLabel = typeof endF === 'number' ? endF.toFixed(6) : '-';
  wrapper.innerHTML = `<strong>Interpretación de la gráfica:</strong> La línea amarilla registra el camino del gradiente descendente; tras ${iterCount} iteraciones converge al punto (${coords.join(', ')}) con f(x)≈${fLabel}. Observa cómo el modelo desciende por la superficie hasta el valle donde se hace mínima la función.`;
  anchorChart.insertAdjacentElement('afterend', wrapper);
}

function insertPlotLegend(chart, items){
  if(!Array.isArray(items) || !items.length) return;
  const legend = document.createElement('div');
  legend.className = 'assistant-plot__legend';
  items.forEach(({ label, color }) => {
    const node = document.createElement('span');
    node.className = 'assistant-plot__legend-item';
    const swatch = document.createElement('span');
    swatch.className = 'assistant-plot__legend-swatch';
    swatch.style.background = color || '#fff';
    node.appendChild(swatch);
    node.appendChild(document.createTextNode(label));
    legend.appendChild(node);
  });
  chart.insertAdjacentElement('afterbegin', legend);
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
  initMethodPanel();
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
