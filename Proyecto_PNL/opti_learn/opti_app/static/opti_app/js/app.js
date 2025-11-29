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
      // Preservar bloques LaTeX antes de procesar Markdown
      const latexBlocks = [];
      let processedText = String(text || '');
      
      // Guardar bloques $$ ... $$ 
      processedText = processedText.replace(/\$\$([\s\S]*?)\$\$/g, (match, content) => {
        latexBlocks.push(match);
        return `%%LATEX_BLOCK_${latexBlocks.length - 1}%%`;
      });
      
      // Guardar bloques $ ... $ (inline)
      processedText = processedText.replace(/\$([^\$\n]+?)\$/g, (match, content) => {
        latexBlocks.push(match);
        return `%%LATEX_INLINE_${latexBlocks.length - 1}%%`;
      });
      
      // Procesar Markdown
      let raw = window.marked.parse(processedText, { breaks: true });
      
      // Restaurar bloques LaTeX
      raw = raw.replace(/%%LATEX_BLOCK_(\d+)%%/g, (match, idx) => latexBlocks[parseInt(idx)]);
      raw = raw.replace(/%%LATEX_INLINE_(\d+)%%/g, (match, idx) => latexBlocks[parseInt(idx)]);
      
      if(window.DOMPurify){
        return window.DOMPurify.sanitize(raw, { 
          USE_PROFILES: { html: true },
          ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
                         'code', 'pre', 'blockquote', 'a', 'span', 'div', 'table', 'thead', 'tbody', 
                         'tr', 'th', 'td', 'hr', 'img'],
          ADD_ATTR: ['class', 'href', 'src', 'alt']
        });
      }
      return raw;
    }
  }catch(e){
    console.error('Error rendering markdown:', e);
  }
  return String(text || '').replace(/</g,'&lt;');
}

function attachPlotForPayload(payload, bubble){
  if(!payload || !bubble) return;
  const bubbleEl = bubble.closest('.bubble') || bubble;
  if(!bubbleEl) return;
  
  // Remover plots anteriores
  bubbleEl.querySelectorAll('.assistant-plot').forEach(node => node.remove());
  
  // NUEVO: Manejar imágenes estáticas (Lagrange, Differential)
  const plot2dPath = payload.plot_2d_path;
  const plot3dPath = payload.plot_3d_path;
  if(plot2dPath || plot3dPath){
    const plotContainer = document.createElement('div');
    plotContainer.className = 'assistant-plot static-plots-container';
    plotContainer.style.cssText = 'display: flex; flex-wrap: wrap; gap: 16px; margin-top: 16px; justify-content: center;';
    
    if(plot2dPath){
      const img2d = document.createElement('img');
      img2d.src = plot2dPath;
      img2d.alt = 'Gráfica 2D';
      img2d.style.cssText = 'max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.2);';
      img2d.onerror = () => { img2d.style.display = 'none'; };
      plotContainer.appendChild(img2d);
    }
    
    if(plot3dPath){
      const img3d = document.createElement('img');
      img3d.src = plot3dPath;
      img3d.alt = 'Gráfica 3D';
      img3d.style.cssText = 'max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.2);';
      img3d.onerror = () => { img3d.style.display = 'none'; };
      plotContainer.appendChild(img3d);
    }
    
    const md = bubbleEl.querySelector('.md');
    if(md){
      md.insertAdjacentElement('afterend', plotContainer);
    } else {
      bubbleEl.appendChild(plotContainer);
    }
    return; // Ya manejamos las imágenes estáticas
  }
  
  // Continuar con manejo de plots interactivos (Plotly)
  if(!payload.plot) return;
  const plotData = payload.plot.plot_data;
  if(plotData && plotData.allow_plots === false){
    return;
  }
  if(plotData) bubbleEl.__gradientPlotData = plotData;
  // 1D: graficar f(x) y trayectoria si existe func_1d
  if(plotData && plotData.func_1d && window.Plotly){
    const chart = document.createElement('div');
    chart.className = 'assistant-plot';
    chart.style.display = 'block';
    chart.style.height = '320px';
    chart.style.minHeight = '320px';
    chart.style.width = '100%';
    const md = bubbleEl.querySelector('.md');
    if(md){
      md.insertAdjacentElement('afterend', chart);
    } else {
      bubbleEl.appendChild(chart);
    }
    renderFunction1D(chart, plotData);
    return;
  }
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
    surfaceChart.classList.add('plot-1d');
    renderFunction1D(surfaceChart, plotData);
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
  const heatTrace = {
    type: 'contour',
    x: mesh.x,
    y: mesh.y,
    z: mesh.z,
    colorscale: theme.contourScale,
    contours: {
      coloring: 'heatmap',
      showlines: false,
      start: zStart,
      end: zEnd,
      size: contourStep,
    },
    showscale: false,
    opacity: 0.75,
  };
  const contourLineTrace = {
    type: 'contour',
    x: mesh.x,
    y: mesh.y,
    z: mesh.z,
    contours: {
      coloring: 'lines',
      showlabels: false,
      start: zStart,
      end: zEnd,
      size: contourStep,
    },
    line: { width: 1.2, color: theme.axis },
    showscale: false,
    opacity: 1,
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
  Plotly.newPlot(chart, [heatTrace, contourLineTrace, trailTrace], layout, config);
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

function renderFunction1D(chart, plotData){
  const theme = resolvePlotTheme();
  const curve = plotData.func_1d;
  chart.innerHTML = '';
  chart.style.display = 'block';
  chart.style.height = '320px';
  chart.style.minHeight = '320px';
  chart.style.width = '100%';
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
  Plotly.newPlot(chart, [funcTrace, pathTrace], layout, {responsive:true, displayModeBar:false});
  setTimeout(()=> { try{ Plotly.Plots.resize(chart); }catch{} }, 60);
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
  const wsUrl = new URL(`ws/chat/${sid}/`, window.location.href);
  wsUrl.protocol = `${proto}:`;
  ws = new WebSocket(wsUrl);
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
      refreshAssistantPlotsTheme();
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
      const apiUrl = new URL('api/ai/chat', window.location.href);
      fetch(apiUrl, {
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

function refreshAssistantPlotsTheme(){
  document.querySelectorAll('.bubble').forEach(bubble=>{
    if(bubble.__gradientPlotData){
      renderGradientPlots(bubble.__gradientPlotData, bubble, { surfaceOnly: false });
    }
  });
  if(!window.Plotly) return;
  const theme = resolvePlotTheme();
  document.querySelectorAll('.js-plotly-plot').forEach(node=>{
    try{
      Plotly.relayout(node, {
        paper_bgcolor: theme.paper,
        plot_bgcolor: theme.plot,
        'xaxis.color': theme.axis,
        'xaxis.gridcolor': theme.grid,
        'xaxis.zerolinecolor': theme.zero,
        'yaxis.color': theme.axis,
        'yaxis.gridcolor': theme.grid,
        'yaxis.zerolinecolor': theme.zero,
        'scene.xaxis.color': theme.axis,
        'scene.xaxis.gridcolor': theme.grid,
        'scene.yaxis.color': theme.axis,
        'scene.yaxis.gridcolor': theme.grid,
        'scene.zaxis.color': theme.axis,
        'scene.zaxis.gridcolor': theme.grid,
      });
    }catch{}
  });
}

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
