const el = (s)=>document.querySelector(s);
const csrftoken = (document.cookie.match(/csrftoken=([^;]+)/)||[])[1]||'';
const sections = {
  resultMain: el('#resultMain'),
  resultDetails: el('#resultDetails'),
  resultInterpretation: el('#resultInterpretation'),
  errors: el('#methodErrors'),
  iterations: el('#iters'),
  lineSearch: el('#lineSearchDetails'),
  solverStatus: el('#solverStatus'),
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

// Construir tarjetas de métricas para la sección de resultados principales
function buildResultCardsHtml(method, meta){
  const formatVal = (v) => {
    if(v === null || v === undefined) return '—';
    if(typeof v === 'number') {
      const abs = Math.abs(v);
      if(abs >= 1e4 || (abs > 0 && abs < 1e-3)) return v.toExponential(4);
      return v.toFixed(6);
    }
    if(Array.isArray(v)) {
      if(v.length === 0) return '—';
      return `[${v.map(x => typeof x === 'number' ? x.toFixed(4) : x).join(', ')}]`;
    }
    // Manejar objetos planos (diccionarios de Python)
    if(typeof v === 'object' && v !== null) {
      const vals = Object.values(v);
      if(vals.length === 0) return '—';
      return `[${vals.map(x => typeof x === 'number' ? x.toFixed(4) : x).join(', ')}]`;
    }
    return String(v);
  };

  switch(method){
    case 'lagrange':
      return `
        <div class="results-grid">
          <div class="result-card result-card--point">
            <div class="result-card__icon"><i class="bi bi-geo-alt-fill"></i></div>
            <div class="result-card__label">Punto óptimo $x^*$</div>
            <div class="result-card__value">${formatVal(meta.x_star)}</div>
          </div>
          <div class="result-card result-card--optimal">
            <div class="result-card__icon"><i class="bi bi-trophy-fill"></i></div>
            <div class="result-card__label">Valor óptimo $f^*$</div>
            <div class="result-card__value">${formatVal(meta.f_star)}</div>
          </div>
          <div class="result-card result-card--lambda">
            <div class="result-card__icon"><i class="bi bi-lightning-fill"></i></div>
            <div class="result-card__label">Multiplicadores $\\lambda^*$</div>
            <div class="result-card__value">${formatVal(meta.lambda_star)}</div>
          </div>
        </div>
      `;
      
    case 'differential':
      return `
        <div class="results-grid">
          <div class="result-card result-card--point">
            <div class="result-card__icon"><i class="bi bi-geo-alt-fill"></i></div>
            <div class="result-card__label">Punto crítico $x^*$</div>
            <div class="result-card__value">${formatVal(meta.optimal_point)}</div>
          </div>
          <div class="result-card result-card--optimal">
            <div class="result-card__icon"><i class="bi bi-bullseye"></i></div>
            <div class="result-card__label">Valor $f(x^*)$</div>
            <div class="result-card__value">${formatVal(meta.optimal_value)}</div>
          </div>
          <div class="result-card result-card--type">
            <div class="result-card__icon"><i class="bi bi-tag-fill"></i></div>
            <div class="result-card__label">Clasificación</div>
            <div class="result-card__value">${meta.nature || '—'}</div>
          </div>
        </div>
      `;
      
    case 'kkt':
      return `
        <div class="results-grid">
          <div class="result-card result-card--point">
            <div class="result-card__icon"><i class="bi bi-geo-alt-fill"></i></div>
            <div class="result-card__label">Punto óptimo $x^*$</div>
            <div class="result-card__value">${formatVal(meta.x_star)}</div>
          </div>
          <div class="result-card result-card--optimal">
            <div class="result-card__icon"><i class="bi bi-trophy-fill"></i></div>
            <div class="result-card__label">Valor óptimo $f^*$</div>
            <div class="result-card__value">${formatVal(meta.f_star)}</div>
          </div>
          <div class="result-card result-card--lambda">
            <div class="result-card__icon"><i class="bi bi-lock-fill"></i></div>
            <div class="result-card__label">$\\lambda$ (igualdad)</div>
            <div class="result-card__value">${formatVal(meta.lambda_eq || [])}</div>
          </div>
          <div class="result-card result-card--type">
            <div class="result-card__icon"><i class="bi bi-shield-check"></i></div>
            <div class="result-card__label">$\\mu$ (desigualdad)</div>
            <div class="result-card__value">${formatVal(meta.mu_ineq || [])}</div>
          </div>
        </div>
      `;
      
    case 'gradient':
      // Extraer el conteo de iteraciones y la norma final del gradiente
      const iterCount = meta.iterations_count ?? (Array.isArray(meta.iterations) ? meta.iterations.length : 0);
      let gradNormFinal = meta.grad_norm;
      // Si no viene grad_norm, intentar obtenerlo de la última iteración
      if((gradNormFinal === undefined || gradNormFinal === null) && Array.isArray(meta.iterations) && meta.iterations.length > 0){
        const lastIter = meta.iterations[meta.iterations.length - 1];
        gradNormFinal = lastIter.grad_norm ?? lastIter.norma_grad;
      }
      
      return `
        <div class="results-grid">
          <div class="result-card result-card--point">
            <div class="result-card__icon"><i class="bi bi-geo-alt-fill"></i></div>
            <div class="result-card__label">Punto óptimo $x^*$</div>
            <div class="result-card__value">${formatVal(meta.x_star)}</div>
          </div>
          <div class="result-card result-card--optimal">
            <div class="result-card__icon"><i class="bi bi-trophy-fill"></i></div>
            <div class="result-card__label">Valor óptimo $f^*$</div>
            <div class="result-card__value">${formatVal(meta.f_star)}</div>
          </div>
          <div class="result-card result-card--type">
            <div class="result-card__icon"><i class="bi bi-arrow-repeat"></i></div>
            <div class="result-card__label">Iteraciones</div>
            <div class="result-card__value">${iterCount}</div>
          </div>
          <div class="result-card result-card--lambda">
            <div class="result-card__icon"><i class="bi bi-speedometer2"></i></div>
            <div class="result-card__label">$\\|\\nabla f\\|$ final</div>
            <div class="result-card__value">${formatVal(gradNormFinal)}</div>
          </div>
        </div>
      `;
      
    case 'qp':
      return `
        <div class="results-grid">
          <div class="result-card result-card--point">
            <div class="result-card__icon"><i class="bi bi-geo-alt-fill"></i></div>
            <div class="result-card__label">Punto óptimo $x^*$</div>
            <div class="result-card__value">${formatVal(meta.x_star)}</div>
          </div>
          <div class="result-card result-card--optimal">
            <div class="result-card__icon"><i class="bi bi-trophy-fill"></i></div>
            <div class="result-card__label">Valor óptimo $f^*$</div>
            <div class="result-card__value">${formatVal(meta.f_star)}</div>
          </div>
          <div class="result-card result-card--type">
            <div class="result-card__icon"><i class="bi bi-check2-circle"></i></div>
            <div class="result-card__label">Tipo de problema</div>
            <div class="result-card__value">${meta.problem_type || 'QP'}</div>
          </div>
        </div>
      `;
      
    default:
      return `
        <div class="results-grid">
          <div class="result-card result-card--point">
            <div class="result-card__icon"><i class="bi bi-geo-alt-fill"></i></div>
            <div class="result-card__label">Punto óptimo $x^*$</div>
            <div class="result-card__value">${formatVal(meta.x_star)}</div>
          </div>
          <div class="result-card result-card--optimal">
            <div class="result-card__icon"><i class="bi bi-trophy-fill"></i></div>
            <div class="result-card__label">Valor óptimo $f^*$</div>
            <div class="result-card__value">${formatVal(meta.f_star)}</div>
          </div>
        </div>
      `;
  }
}

// Mantener compatibilidad con la versión anterior
function buildMetricsHtml(method, meta){
  return buildResultCardsHtml(method, meta);
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

// ============================================================================
// RENDERIZADO DE SECCIONES DE RESULTADOS V3
// ============================================================================

function setResultSections(mainHtml, detailsHtml, interpretationHtml){
  // Sección de resultados principales (métricas/cards)
  if(sections.resultMain){
    sections.resultMain.innerHTML = mainHtml || '<div class="text-muted p-3">Ejecuta el método para ver resultados.</div>';
  }
  
  // Sección de procedimiento/detalles (en la nueva estructura va en #resultProcedure o #resultDetails)
  const procedureSection = el('#resultProcedure') || sections.resultDetails;
  if(procedureSection && detailsHtml){
    procedureSection.innerHTML = detailsHtml;
  }
  
  // Sección de interpretación pedagógica
  if(sections.resultInterpretation){
    const hasContent = Boolean(interpretationHtml);
    sections.resultInterpretation.innerHTML = hasContent
      ? renderMarkdownToHTML(interpretationHtml)
      : '<div class="text-muted">Esperando explicación pedagógica...</div>';
    
    // Activar la sección si hay contenido
    const solutionSection = el('.method-solution-section');
    if(solutionSection && hasContent){
      solutionSection.classList.add('has-results');
    }
  }
  
  // Actualizar estado del solver
  if(sections.solverStatus){
    const hasResults = mainHtml && mainHtml.includes('result-card');
    sections.solverStatus.innerHTML = hasResults 
      ? '<span class="status-badge status-badge--success"><i class="bi bi-check-circle"></i> Resuelto</span>'
      : '<span class="status-badge status-badge--pending"><i class="bi bi-clock"></i> Pendiente</span>';
  }
  
  // Re-renderizar MathJax en todas las secciones actualizadas
  try{
    if(window.MathJax && window.MathJax.typesetPromise){
      const elementsToTypeset = [
        sections.resultMain,
        sections.resultInterpretation,
        procedureSection
      ].filter(Boolean);
      
      if(elementsToTypeset.length){
        window.MathJax.typesetPromise(elementsToTypeset);
      }
    }
  }catch(e){
    console.error('Error al procesar MathJax:', e);
  }
}

// Renderizar explicación pedagógica con formato mejorado
function renderPedagogicalExplanation(explanation, method){
  if(!explanation) return '';
  
  // Procesar Markdown a HTML con soporte para bloques especiales
  let html = renderMarkdownToHTML(explanation);
  
  // Añadir iconos y estilos a secciones clave
  html = html
    .replace(/<h4>(.*?Paso\s*\d+.*?)<\/h4>/gi, '<h4 class="step-heading"><i class="bi bi-arrow-right-circle"></i> $1</h4>')
    .replace(/<strong>(Resultado|Solución|Óptimo|Conclusión):/gi, '<strong class="result-label"><i class="bi bi-check2-circle"></i> $1:')
    .replace(/<strong>(Nota|Importante|Advertencia):/gi, '<strong class="note-label"><i class="bi bi-info-circle"></i> $1:');
  
  return html;
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
    '<div class="loading-state"><div class="spinner-border spinner-border-sm text-primary" role="status"></div><span class="ms-2">Resolviendo...</span></div>',
    '',
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

    // Construir métricas principales según el método
    const meta = result.metadata || {};
    let metricsHtml = buildResultCardsHtml(method, meta);

    // Renderizar explicación pedagógica completa
    const explanationHtml = renderPedagogicalExplanation(result.explanation, method);
    
    // Construir detalles del procedimiento si existen
    let procedureHtml = '';
    if(meta.steps || meta.procedure){
      procedureHtml = renderProcedureSteps(meta.steps || meta.procedure);
    } else if(result.explanation && ['kkt', 'qp', 'lagrange', 'differential'].includes(method)){
      // Para métodos analíticos, la explicación ES el procedimiento
      procedureHtml = explanationHtml;
    }

    // Mostrar resultados en las secciones correspondientes
    setResultSections(metricsHtml, procedureHtml, explanationHtml);
    
    // Renderizar gráficas si existen (estáticas PNG/JPG)
    if(meta.plot_2d_path || meta.plot_3d_path){
      renderStaticPlots(meta.plot_2d_path, meta.plot_3d_path);
    }
    
    // Renderizar gráficas interactivas si existen plot_data (para gradient)
    if(meta.plot_data){
      renderMethodPlots(meta.plot_data);
    }
    
    // Renderizar según el método
    if(method === 'lagrange'){
      // Renderizar puntos críticos de Lagrange
      renderLagrangeCriticalPoints(
        meta.critical_points,
        meta.x_star,
        meta.f_star,
        meta.lambda_star,
        meta.nature
      );
    } else if(method === 'kkt'){
      // Renderizar casos evaluados de KKT
      renderKKTCandidates(meta.candidates, meta.x_star, meta.f_star, meta.is_maximization);
    } else if(method === 'qp'){
      // Renderizar sección específica de QP
      renderQPDecomposition(meta);
    } else if(method === 'differential'){
      // Renderizar sección específica de Differential
      renderDifferentialAnalysis(meta);
    } else {
      // Renderizar iteraciones si existen (para gradient) - buscar en metadata
      const iterations = meta.iterations || result.iterations || [];
      if(Array.isArray(iterations) && iterations.length > 0){
        renderMethodIterations(iterations);
      }
    }

    // Procesar LaTeX con MathJax en todas las secciones
    if(window.MathJax && window.MathJax.typesetPromise){
      setTimeout(() => {
        const elementsToTypeset = document.querySelectorAll('.method-solution-section, .method-iterations-section, .result-card');
        if(elementsToTypeset.length){
          window.MathJax.typesetPromise([...elementsToTypeset]).catch(err => console.error('MathJax error:', err));
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

// Función para renderizar pasos del procedimiento
function renderProcedureSteps(steps){
  if(!steps || !Array.isArray(steps) || steps.length === 0) return '';
  
  let html = '<div class="procedure-steps">';
  steps.forEach((step, idx) => {
    let title = '';
    let description = '';
    
    if(typeof step === 'string'){
      // Step es un string simple
      description = step;
    } else if(step.titulo && step.contenido !== undefined){
      // Formato del solver QP: {numero, titulo, contenido}
      title = step.titulo;
      description = formatQPStepContent(step.numero, step.contenido);
    } else {
      // Formato estándar: {title, description}
      title = step.title || '';
      description = step.description || '';
    }
    
    const stepNum = step.numero || (idx + 1);
    
    html += `
      <div class="procedure-step">
        <div class="procedure-step__number">${stepNum}</div>
        <div class="procedure-step__content">
          ${title ? `<div class="procedure-step__title">${title}</div>` : ''}
          <div class="procedure-step__description">${renderMarkdownToHTML(description)}</div>
        </div>
      </div>
    `;
  });
  html += '</div>';
  return html;
}

// Función auxiliar para formatear contenido de pasos QP
function formatQPStepContent(stepNum, contenido){
  if(!contenido || typeof contenido !== 'object') return String(contenido || '');
  
  let html = '';
  
  switch(stepNum){
    case 1: // DEFINICION DEL PROBLEMA
      if(contenido.objetivo) html += `<p><strong>Función objetivo:</strong> $${contenido.objetivo}$</p>`;
      if(contenido.variables) html += `<p><strong>Variables:</strong> ${contenido.variables}</p>`;
      if(contenido.n_ineq !== undefined || contenido.n_eq !== undefined){
        html += `<p><strong>Restricciones:</strong> ${contenido.n_eq || 0} igualdad, ${contenido.n_ineq || 0} desigualdad</p>`;
      }
      if(contenido.restricciones_detalles && contenido.restricciones_detalles.length > 0){
        html += '<ul class="constraint-list">';
        contenido.restricciones_detalles.forEach(r => {
          const kindSymbol = r.kind === 'eq' ? '=' : (r.kind === 'ge' ? '≥' : '≤');
          html += `<li>$${r.expr} ${kindSymbol} ${r.rhs}$</li>`;
        });
        html += '</ul>';
      }
      break;
      
    case 2: // MATRICES
      if(contenido.D){
        html += '<p><strong>Matriz Hessiana $Q$:</strong></p>';
        html += formatMatrixLatex(contenido.D, 'Q');
      }
      if(contenido.C){
        html += '<p><strong>Vector de coeficientes lineales $c$:</strong></p>';
        html += formatVectorLatex(contenido.C, 'c');
      }
      if(contenido.A_ineq && contenido.A_ineq.length > 0){
        html += '<p><strong>Matriz de restricciones $A$:</strong></p>';
        html += formatMatrixLatex(contenido.A_ineq, 'A');
      }
      if(contenido.b_ineq && contenido.b_ineq.length > 0){
        html += '<p><strong>Vector $b$:</strong> $[' + contenido.b_ineq.map(v => formatNum(v)).join(', ') + ']$</p>';
      }
      break;
      
    case 3: // CONVEXIDAD
      if(contenido.eigenvalues){
        html += '<p><strong>Eigenvalores de $Q$:</strong> $\\lambda = [' + contenido.eigenvalues.map(v => formatNum(v)).join(', ') + ']$</p>';
      }
      if(contenido.definiteness){
        html += `<p><strong>Definitud:</strong> ${contenido.definiteness}</p>`;
      }
      if(contenido.convexa !== undefined){
        const badge = contenido.convexa 
          ? '<span class="badge bg-success">✓ Problema convexo</span>'
          : '<span class="badge bg-warning text-dark">⚠ No convexo</span>';
        html += `<p>${badge}</p>`;
      }
      break;
      
    case 4: // SISTEMA KKT
      html += '<p><strong>Dimensiones del sistema KKT:</strong></p>';
      html += '<ul>';
      if(contenido.n_vars !== undefined) html += `<li>Variables primales: ${contenido.n_vars}</li>`;
      if(contenido.n_lambda_eq !== undefined) html += `<li>Multiplicadores de igualdad ($\\lambda$): ${contenido.n_lambda_eq}</li>`;
      if(contenido.n_lambda_ineq !== undefined) html += `<li>Multiplicadores de desigualdad ($\\mu$): ${contenido.n_lambda_ineq}</li>`;
      if(contenido.n_mu !== undefined) html += `<li>Variables de holgura: ${contenido.n_mu}</li>`;
      html += '</ul>';
      break;
      
    case 5: // PROCESO DE OPTIMIZACION
      if(contenido.metodo) html += `<p><strong>Método:</strong> ${contenido.metodo}</p>`;
      if(contenido.convergio !== undefined){
        const badge = contenido.convergio 
          ? '<span class="badge bg-success">✓ Convergió</span>'
          : '<span class="badge bg-danger">✗ No convergió</span>';
        html += `<p><strong>Estado:</strong> ${badge}</p>`;
      }
      if(contenido.total_iteraciones !== undefined) html += `<p><strong>Iteraciones:</strong> ${contenido.total_iteraciones}</p>`;
      if(contenido.x_optimo){
        html += '<p><strong>Punto óptimo:</strong> $x^* = [' + contenido.x_optimo.map(v => formatNum(v)).join(', ') + ']$</p>';
      }
      if(contenido.f_optimo !== undefined) html += `<p><strong>Valor óptimo:</strong> $f(x^*) = ${formatNum(contenido.f_optimo)}$</p>`;
      if(contenido.mensaje) html += `<p class="text-muted"><em>${contenido.mensaje}</em></p>`;
      break;
      
    case 6: // VERIFICACION KKT
      html += '<p><strong>Verificación de condiciones KKT:</strong></p>';
      html += '<ul>';
      if(contenido.gradiente_f){
        html += `<li><strong>$\\nabla_x L = 0$:</strong> Gradiente ≈ $[${contenido.gradiente_f.map(v => formatNum(v, 2)).join(', ')}]$ ✓</li>`;
      }
      if(contenido.residual_igualdad !== undefined) html += `<li><strong>Restricciones igualdad:</strong> Residual = ${formatNum(contenido.residual_igualdad)} ✓</li>`;
      if(contenido.violacion_desigualdad !== undefined) html += `<li><strong>Restricciones desigualdad:</strong> Violación máx = ${formatNum(contenido.violacion_desigualdad)} ✓</li>`;
      if(contenido.x_no_negativo !== undefined){
        const check = contenido.x_no_negativo ? '✓' : '✗';
        html += `<li><strong>No negatividad:</strong> $x \\geq 0$ ${check}</li>`;
      }
      html += '</ul>';
      break;
      
    case 7: // SOLUCION OPTIMA
      if(contenido.solucion){
        html += '<p><strong>Solución óptima:</strong></p>';
        html += '<div class="solution-box">';
        const vars = Object.entries(contenido.solucion);
        vars.forEach(([varName, val]) => {
          html += `<p>$${varName}^* = ${formatNum(val)}$</p>`;
        });
        html += '</div>';
      }
      if(contenido.valor_objetivo !== undefined){
        html += `<p><strong>Valor óptimo:</strong> $f(x^*) = ${formatNum(contenido.valor_objetivo)}$</p>`;
      }
      if(contenido.multiplicadores){
        html += '<p><strong>Multiplicadores de Lagrange:</strong></p>';
        if(contenido.multiplicadores.lambda_ineq){
          html += '<p>$\\mu$ (desigualdad): $[' + contenido.multiplicadores.lambda_ineq.map(v => formatNum(v)).join(', ') + ']$</p>';
        }
        if(contenido.multiplicadores.mu){
          html += '<p>$\\lambda$ (igualdad): $[' + contenido.multiplicadores.mu.map(v => formatNum(v)).join(', ') + ']$</p>';
        }
      }
      break;
      
    default:
      // Formateo genérico para otros pasos
      html = formatGenericContent(contenido);
  }
  
  return html || formatGenericContent(contenido);
}

// Formatear matriz en LaTeX
function formatMatrixLatex(matrix, name){
  if(!matrix || !Array.isArray(matrix)) return '';
  let latex = `$$${name} = \\begin{bmatrix}`;
  matrix.forEach((row, i) => {
    if(Array.isArray(row)){
      latex += row.map(v => formatNum(v)).join(' & ');
    } else {
      latex += formatNum(row);
    }
    if(i < matrix.length - 1) latex += ' \\\\ ';
  });
  latex += '\\end{bmatrix}$$';
  return latex;
}

// Formatear vector en LaTeX
function formatVectorLatex(vector, name){
  if(!vector || !Array.isArray(vector)) return '';
  return `$$${name} = \\begin{bmatrix} ${vector.map(v => formatNum(v)).join(' \\\\ ')} \\end{bmatrix}$$`;
}

// Formatear número
function formatNum(val, decimals = 4){
  if(val === null || val === undefined) return '—';
  if(typeof val !== 'number') return String(val);
  if(Math.abs(val) < 1e-10) return '0';
  if(Math.abs(val) >= 1e4 || (Math.abs(val) > 0 && Math.abs(val) < 1e-3)){
    return val.toExponential(2);
  }
  return val.toFixed(decimals).replace(/\.?0+$/, '');
}

// Formatear contenido genérico
function formatGenericContent(contenido){
  if(!contenido || typeof contenido !== 'object') return String(contenido || '');
  
  let html = '<ul>';
  for(const [key, value] of Object.entries(contenido)){
    if(value === null || value === undefined) continue;
    const displayKey = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
    if(Array.isArray(value)){
      html += `<li><strong>${displayKey}:</strong> [${value.map(v => typeof v === 'number' ? formatNum(v) : v).join(', ')}]</li>`;
    } else if(typeof value === 'object'){
      html += `<li><strong>${displayKey}:</strong> ${JSON.stringify(value)}</li>`;
    } else {
      html += `<li><strong>${displayKey}:</strong> ${value}</li>`;
    }
  }
  html += '</ul>';
  return html;
}

// Función para renderizar la sección de análisis de Cálculo Diferencial
function renderDifferentialAnalysis(meta){
  // Renderizar Gradiente
  const gradientEl = document.getElementById('gradientContent');
  if(gradientEl){
    let html = '';
    if(meta.gradient){
      if(Array.isArray(meta.gradient)){
        // Gradiente como array de strings LaTeX
        html = '<div class="gradient-display">';
        html += '$$\\nabla f = \\begin{bmatrix}';
        html += meta.gradient.map(g => typeof g === 'string' ? g : formatNum(g)).join(' \\\\ ');
        html += '\\end{bmatrix}$$';
        html += '</div>';
      } else if(typeof meta.gradient === 'string'){
        // Gradiente ya formateado en LaTeX
        html = `<div class="gradient-display">$$\\nabla f = ${meta.gradient}$$</div>`;
      }
    } else {
      html = '<span class="text-muted">Gradiente no disponible</span>';
    }
    gradientEl.innerHTML = html;
  }
  
  // Renderizar Hessiano
  const hessianEl = document.getElementById('hessianContent');
  if(hessianEl){
    let html = '';
    if(meta.hessian){
      if(Array.isArray(meta.hessian)){
        // Hessiano como matriz
        html = '<div class="hessian-display">';
        html += '$$H_f = \\begin{bmatrix}';
        meta.hessian.forEach((row, i) => {
          if(Array.isArray(row)){
            html += row.map(v => typeof v === 'string' ? v : formatNum(v)).join(' & ');
          } else {
            html += typeof row === 'string' ? row : formatNum(row);
          }
          if(i < meta.hessian.length - 1) html += ' \\\\ ';
        });
        html += '\\end{bmatrix}$$';
        html += '</div>';
      } else if(typeof meta.hessian === 'string'){
        // Hessiano ya formateado en LaTeX
        html = `<div class="hessian-display">$$H_f = ${meta.hessian}$$</div>`;
      }
      
      // Agregar determinante si está disponible
      if(meta.hessian_det !== undefined && meta.hessian_det !== null){
        html += `<p class="mt-2"><strong>Determinante:</strong> $\\det(H_f) = ${formatNum(meta.hessian_det)}$</p>`;
      }
      
      // Agregar eigenvalores si están disponibles
      if(meta.eigenvalues && Array.isArray(meta.eigenvalues) && meta.eigenvalues.length > 0){
        html += `<p><strong>Eigenvalores:</strong> $\\lambda = [${meta.eigenvalues.map(v => formatNum(v)).join(', ')}]$</p>`;
      }
    } else {
      html = '<span class="text-muted">Hessiano no disponible</span>';
    }
    hessianEl.innerHTML = html;
  }
  
  // Renderizar tabla de puntos críticos
  const itersEl = document.getElementById('iters');
  if(itersEl){
    let html = '';
    
    // Usar classifications si está disponible, sino usar critical_points
    const points = meta.classifications || meta.critical_points || [];
    
    if(Array.isArray(points) && points.length > 0){
      points.forEach((cp, idx) => {
        // Determinar el punto y naturaleza según la estructura de datos
        const point = cp.point || cp.critical_point || cp;
        const nature = cp.nature || cp.classification || cp.type || '—';
        const value = cp.value !== undefined ? cp.value : (cp.f_value !== undefined ? cp.f_value : '—');
        const det = cp.determinant !== undefined ? cp.determinant : (cp.hessian_det !== undefined ? cp.hessian_det : '—');
        
        // Badge según naturaleza
        const natureLower = String(nature).toLowerCase();
        let badgeClass = 'bg-secondary';
        if(natureLower.includes('mínimo') || natureLower.includes('minimo') || natureLower.includes('minimum')){
          badgeClass = 'bg-success';
        } else if(natureLower.includes('máximo') || natureLower.includes('maximo') || natureLower.includes('maximum')){
          badgeClass = 'bg-danger';
        } else if(natureLower.includes('silla') || natureLower.includes('saddle')){
          badgeClass = 'bg-warning text-dark';
        }
        
        html += `
          <tr>
            <td><strong>P${idx + 1}</strong></td>
            <td><code>${formatPoint(point)}</code></td>
            <td>${typeof value === 'number' ? formatNum(value) : value}</td>
            <td>${typeof det === 'number' ? formatNum(det) : det}</td>
            <td><span class="badge ${badgeClass}">${nature}</span></td>
          </tr>
        `;
      });
    } else {
      // Mostrar al menos el punto óptimo si existe
      if(meta.optimal_point){
        const nature = meta.nature || '—';
        const natureLower = String(nature).toLowerCase();
        let badgeClass = 'bg-secondary';
        if(natureLower.includes('mínimo') || natureLower.includes('minimo')){
          badgeClass = 'bg-success';
        } else if(natureLower.includes('máximo') || natureLower.includes('maximo')){
          badgeClass = 'bg-danger';
        } else if(natureLower.includes('silla')){
          badgeClass = 'bg-warning text-dark';
        }
        
        html = `
          <tr>
            <td><strong>P1</strong></td>
            <td><code>${formatPoint(meta.optimal_point)}</code></td>
            <td>${meta.optimal_value !== undefined ? formatNum(meta.optimal_value) : '—'}</td>
            <td>${meta.hessian_det !== undefined ? formatNum(meta.hessian_det) : '—'}</td>
            <td><span class="badge ${badgeClass}">${nature}</span></td>
          </tr>
        `;
      } else {
        html = `
          <tr>
            <td colspan="5" class="text-center text-muted">
              <i class="bi bi-info-circle"></i> No se encontraron puntos críticos.
            </td>
          </tr>
        `;
      }
    }
    
    itersEl.innerHTML = html;
  }
  
  // Re-renderizar MathJax
  if(window.MathJax && window.MathJax.typesetPromise){
    const elements = [gradientEl, hessianEl, itersEl].filter(e => e);
    if(elements.length > 0){
      window.MathJax.typesetPromise(elements).catch(err => console.error('MathJax error:', err));
    }
  }
}

// Función para renderizar tabla de puntos críticos (differential) - Legacy
function renderCriticalPointsTable(criticalPoints){
  if(!sections.iterations || !Array.isArray(criticalPoints)) return;
  
  let html = `
    <table class="table table-sm table-striped iterations-table">
      <thead>
        <tr>
          <th>Punto</th>
          <th>Coordenadas</th>
          <th>$f(x^*)$</th>
          <th>Clasificación</th>
        </tr>
      </thead>
      <tbody>
  `;
  
  criticalPoints.forEach((cp, idx) => {
    const badgeClass = {
      'mínimo': 'bg-success',
      'máximo': 'bg-danger',
      'silla': 'bg-warning text-dark',
      'indeterminado': 'bg-secondary'
    }[cp.nature?.toLowerCase()] || 'bg-secondary';
    
    html += `
      <tr>
        <td><strong>P${idx + 1}</strong></td>
        <td><code>${formatPoint(cp.point)}</code></td>
        <td>${formatNumber(cp.value)}</td>
        <td><span class="badge ${badgeClass}">${cp.nature || '—'}</span></td>
      </tr>
    `;
  });
  
  html += '</tbody></table>';
  sections.iterations.innerHTML = html;
  
  // Re-renderizar MathJax
  if(window.MathJax && window.MathJax.typesetPromise){
    window.MathJax.typesetPromise([sections.iterations]);
  }
}

// Función para renderizar la sección específica de QP (Matriz Q, Vector c, etc.)
function renderQPDecomposition(meta){
  // Renderizar Matriz Q
  const matrixQEl = document.getElementById('matrixQ');
  if(matrixQEl && meta.Q){
    const Q = meta.Q;
    let html = '<div class="matrix-display">';
    if(Array.isArray(Q) && Q.length > 0){
      html += '$$Q = \\begin{bmatrix}';
      Q.forEach((row, i) => {
        if(Array.isArray(row)){
          html += row.map(v => typeof v === 'number' ? v.toFixed(4) : v).join(' & ');
        } else {
          html += typeof row === 'number' ? row.toFixed(4) : row;
        }
        if(i < Q.length - 1) html += ' \\\\ ';
      });
      html += '\\end{bmatrix}$$';
    } else {
      html += '<span class="text-muted">No disponible</span>';
    }
    html += '</div>';
    matrixQEl.innerHTML = html;
  }
  
  // Renderizar Vector c
  const vectorCEl = document.getElementById('vectorC');
  if(vectorCEl && meta.c){
    const c = meta.c;
    let html = '<div class="vector-display">';
    if(Array.isArray(c) && c.length > 0){
      html += '$$c = \\begin{bmatrix}';
      html += c.map(v => typeof v === 'number' ? v.toFixed(4) : v).join(' \\\\ ');
      html += '\\end{bmatrix}$$';
    } else {
      html += '<span class="text-muted">No disponible</span>';
    }
    html += '</div>';
    vectorCEl.innerHTML = html;
  }
  
  // Renderizar análisis de convexidad
  const convexityEl = document.getElementById('convexityAnalysis');
  if(convexityEl && meta.convexity){
    const conv = meta.convexity;
    let html = '<div class="convexity-info">';
    
    // Eigenvalues
    if(conv.eigenvalues && conv.eigenvalues.length > 0){
      html += '<p><strong>Eigenvalores de Q:</strong> ';
      html += conv.eigenvalues.map(v => typeof v === 'number' ? v.toFixed(4) : v).join(', ');
      html += '</p>';
    }
    
    // Definiteness
    if(conv.definiteness){
      html += `<p><strong>Definitud:</strong> ${conv.definiteness}</p>`;
    }
    
    // Is convex
    const convexBadge = conv.is_convex 
      ? '<span class="badge bg-success"><i class="bi bi-check-circle"></i> Problema convexo</span>'
      : '<span class="badge bg-warning text-dark"><i class="bi bi-exclamation-triangle"></i> No convexo</span>';
    html += `<p>${convexBadge}</p>`;
    
    html += '</div>';
    convexityEl.innerHTML = html;
  }
  
  // Renderizar tabla de solución KKT
  const itersEl = document.getElementById('iters');
  if(itersEl){
    let html = '';
    
    // Agregar variables primales (x)
    if(meta.x_star && Array.isArray(meta.x_star)){
      meta.x_star.forEach((val, i) => {
        html += `
          <tr>
            <td><code>x${i+1}</code></td>
            <td><strong>${typeof val === 'number' ? val.toFixed(6) : val}</strong></td>
            <td><span class="badge bg-primary">Primal</span></td>
          </tr>
        `;
      });
    }
    
    // Agregar valor óptimo
    if(meta.f_star !== null && meta.f_star !== undefined){
      html += `
        <tr class="table-success">
          <td><code>f(x*)</code></td>
          <td><strong>${typeof meta.f_star === 'number' ? meta.f_star.toFixed(6) : meta.f_star}</strong></td>
          <td><span class="badge bg-success">Valor óptimo</span></td>
        </tr>
      `;
    }
    
    if(html){
      itersEl.innerHTML = html;
    } else {
      itersEl.innerHTML = `
        <tr>
          <td colspan="3" class="text-center text-muted">
            <i class="bi bi-info-circle"></i> No se encontró solución numérica.
          </td>
        </tr>
      `;
    }
  }
  
  // Re-renderizar MathJax
  if(window.MathJax && window.MathJax.typesetPromise){
    const elements = [matrixQEl, vectorCEl, convexityEl, itersEl].filter(e => e);
    if(elements.length > 0){
      window.MathJax.typesetPromise(elements).catch(err => console.error('MathJax error:', err));
    }
  }
}

// Formatea un punto como string
function formatPoint(point){
  if(!point) return '—';
  if(Array.isArray(point)){
    return `(${point.map(v => typeof v === 'number' ? v.toFixed(4) : v).join(', ')})`;
  }
  if(typeof point === 'object'){
    // Objeto como {x: val, y: val}
    const vals = Object.values(point).map(v => typeof v === 'number' ? v.toFixed(4) : v);
    return `(${vals.join(', ')})`;
  }
  return String(point);
}

// Función auxiliar para renderizar gráficas estáticas (PNG/JPG)
function renderStaticPlots(plot2dPath, plot3dPath){
  const plotContour = el('#plotContour');
  const plotSurface = el('#plotSurface');
  
  if(plotContour && plot2dPath){
    // Buscar el body dentro del viz-card, o usar todo el elemento
    const body = plotContour.querySelector('.viz-card__body') || plotContour;
    body.innerHTML = `<img src="${plot2dPath}" alt="Gráfica 2D" style="max-width: 100%; height: auto; border-radius: 8px; display: block;">`;
  }
  
  if(plotSurface && plot3dPath){
    const body = plotSurface.querySelector('.viz-card__body') || plotSurface;
    body.innerHTML = `<img src="${plot3dPath}" alt="Gráfica 3D" style="max-width: 100%; height: auto; border-radius: 8px; display: block;">`;
  }
}

// Función para renderizar puntos críticos de Lagrange
function renderLagrangeCriticalPoints(criticalPoints, xStar, fStar, lambdaStar, nature){
  if(!sections.iterations) return;
  
  // Limpiar contenido anterior
  sections.iterations.innerHTML = '';
  
  // Si hay punto óptimo, mostrar en la tabla
  if(xStar || (criticalPoints && criticalPoints.length > 0)){
    const points = criticalPoints && criticalPoints.length > 0 
      ? criticalPoints 
      : [{ point: xStar, value: fStar, lambda: lambdaStar, nature: nature || 'óptimo' }];
    
    points.forEach((cp, idx) => {
      const tr = document.createElement('tr');
      
      // Determinar los valores
      const pointVal = cp.point || cp.x || xStar;
      const lambdaVal = cp.lambda || cp.lambda_star || lambdaStar;
      const fVal = cp.value || cp.f || fStar;
      const pointNature = cp.nature || nature || '—';
      
      // Badge de clasificación
      const badgeClass = {
        'mínimo': 'bg-success',
        'máximo': 'bg-danger',
        'silla': 'bg-warning text-dark',
        'óptimo': 'bg-primary'
      }[pointNature?.toLowerCase()] || 'bg-secondary';
      
      tr.innerHTML = `
        <td><strong>P${idx + 1}</strong></td>
        <td><code>${formatPoint(pointVal)}</code></td>
        <td><code>${formatPoint(lambdaVal)}</code></td>
        <td>${formatNumber(fVal)}</td>
        <td><span class="badge ${badgeClass}">${pointNature}</span></td>
      `;
      sections.iterations.appendChild(tr);
    });
  } else {
    sections.iterations.innerHTML = `
      <tr>
        <td colspan="5" class="text-center text-muted">
          <i class="bi bi-info-circle"></i> No se encontraron puntos críticos
        </td>
      </tr>
    `;
  }
  
  // Re-renderizar MathJax
  if(window.MathJax && window.MathJax.typesetPromise){
    window.MathJax.typesetPromise([sections.iterations]);
  }
}

// Función para renderizar candidatos KKT
function renderKKTCandidates(candidates, xStar, fStar, isMaximization){
  if(!sections.iterations) return;
  
  // Limpiar contenido anterior
  sections.iterations.innerHTML = '';
  
  if(!candidates || candidates.length === 0){
    sections.iterations.innerHTML = `
      <tr>
        <td colspan="6" class="text-center text-muted">
          <i class="bi bi-info-circle"></i> No se encontraron candidatos válidos que satisfagan las condiciones KKT
        </td>
      </tr>
    `;
    return;
  }
  
  // Encontrar el mejor candidato (menor valor si minimización, mayor si maximización)
  let bestIdx = 0;
  let bestValue = candidates[0]?.objective_value;
  candidates.forEach((c, idx) => {
    if(c.objective_value !== undefined){
      if(isMaximization && c.objective_value > bestValue){
        bestValue = c.objective_value;
        bestIdx = idx;
      } else if(!isMaximization && c.objective_value < bestValue){
        bestValue = c.objective_value;
        bestIdx = idx;
      }
    }
  });
  
  candidates.forEach((candidate, idx) => {
    const tr = document.createElement('tr');
    const isBest = idx === bestIdx && candidate.kkt_valid;
    
    // Formatear variables x*
    const varsStr = candidate.variables 
      ? Object.entries(candidate.variables).map(([k,v]) => `${k}=${formatNumber(v)}`).join(', ')
      : '—';
    
    // Formatear multiplicadores (lambdas y mus combinados)
    let muStr = '—';
    if(candidate.mus && Object.keys(candidate.mus).length > 0){
      muStr = Object.values(candidate.mus).map(v => formatNumber(v)).join(', ');
    }
    if(candidate.lambdas && Object.keys(candidate.lambdas).length > 0){
      const lambdaVals = Object.values(candidate.lambdas).map(v => formatNumber(v)).join(', ');
      muStr = muStr !== '—' ? `λ: ${lambdaVals}, μ: ${muStr}` : `λ: ${lambdaVals}`;
    }
    
    // Valor objetivo
    const fVal = candidate.objective_value !== undefined ? formatNumber(candidate.objective_value) : '—';
    
    // Badge de validez
    const isValid = candidate.kkt_valid || candidate.status === 'valid';
    const validBadge = isValid 
      ? `<span class="badge bg-success"><i class="bi bi-check-circle"></i> Sí</span>`
      : `<span class="badge bg-danger"><i class="bi bi-x-circle"></i> No</span>`;
    
    // Qué restricciones están activas
    const activeStr = candidate.active_constraints 
      ? candidate.active_constraints.join(', ') 
      : (candidate.case_name || `Caso ${idx + 1}`);
    
    tr.innerHTML = `
      <td><strong>${idx + 1}</strong> ${isBest ? '<i class="bi bi-star-fill text-warning" title="Óptimo"></i>' : ''}</td>
      <td>${activeStr}</td>
      <td><code>${varsStr}</code></td>
      <td><code>${muStr}</code></td>
      <td>${fVal}</td>
      <td>${validBadge}</td>
    `;
    
    if(isBest){
      tr.classList.add('table-success');
    }
    
    sections.iterations.appendChild(tr);
  });
  
  // Re-renderizar MathJax
  if(window.MathJax && window.MathJax.typesetPromise){
    window.MathJax.typesetPromise([sections.iterations]);
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
  
  if(rows.length === 0){
    sections.iterations.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Sin iteraciones disponibles</td></tr>';
    return;
  }
  
  rows.forEach(it=>{
    const tr=document.createElement('tr');
    const fmt = (val)=> typeof val === 'number' ? formatNumber(val) : (val ?? '—');
    
    // Formatear x_k como string legible
    let xkStr = '—';
    if(Array.isArray(it.x_k)){
      xkStr = `[${it.x_k.map(v => typeof v === 'number' ? v.toFixed(4) : v).join(', ')}]`;
    } else if(it.x_k !== undefined){
      xkStr = String(it.x_k);
    }
    
    const alphaVal = (typeof it.step === 'number' && !Number.isNaN(it.step)) 
      ? formatNumber(it.step) 
      : (typeof it.alpha === 'number' ? formatNumber(it.alpha) : (it.alpha ?? '—'));
    
    tr.innerHTML = `
      <td>${it.k ?? '—'}</td>
      <td><code class="text-xs">${xkStr}</code></td>
      <td>${fmt(it.f_k)}</td>
      <td>${fmt(it.grad_norm)}</td>
      <td>${alphaVal}</td>
    `;
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
