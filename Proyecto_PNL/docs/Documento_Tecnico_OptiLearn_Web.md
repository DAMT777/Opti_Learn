OptiLearn Web — Documento Técnico del Proyecto

Versión: 0.9 (borrador inicial)
Fecha: 2025-11-07
Autoría: Equipo OptiLearn (base para trabajo colaborativo)

1. Resumen Ejecutivo
- OptiLearn Web es una plataforma educativa basada en Django que analiza, resuelve y explica problemas de optimización no lineal de forma interactiva, con soporte de IA explicativa.
- Combina cálculo simbólico (SymPy), numérico (NumPy/SciPy), visualización (Plotly/Matplotlib), chat educativo (Django Channels) y generación de reportes (ReportLab/FPDF).
- El foco es didáctico: resultados reproducibles, pasos matemáticos claros, recomendaciones guiadas y visualizaciones del proceso de convergencia.

2. Objetivos y Alcance
2.1 Objetivo general
- Desarrollar una aplicación web educativa que resuelva problemas de optimización no lineal y explique el proceso, integrando IA para recomendar métodos y acompañar al usuario.

2.2 Métodos soportados
- Cálculo diferencial (sin restricciones)
- Lagrange (restricciones de igualdad)
- KKT (restricciones de desigualdad)
- Algoritmos por gradiente (p.ej., gradiente descendente con búsqueda de línea)
- Programación cuadrática (QP)

2.3 Alcance funcional
- Análisis de problemas ingresados (simbólico o lenguaje natural).
- Recomendación del método apropiado.
- Resolución paso a paso con explicación iterativa.
- Visualización 2D/3D (contornos, superficies, trayectorias).
- Chat educativo con historial por usuario/sesión.
- Exportación de reportes académicos en PDF con gráficas.

3. Requisitos
3.1 Funcionales
- Ingreso de funciones objetivo y restricciones (texto simbólico, JSON o NL). 
- Análisis automático: detección de variables, tipo de restricción, convexidad local (si aplica), naturaleza cuadrática.
- Sugerencia de método y parámetros iniciales (puntos de arranque, tolerancias, límites).
- Ejecución controlada por iteraciones con métricas (norma del gradiente, error, paso, criterio de parada).
- Chat integrado: IA explica pasos, justifica decisiones, resume resultados y comparte las iteraciones para que el frontend pueda mostrar trayectorias con Plotly.
- Persistencia de problemas, soluciones, iteraciones y mensajes.
- Exportación a PDF con desarrollo y visualizaciones.

3.2 No funcionales
- Rendimiento: respuesta interactiva en < 2 s para análisis; solvers intensivos pueden ejecutarse en background si exceden 2–5 s.
- Seguridad: autenticación Django, CSRF, sanitización de expresiones, límites de tiempo/recursos en cómputo simbólico/numérico.
- Escalabilidad: Channels + Redis; opción de Postgres; contenedores Docker.
- Usabilidad: UI responsiva, accesible, tono didáctico y consistente.
- Portabilidad: ejecución local con SQLite y sin GPU; opcional despliegue en cloud.

4. Arquitectura del Sistema
4.1 Stack principal
- Backend: Django 4.x, Django REST Framework, Django Channels, Redis (canales), Celery (opcional para tareas largas).
- IA: OpenAI (GPT‑4o) o modelo local (Hugging Face) vía wrappers; temperatura 0.5–0.7.
- Cálculo: SymPy, NumPy, SciPy; QP con OSQP/quadprog/cvxopt (según disponibilidad).
- Visualización: Plotly (interactivo) y Matplotlib (estático).
- Reportes: ReportLab o FPDF.
- Base de datos: SQLite (desarrollo) / PostgreSQL (producción).

4.2 Patrón y módulos
- MVT de Django + servicios modulares en `core/` (análisis, solvers, IA) y `utils/` (gráficas, PDF, helpers).
- Comunicación tiempo real: WebSockets (Django Channels) para chat y progreso de métodos.

