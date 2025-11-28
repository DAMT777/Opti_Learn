const el = (s)=>document.querySelector(s);
const csrftoken = (document.cookie.match(/csrftoken=([^;]+)/)||[])[1]||'';
const sections = {
  resultMain: el('#resultMain'),
  resultDetails: el('#resultDetails'),
  resultInterpretation: el('#resultInterpretation'),
  errors: el('#methodErrors'),
  iterations: el('#iters'),
  lineSearch: el('#lineSearchDetails'),
  plots: {
    contour: el('#plotContour'),
    surface: el('#plotSurface'),
    fx: el('#plotFx'),
  },
};
let lastPlotData = null;

// ============================================================================
// UTILIDADES DE RENDERIZADO
// ============================================================================

function renderMarkdownToHTML(text){
  try{
    if(window.marked){
      const raw = window.marked.parse(String(text || ''), { breaks: true });
      if(window.DOMPurify){
        return window.DOMPurify.sanitize(raw, { USE_PROFILES: { html: true } });
      }
      return raw;
    }
  }catch{}
  return String(text || '').replace(/</g,'&lt;');
}

function buildMetricsHtml(method, meta){
  const formatVal = (v) => typeof v === 'number' ? v.toFixed(6) : (v ?? '-');
  
  switch(method){
    case 'lagrange':
      return `
        <div class="metric">
          <div class="metric__label">f*</div>
          <div class="metric__value">${formatVal(meta.f_star)}</div>
        </div>
        <div class="metric">
          <div class="metric__label">x*</div>
          <div class="metric__value small">${JSON.stringify(meta.x_star)}</div>
        </div>
        <div class="metric">
          <div class="metric__label">λ*</div>
          <div class="metric__value small">${JSON.stringify(meta.lambda_star)}</div>
        </div>
      `;
      
    case 'differential':
      return `
        <div class="metric">
          <div class="metric__label">Naturaleza</div>
          <div class="metric__value">${meta.nature || '-'}</div>
        </div>
        <div class="metric">
          <div class="metric__label">Punto óptimo</div>
          <div class="metric__value small">${JSON.stringify(meta.optimal_point)}</div>
        </div>
        <div class="metric">
          <div class="metric__label">Valor óptimo</div>
          <div class="metric__value">${formatVal(meta.optimal_value)}</div>
        </div>
      `;
      
    case 'kkt':
      return `
        <div class="metric">
          <div class="metric__label">f*</div>
          <div class="metric__value">${formatVal(meta.f_star)}</div>
        </div>
        <div class="metric">
          <div class="metric__label">x*</div>
          <div class="metric__value small">${JSON.stringify(meta.x_star)}</div>
        </div>
        <div class="metric">
          <div class="metric__label">λ* (igual.)</div>
          <div class="metric__value small">${JSON.stringify(meta.lambda_eq || [])}</div>
        </div>
        <div class="metric">
          <div class="metric__label">μ* (desig.)</div>
          <div class="metric__value small">${JSON.stringify(meta.mu_ineq || [])}</div>
        </div>
      `;
      
    case 'gradient':
      return `
        <div class="metric">
          <div class="metric__label">f*</div>
          <div class="metric__value">${formatVal(meta.f_star)}</div>
        </div>
        <div class="metric">
          <div class="metric__label">x*</div>
          <div class="metric__value small">${JSON.stringify(meta.x_star)}</div>
        </div>
        <div class="metric">
          <div class="metric__label">Iteraciones</div>
          <div class="metric__value">${meta.iterations ?? '-'}</div>
        </div>
        <div class="metric">
          <div class="metric__label">‖∇f‖</div>
          <div class="metric__value">${formatVal(meta.grad_norm)}</div>
        </div>
      `;
      
    case 'qp':
      return `
        <div class="metric">
          <div class="metric__label">f*</div>
          <div class="metric__value">${formatVal(meta.f_star)}</div>
        </div>
        <div class="metric">
          <div class="metric__label">x*</div>
          <div class="metric__value small">${JSON.stringify(meta.x_star)}</div>
        </div>
        <div class="metric">
          <div class="metric__label">Tipo</div>
          <div class="metric__value">${meta.problem_type || 'QP'}</div>
        </div>
      `;
      
    default:
      return `
        <div class="metric">
          <div class="metric__label">f*</div>
          <div class="metric__value">${formatVal(meta.f_star)}</div>
        </div>
        <div class="metric">
          <div class="metric__label">x*</div>
          <div class="metric__value small">${JSON.stringify(meta.x_star)}</div>
        </div>
      `;
  }
}