4.3 Estructura del repositorio (propuesta)
```
opti_learn/
├── manage.py
├── opti_app/
│   ├── models.py            # Usuarios (Django), Problemas, Restricciones, Soluciones, Iteraciones, Chat
│   ├── views.py             # Vistas/Endpoints DRF y páginas
│   ├── urls.py              # Rutas
│   ├── templates/           # HTML (Bootstrap/Tailwind)
│   ├── static/              # CSS, JS, assets
│   ├── routing.py           # Channels routing
│   ├── consumers.py         # WebSocket (chat/progreso)
│   ├── core/
│   │   ├── analyzer.py
│   │   ├── solver_gradiente.py
│   │   ├── solver_lagrange.py
│   │   ├── solver_kkt.py
│   │   ├── solver_cuadratico.py
│   │   ├── recommender_ai.py
│   │   └── ai_prompts.py
│   └── utils/
│       ├── plotter.py
│       ├── pdf_exporter.py
│       └── helpers.py
├── opti_learn/settings.py   # Configuración Django/Channels/DRF
├── requirements.txt
└── docs/
    └── Documento_Tecnico_OptiLearn_Web.md
```

4.4 Integración IA
- Heurísticas deterministas (por estructura del problema) + salida LLM complementaria.
- Prompts predefinidos: Maestro General (análisis), Iterativo (explicaciones), Final (interpretación). 
- Controles: temperatura moderada, longitud limitada, redacción académica y verificaciones con datos numéricos del solver.

5. Modelado de Datos (ORM Django)
5.1 Entidades principales
- Usuario: usar `django.contrib.auth.User` o `AbstractUser` extendido.
- Problema (`Problem`):
  - `id` (UUID), `owner` (FK Usuario, null si anónimo permitido)
  - `title` (str), `description` (text)
  - `objective_expr` (text) — expresión SymPy
  - `variables` (json) — lista de nombres/orden
  - `constraints_raw` (json|text) — originales del usuario
  - `is_quadratic` (bool), `has_equalities` (bool), `has_inequalities` (bool)
  - `created_at`, `updated_at`
- Restricción (`Constraint`):
  - `id`, `problem` (FK), `kind` (eq|le|ge), `expr` (text), `normalized` (text)
- Solución (`Solution`):
  - `id`, `problem` (FK), `method` (enum: differential|lagrange|kkt|gradient|qp)
  - `x_star` (json), `f_star` (float), `status` (ok|infeasible|timeout|error)
  - `iterations_count` (int), `tolerance` (float), `runtime_ms` (int)
  - `explanation_final` (text)
  - `created_at`
- Iteración (`Iteration`):
  - `id`, `solution` (FK), `k` (int), `x_k` (json), `f_k` (float), `grad_norm` (float), `step` (float), `notes` (text)
- Sesión de chat (`ChatSession`):
  - `id`, `user` (FK), `problem` (FK opcional), `created_at`, `active`
- Mensaje de chat (`ChatMessage`):
  - `id`, `session` (FK), `role` (user|assistant|system), `content` (text), `payload` (json con análisis/iteraciones para gráficas), `created_at`

5.2 Índices y consideraciones
- Índices por `owner`, `created_at` en `Problem`.
- En `Iteration`, índice compuesto (`solution`, `k`).
- JSONFields para vectores/matrices (ordenado por variable). 
- Trazabilidad: soft‑delete opcional, auditoría en cambios críticos.

6. API y Rutas
6.1 REST (DRF)
- `POST /api/problems/parse` — Entrada: texto/JSON. Salida: variables, objetivo, restricciones normalizadas, flags (cuadrática/KKT/…).
- `POST /api/problems` — Crea problema; payload con expresiones y metadatos.
- `GET /api/problems/:id` — Detalle; incluye resumen analítico.
- `GET /api/problems` — Lista paginada por usuario/fecha.
- `POST /api/problems/:id/solve` — Ejecuta método sugerido o forzado; retorna `Solution` preliminar o `202 Accepted` y WS para progreso.
- `GET /api/solutions/:id` — Resultado final; vínculo a reporte y gráficas.
- `GET /api/problems/:id/iterations` — Iteraciones (para graficar).
- `POST /api/reports/:problem_id` — Genera PDF; retorna URL/descarga.