function formatNumber(value){
  if(typeof value !== 'number' || Number.isNaN(value)){
    return '-';
  }
  const abs = Math.abs(value);
  if(abs >= 1e4 || (abs > 0 && abs < 1e-3)){
    return value.toExponential(3);
  }
  return value.toFixed(6);
}

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

// Parsea restricciones desde el contenedor dinámico de restricciones
function parseConstraintsFromDynamicForm(){
  const container = el('#constraintsContainer');
  if(!container) return [];
  
  const rows = container.querySelectorAll('.constraint-row');
  const constraints = [];
  
  rows.forEach(row => {
    const kindSelect = row.querySelector('.constraint-kind');
    const exprInput = row.querySelector('.constraint-input');
    
    if(exprInput){
      const expr = exprInput.value.trim();
      if(expr){
        // Si hay selector de tipo, usar ese valor
        let kind = 'eq';  // por defecto para Lagrange
        if(kindSelect){
          kind = kindSelect.value;  // 'le', 'ge', 'eq'
        }
        
        constraints.push({
          expr: expr,
          kind: kind
        });
      }
    }
  });
  
  return constraints;
}

// Decide cuál parser de restricciones usar
function getConstraints(){
  const method = window.OPTI?.METHOD || '';
  
  // Si hay un contenedor dinámico, usarlo
  const container = el('#constraintsContainer');
  if(container && container.querySelectorAll('.constraint-row').length > 0){
    return parseConstraintsFromDynamicForm();
  }
  
  // Fallback al campo JSON
  return parseConstraintsField();
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
  if(sections.resultInterpretation){
    const hasContent = Boolean(interpretationHtml);
    sections.resultInterpretation.innerHTML = hasContent
      ? renderMarkdownToHTML(interpretationHtml)
      : '<div class="text-muted">Sin interpretacion.</div>';
    try{
      if(window.MathJax && window.MathJax.typesetPromise){
        window.MathJax.typesetPromise([sections.resultInterpretation]);
      }
    }catch{}
  }
}

function resetOutputs(){
  setResultSections('', '', '');
  if(sections.iterations) sections.iterations.innerHTML = '';
  if(sections.lineSearch) sections.lineSearch.innerHTML = 'Sin datos de busqueda de linea.';
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

  // Determinar endpoint según método - TODOS los métodos usan endpoints pedagógicos
  let endpoint = null;
  let payload = {
    objective_expr: objective,
    variables: variables
  };

  // Usar el nuevo parser que detecta automáticamente el formato
  const constraints = getConstraints();

  switch(method){
    case 'lagrange':
      if(!constraints || constraints.length === 0){
        showMethodError('El método de Lagrange requiere al menos una restricción de igualdad.');
        return;
      }
      endpoint = '/api/methods/lagrange/solve';
      payload.constraints = constraints;
      break;
      
    case 'differential':
      endpoint = '/api/methods/differential/solve';
      break;
      
    case 'kkt':
      if(!constraints || constraints.length === 0){
        showMethodError('El método KKT requiere al menos una restricción.');
        return;
      }
      endpoint = '/api/methods/kkt/solve';
      payload.constraints = constraints;
      // Verificar si es maximización
      const isMax = el('#isMaximization')?.checked || false;
      payload.maximize = isMax;
      break;
      
    case 'gradient':
      endpoint = '/api/methods/gradient/solve';
      // Agregar parámetros opcionales si existen
      const gradParams = collectOptionalParams();
      if(gradParams.x0) payload.x0 = gradParams.x0;
      if(gradParams.tol) payload.tol = gradParams.tol;
      if(gradParams.max_iter) payload.max_iter = gradParams.max_iter;
      break;
      
    case 'qp':
      endpoint = '/api/methods/qp/solve';
      if(constraints && constraints.length > 0){
        payload.constraints = constraints;
      }
      break;
      
    default:
      // Para cualquier otro método, usar el flujo original con persistencia
      return solveWithPersistence();
  }

  // Mostrar loading
  setResultSections(
    '<div class="spinner-border spinner-border-sm text-primary" role="status"></div>',
    'Resolviendo paso a paso...',
    ''
  );

  try{
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken
      },
      body: JSON.stringify(payload)
    });

    const result = await response.json();

    if(!response.ok || !result.success){
      showMethodError(result.error || 'Error al resolver el problema.');
      setResultSections('<div class="text-danger">No se obtuvo resultado.</div>', '', '');
      return;
    }

    // Renderizar explicación pedagógica (Markdown con LaTeX)
    const explanationHtml = renderMarkdownToHTML(result.explanation);
    
    // Construir métricas principales según el método
    const meta = result.metadata || {};
    let metricsHtml = buildMetricsHtml(method, meta);

    // Mostrar resultados
    setResultSections(metricsHtml, '', explanationHtml);
    
    // Renderizar gráficas si existen
    if(meta.plot_2d_path || meta.plot_3d_path){
      renderStaticPlots(meta.plot_2d_path, meta.plot_3d_path);
    }

    // Procesar LaTeX con MathJax
    if(window.MathJax && window.MathJax.typesetPromise){
      setTimeout(() => {
        const resultDetails = el('#resultDetails');
        if(resultDetails){
          window.MathJax.typesetPromise([resultDetails]).catch(err => console.error('MathJax error:', err));
        }
      }, 100);
    }

    showMethodError('');
  }catch(err){
    console.error('Error al resolver:', err);
    showMethodError('No se pudo ejecutar el solver. Intenta nuevamente.');
    setResultSections('<div class="text-danger">Error de conexión.</div>', '', '');
  }
}