6.2 WebSocket (Django Channels)
- Ruta: `/ws/chat/:session_id/`
- Mensajes (JSON):
  - Cliente→Servidor: `{type: "user_message", text, problem_id?}`
- Servidor→Cliente (IA): `{type: "assistant_message", text, payload?}` donde `payload.plot` incluye iteraciones, `x_k` y `f_k` para que la UI monte la gráfica correspondiente.
  - Progreso solver: `{type: "iteration", k, x_k, f_k, grad_norm, step}`
  - Estado: `{type: "status", stage: analyzing|solving|done|error, detail}`

6.3 Errores y convenciones
- Respuestas con `code`, `message`, `details`.
- Códigos: 400 (validación), 404, 422 (expresión inválida), 429 (límite), 500 (error interno).

7. Algoritmos y Cálculo
7.1 Analyzer (`core/analyzer.py`)
- Parsear expresiones con SymPy (`sympify` con `locals` permitidos, sin `eval`).
- Detectar variables libres, tipo de restricción (eq/le/ge), y evaluar si la función es cuadrática: `f.as_quadratic_form()` o inspección de polinomio.
- Señales: convexidad local (Hessiano semidefinido) cuando aplicable; warnings si no se determina.
- Salida estructurada (dict/JSON) con: variables ordenadas, objetivo, restricciones normalizadas, flags.

7.2 Gradiente descendente (`core/solver_gradiente.py`)
- Entrada: `f(x)`, `x0`, `tol`, `max_iter`, `line_search` (backtracking Armijo o Wolfe).
- Bucle: calcular `grad f(x_k)`, norma, determinar `alpha_k` (búsqueda de línea), actualizar `x_{k+1} = x_k - alpha_k ∇f(x_k)`.
- Criterios de parada: `||∇f|| < tol`, cambio relativo pequeño o `max_iter`.
- Registrar iteraciones con `x_k`, `f_k`, `grad_norm`, `alpha_k`.

7.3 Lagrange (`core/solver_lagrange.py`)
- Formar `L(x, λ) = f(x) + Σ λ_i g_i(x)` (igualdades `g_i(x)=0`).
- Resolver sistema estacionario `∇_x L = 0`, `g(x) = 0` con SymPy/SciPy (no lineal). Verificar Hessiano en el candidato para clasificar (mín/max/silla) con pruebas de definitud.

7.4 KKT (`core/solver_kkt.py`)
- Para desigualdades `h_j(x) ≤ 0`: condiciones `∇f + Σ λ_i ∇g_i + Σ μ_j ∇h_j = 0`, `g=0`, `h≤0`, `μ≥0`, `μ_j h_j(x)=0`.
- Estrategia: 
  1) Intento simbólico (pequeños sistemas) con `nsolve` + penalización/complementariedad suavizada.
  2) Si el problema es cuadrático y restricciones lineales → derivar QP y delegar a solver QP.
- Verificación: factibilidad y complementariedad numérica.

7.5 Programación Cuadrática (`core/solver_cuadratico.py`)
- Forma estándar: minimizar `0.5 x^T Q x + c^T x` s.a. `A x ≤ b`, `A_eq x = b_eq`.
- Solvers: OSQP (preferido), quadprog o cvxopt según disponibilidad.
- Validar que `Q` sea simétrica (y PSD para convexidad). Normalizar restricciones.

7.6 Estabilidad y límites
- Normalización de escalas (estandarizar variables) para mejorar condición numérica.
- Límites de tiempo por iteración y global (por configuración).
- Manejo de errores y estados: `ok`, `infeasible`, `unbounded`, `timeout`.

8. Módulo de IA
8.1 Recomendación (`core/recommender_ai.py`)
- Heurística: 
  - Sin restricciones → gradiente/diferencial (si analítico resuelve).
  - Igualdades → Lagrange.
  - Desigualdades → KKT; si cuadrático convexo con lineales → QP.