// Función auxiliar para renderizar gráficas estáticas (PNG/JPG)
function renderStaticPlots(plot2dPath, plot3dPath){
  const plotContour = el('#plotContour');
  const plotSurface = el('#plotSurface');
  
  if(plotContour && plot2dPath){
    plotContour.innerHTML = `<img src="${plot2dPath}" alt="Gráfica 2D" style="max-width: 100%; height: auto; border-radius: 8px;">`;
  }
  
  if(plotSurface && plot3dPath){
    plotSurface.innerHTML = `<img src="${plot3dPath}" alt="Gráfica 3D" style="max-width: 100%; height: auto; border-radius: 8px;">`;
  }
}

// Función original para métodos que requieren persistencia (gradient, kkt, qp)
async function solveWithPersistence(){
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
    const interpretation = renderInterpretation(sol.explanation_final, sol.iterations_count);
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
    const fmt = (val)=> typeof val === 'number' ? formatNumber(val) : (val ?? '');
    const alphaVal = (typeof it.step === 'number' && !Number.isNaN(it.step)) ? formatNumber(it.step) : (typeof it.alpha === 'number' ? formatNumber(it.alpha) : (it.alpha ?? ''));
    tr.innerHTML = `<td>${it.k ?? ''}</td><td>${fmt(it.f_k)}</td><td>${fmt(it.grad_norm)}</td><td>${alphaVal}</td>`;
    sections.iterations.appendChild(tr);
  });
  renderLineSearchDetails(rows);
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

function renderInterpretation(value, iters){
  if(!value){
    return `Despues de ${iters ?? '-'} iteraciones se alcanzo el punto optimo reportado.`;
  }
  if(typeof value === 'object'){
    if(Array.isArray(value)){
      return value.map(v=>`- ${v}`).join('\n');
    }
    return Object.entries(value).map(([k,v])=>`- ${k}: ${v}`).join('\n');
  }
  return String(value);
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
  if(plotData && plotData.allow_plots === false){
    const msg = plotData.message || 'Las visualizaciones solo están disponibles para funciones con 1 o 2 variables.';
    Object.values(nodes).forEach(node=>{
      if(node) node.innerHTML = `<span>${msg}</span>`;
    });
    return;
  }
  if(!plotData || !window.Plotly){
    return;
  }
  const theme = getPlotTheme();
  if(plotData.func_1d && nodes.surface){
    renderCurve1D(nodes.surface, plotData, theme);
    if(nodes.contour){
      nodes.contour.innerHTML = '<span>No aplica para 1 variable.</span>';
    }
  }
  if(nodes.contour && plotData.mesh){
    renderContourPlot(nodes.contour, plotData, theme);
  }
  if(nodes.surface && plotData.mesh){
    renderSurfacePlot(nodes.surface, plotData, theme);
  }
  if(nodes.fx){
    renderFxPlot(nodes.fx, plotData, theme);
  }
}

function renderLineSearchDetails(rows){
  if(!sections.lineSearch) return;
  const traces = (rows || []).filter(it => Array.isArray(it.line_search) && it.line_search.length);
  if(!traces.length){
    sections.lineSearch.innerHTML = '<div class="text-muted">Sin datos de busqueda de linea.</div>';
    return;
  }
  const html = traces.slice(0, 4).map(it=>{
    const steps = it.line_search.map(step=>{
      const badge = step.accepted
        ? '<span class="badge bg-success ms-2">Aceptado</span>'
        : '<span class="badge bg-warning text-dark ms-2">Reducir</span>';
      const reason = step.reason === 'min_alpha'
        ? '<small class="text-muted ms-1">alpha minimo</small>'
        : '';
      const reasonTag = reason ? ` ${reason}` : '';
      return `<li><code>&alpha;=${formatNumber(step.alpha)}</code> &rarr; f=${formatNumber(step.f_value)} <small class="text-muted">(umbral ${formatNumber(step.threshold)})</small>${badge}${reasonTag}</li>`;
    }).join('');
    return `
      <div class="line-search-block">
        <div class="fw-semibold mb-1">Iteracion ${it.k}</div>
        <ol class="line-search-block__list">
          ${steps}
        </ol>
      </div>
    `;
  }).join('');
  sections.lineSearch.innerHTML = html;
  try{
    if(window.MathJax && window.MathJax.typesetPromise){
      window.MathJax.typesetPromise([sections.lineSearch]);
    }
  }catch{}
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

function renderCurve1D(node, plotData, theme){
  const curve = plotData.func_1d;
  if(!curve || !Array.isArray(curve.x) || !Array.isArray(curve.f)){
    node.innerHTML = '<span>No hay datos para la función.</span>';
    return;
  }
  node.innerHTML = '';
  node.style.height = '320px';
  node.style.minHeight = '320px';
  node.style.width = '100%';
  node.style.display = 'block';
  node.style.padding = '0';
  node.style.overflow = 'visible';
  const traj = plotData.trajectory || { x: [], f: [] };
  const funcTrace = {
    x: curve.x,
    y: curve.f,
    mode: 'lines',
    line: { color: '#3a77d8', width: 2 },
    name: 'f(x)',
  };
  const pathTrace = {
    x: traj.x,
    y: traj.f,
    mode: 'markers+lines',
    line: { color: '#ffba08', dash: 'dashdot', width: 2 },
    marker: { color: '#ffba08', size: 8 },
    name: 'Iteraciones',
  };
  const layout = {
    title: 'Función y trayectoria (1 variable)',
    paper_bgcolor: theme.paper,
    plot_bgcolor: theme.plot,
    xaxis: { title: 'x', color: theme.axis, gridcolor: theme.grid, zerolinecolor: theme.zero },
    yaxis: { title: 'f(x)', color: theme.axis, gridcolor: theme.grid, zerolinecolor: theme.zero },
    margin: { t: 60, b: 50, l: 60, r: 20 },
    height: 320,
  };
  Plotly.newPlot(node, [funcTrace, pathTrace], layout, {responsive:true, displayModeBar:false});
  setTimeout(()=> { try{ Plotly.Plots.resize(node); }catch{} }, 60);
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

// ============================================================================
// INICIALIZACIÓN Y EVENTOS
// ============================================================================

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
  
  // =========================================================================
  // Sistema de restricciones dinámicas
  // =========================================================================
  
  const constraintsContainer = el('#constraintsContainer');
  const addConstraintBtn = el('#addConstraintBtn');
  
  // Función para crear una nueva fila de restricción
  function createConstraintRow(kind = 'eq', expr = ''){
    const method = window.OPTI?.METHOD || '';
    const showKind = ['kkt', 'qp'].includes(method);
    
    const row = document.createElement('div');
    row.className = 'input-group mb-2 constraint-row';
    
    if(showKind){
      // KKT/QP: mostrar selector de tipo
      row.innerHTML = `
        <select class="form-select constraint-kind" style="max-width: 100px;">
          <option value="le" ${kind === 'le' ? 'selected' : ''}>≤ 0</option>
          <option value="ge" ${kind === 'ge' ? 'selected' : ''}>≥ 0</option>
          <option value="eq" ${kind === 'eq' ? 'selected' : ''}>= 0</option>
        </select>
        <input type="text" class="form-control constraint-input" placeholder="x + y - 1" value="${expr}">
        <button type="button" class="btn btn-outline-danger btn-remove-constraint" title="Eliminar"><i class="bi bi-x"></i></button>
      `;
    } else {
      // Lagrange: solo igualdad
      row.innerHTML = `
        <input type="text" class="form-control constraint-input" placeholder="x + y - 1" value="${expr}">
        <span class="input-group-text">= 0</span>
        <button type="button" class="btn btn-outline-danger btn-remove-constraint" title="Eliminar"><i class="bi bi-x"></i></button>
      `;
    }
    
    return row;
  }
  
  // Agregar restricción
  if(addConstraintBtn && constraintsContainer){
    addConstraintBtn.addEventListener('click', ()=>{
      const newRow = createConstraintRow();
      constraintsContainer.appendChild(newRow);
      const newInput = newRow.querySelector('.constraint-input');
      if(newInput) newInput.focus();
    });
  }
  
  // Eliminar restricción (delegación de eventos)
  if(constraintsContainer){
    constraintsContainer.addEventListener('click', (e)=>{
      const removeBtn = e.target.closest('.btn-remove-constraint');
      if(removeBtn){
        const row = removeBtn.closest('.constraint-row');
        if(row){
          // Mantener al menos una fila
          const allRows = constraintsContainer.querySelectorAll('.constraint-row');
          if(allRows.length > 1){
            row.remove();
          } else {
            // Si es la última, solo limpiar el campo
            const input = row.querySelector('.constraint-input');
            if(input) input.value = '';
          }
        }
      }
    });
  }
  
  // =========================================================================
  // Manejador de ejemplos - soporta también restricciones
  // =========================================================================
  
  document.querySelectorAll('[data-example]').forEach(btn=>{
    btn.addEventListener('click', ()=>{
      const expr = btn.getAttribute('data-example');
      const vars = btn.getAttribute('data-vars');
      const constr = btn.getAttribute('data-constraints');
      const x0Val = btn.getAttribute('data-x0');
      
      const objective = el('#objective');
      const variables = el('#variables');
      const constraints = el('#constraints');
      const x0 = el('#x0');
      
      if(objective && expr){
        objective.value = expr;
      }
      if(variables && vars){
        variables.value = vars;
      }
      
      // Manejar restricciones JSON o dinámicas
      if(constr){
        try{
          const parsedConstraints = JSON.parse(constr);
          
          // Si hay contenedor dinámico, llenar las filas
          if(constraintsContainer){
            // Limpiar contenedor
            constraintsContainer.innerHTML = '';
            
            // Crear filas para cada restricción
            parsedConstraints.forEach(c => {
              const cExpr = typeof c === 'string' ? c : (c.expr || '');
              const cKind = typeof c === 'object' ? (c.kind || 'eq') : 'eq';
              const row = createConstraintRow(cKind, cExpr);
              constraintsContainer.appendChild(row);
            });
            
            // Si no hay restricciones, agregar una fila vacía
            if(parsedConstraints.length === 0){
              constraintsContainer.appendChild(createConstraintRow());
            }
          }
          
          // También llenar el campo JSON si existe
          if(constraints){
            constraints.value = JSON.stringify(parsedConstraints, null, 2);
          }
        } catch(e){
          console.error('Error parseando restricciones del ejemplo:', e);
        }
      }
      
      if(x0 && x0Val){
        x0.value = x0Val;
      }
      
      // Mostrar notificación de ejemplo cargado
      showMethodError('');
      if(objective) objective.focus();
    });
  });
  
  // Auto-formatear JSON de restricciones al salir del campo
  const constraintsField = el('#constraints');
  if(constraintsField){
    constraintsField.addEventListener('blur', ()=>{
      const val = constraintsField.value.trim();
      if(!val) return;
      try{
        const parsed = JSON.parse(val);
        constraintsField.value = JSON.stringify(parsed, null, 2);
      }catch{
        // No hacer nada si no es JSON válido - se mostrará error al resolver
      }
    });
  }
});