- LLM: validar/justificar recomendación con breve explicación; estilo académico.

8.2 Prompts (`core/ai_prompts.py`)
- Maestro General: realiza el diagnóstico del problema y sugiere el método con fundamento.
- Iterativo: explica cada iteración, interpreta `∇f`, paso y convergencia.
- Final: resume el resultado, clasifica el punto (mín/max/silla) y limita alcances.
- Parámetros: temperatura 0.5–0.7, `max_tokens` controlado, español formal y claro.

8.3 Seguridad IA
- No inventar resultados: la IA debe referenciar datos del solver (inputs numéricos/ simbólicos) y evitar especulación.
- Filtrar contenido del chat y limitar longitud para estabilidad.

9. Visualización (`utils/plotter.py`)
- 2D: curvas de nivel de `f(x,y)` + trayectoria `{x_k}`.
- 3D: superficie `z=f(x,y)` con malla; resaltar camino de descenso.
- Exportación: guardar PNG/SVG para PDF; controles de densidad y rango.

10. Reportes (`utils/pdf_exporter.py`)
- Contenido: descripción del problema, método, desarrollo paso a paso, tablas de iteraciones, explicaciones IA, gráficas y conclusiones.
- Plantilla consistente, portada y numeración. Compatible multiplataforma.

11. UI/UX
- Framework: Bootstrap 5 o TailwindCSS.
- Disposición: barra lateral (métodos + historial), zona principal (chat+resultados), panel superior (estado/método sugerido).
- Paleta cromática: 
  - Fondo: #eff9ff – #dcf1fd
  - Secundarios: #c1e7fc, #96d9fa, #65c2f5, #40a6f1
  - Primarios: #2185e4, #2274d3
  - Contraste: #225dab, #215087, #193152
- Lineamientos: 
  - Fondo degradado (#eff9ff→#dcf1fd).
  - Barra lateral con gradiente azul suave (#c1e7fc→#65c2f5).
  - Botones #2185e4 (hover #2274d3), textos #193152.
  - Sombras sutiles, bordes 16px, tipografías Poppins/Inter.

12. Seguridad
- Autenticación y autorización: Django Auth, sesiones/DRF tokens. Posible SSO futuro.
- CSRF, XSS y sanitización de entradas: usar `sympy.sympify` con `locals` controlados (sin `eval`).
- Rate‑limit en chat/API y tamaño de payloads.
- Aislar ejecución de solvers largos (hilos/tareas) con límites de tiempo y memoria.
- Gestión segura de claves (OpenAI/HF) vía variables de entorno.

13. Pruebas y Calidad
- Unitarias: 
  - `analyzer`: parsing, normalización, detección de estructura.
  - `solvers`: convergencia en funciones de prueba (cuadráticas convexas, Rosenbrock reducido, etc.).
- Integración: endpoints DRF y flujo chat por Channels.
- E2E (opcional): Playwright para UI básica.
- Datos sintéticos y fixtures para reproducibilidad.

14. DevOps y Despliegue
- Variables de entorno: 
  - `DJANGO_SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`
  - `DATABASE_URL` (o `DB_*`), `REDIS_URL`
  - `OPENAI_API_KEY` (si se usa), `HF_MODEL` (alternativa local)
- Docker (propuesto):
  - Servicios: `web` (Django+Gunicorn+Daphne), `redis`, `db` (Postgres), `worker` (Celery, opcional), `nginx`.
- Static/Media: `collectstatic`, caché de assets, compresión.
- Observabilidad: logging estructurado (JSON), métricas básicas (tiempos de solver, iteraciones, errores).

15. Roadmap y Hitos (propuesta)
- MVP (Semanas 1–4):
  - Proyecto Django/DRF/Channels + UI base.
  - `analyzer` con SymPy (variables, restricciones, cuadrática).
  - Solver: gradiente descendente (2D/ND) con backtracking.
  - Visualización 2D + PDF básico.
- v1.1 (Semanas 5–6):
  - Lagrange (igualdades) con clasificación de punto.
  - Chat IA (maestro e iterativo) + persistencia.
- v1.2 (Semanas 7–8):
  - KKT (desigualdades) para casos pequeños.
  - QP con OSQP/quadprog.
  - Reportes enriquecidos y gráficas 3D.
- v1.3 (Semanas 9–10):
  - Mejoras UX, accesibilidad, refactor y endurecimiento de seguridad.

16. Riesgos y Mitigaciones
- Inestabilidad numérica en problemas mal condicionados → normalización de variables, escalado, verificación de Hessiano y tolerancias adaptativas.
- Tiempo de cómputo alto en simbólico/solución no lineal → límites de tiempo, fallback a métodos numéricos, ejecución asíncrona.
- Errores de parsing o expresiones complejas → mensajes de validación claros, ejemplos, documentación in‑app.
- Dependencia de IA externa → opción de modelo local y caché de explicaciones.

17. Ejemplos de Esquemas (contratos de datos)
- Problema (crear):
  ```json
  {
    "title": "Rosenbrock reducido",
    "objective_expr": "(1 - x)**2 + 100*(y - x**2)**2",
    "variables": ["x", "y"],
    "constraints": [
      {"kind": "eq", "expr": "x + y - 1"},
      {"kind": "le", "expr": "x - 0.5"}
    ]
  }
  ```
- Iteración (evento WS):
  ```json
  {"type":"iteration","k":7,"x_k":[0.91,0.83],"f_k":0.021,"grad_norm":0.12,"step":0.05}
  ```
- Mensaje IA:
  ```json
  {"type":"assistant_message","text":"El gradiente en k=7 es pequeño; el paso se reduce por Armijo."}
  ```

18. Guías de Implementación (stubs mínimos)
- `core/analyzer.py` (idea):
  - `analyze_problem(text_or_json) -> dict`: parsea SymPy, identifica variables, clasifica restricciones, intenta extraer forma cuadrática (Q, c) si aplica.
- `core/solver_gradiente.py` (idea):
  - `solve(f, vars, x0, tol=1e-6, max_iter=500, line_search='armijo') -> Solution + [Iteration]`.
- `core/recommender_ai.py` (idea):
  - `recommend(problem_meta) -> {method, rationale}` combinando heurística + LLM.
- `utils/plotter.py` (idea):
  - `contour_with_path(f, vars, iters) -> fig` y `surface3d(...)`.
- `utils/pdf_exporter.py` (idea):
  - `build_report(problem, solution, iterations, figures) -> bytes`.

19. Instalación y Entorno (desarrollo)
- Requisitos: Python 3.11+, Node (si se usa build de assets), Redis (para Channels en local, opcional con canal de memoria en desarrollo).
- Paquetes (requirements): Django, djangorestframework, channels, channels-redis, sympy, numpy, scipy, plotly, matplotlib, reportlab (o fpdf), openai (opcional), osqp/quadprog/cvxopt (según plataforma).
- Comandos sugeridos:
  - `python -m venv .venv && .venv\Scripts\activate` (Windows)
  - `pip install -r requirements.txt`
  - `python manage.py migrate && python manage.py runserver`

20. Criterios de Aceptación (MVP)
- Dado un problema sin restricciones, el sistema:
  - Analiza variables y sugiere gradiente.
  - Ejecuta el método con al menos 1 visualización 2D.
  - Muestra explicaciones de IA por iteración (texto breve, consistente con los datos numéricos).
  - Genera un PDF con resumen, iteraciones y gráfica.

Anexo A — Notas de Implementación SymPy
- Usar `sympy.symbols` para variables y `sympy.sympify` para parseo seguro con un dict de funciones permitidas (sin builtins peligrosos).
- Derivadas: `sympy.diff`; gradiente como lista; Hessiano con `sympy.hessian`.
- Evaluaciones numéricas con `lambdify` (módulos `numpy`) para velocidad.

Anexo B — Convenciones de Nombres
- Variables vectoriales en listas/arrays ordenadas según `variables`.
- Iteraciones indexadas desde k=0.
- Campos JSON con claves minúsculas y snake_case.

Fin del documento.
