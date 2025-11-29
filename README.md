<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Django-5.x-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django">
  <img src="https://img.shields.io/badge/SymPy-1.12+-green?style=for-the-badge&logo=sympy&logoColor=white" alt="SymPy">
  <img src="https://img.shields.io/badge/AI-Groq_LLaMA-orange?style=for-the-badge&logo=openai&logoColor=white" alt="Groq AI">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="License">
</p>

<h1 align="center">🎓 OptiLearn Web</h1>

<p align="center">
  <strong>Plataforma Educativa Interactiva para Optimización No Lineal</strong>
</p>

<p align="center">
  Una aplicación web moderna que analiza, resuelve y explica problemas de optimización no lineal de forma interactiva, con asistente de IA integrado.
</p>

---

## 📋 Tabla de Contenidos

- [🎯 Descripción](#-descripción)
- [✨ Características](#-características)
- [🛠️ Métodos Soportados](#️-métodos-soportados)
- [🏗️ Arquitectura](#️-arquitectura)
- [📦 Requisitos](#-requisitos)
- [🚀 Instalación](#-instalación)
- [⚙️ Configuración](#️-configuración)
- [🎮 Uso](#-uso)
- [📁 Estructura del Proyecto](#-estructura-del-proyecto)
- [🤖 Sistema de Detección Inteligente](#-sistema-de-detección-inteligente)
- [🔧 API Reference](#-api-reference)
- [📊 Visualizaciones](#-visualizaciones)
- [🧪 Testing](#-testing)
- [🤝 Contribución](#-contribución)
- [📄 Licencia](#-licencia)

---

## 🎯 Descripción

**OptiLearn Web** es una plataforma educativa basada en Django diseñada para estudiantes y profesionales que desean aprender y resolver problemas de **Programación No Lineal (PNL)**. 

La aplicación combina:
- 🧮 **Cálculo simbólico** con SymPy
- 📈 **Cálculo numérico** con NumPy/SciPy
- 📊 **Visualización interactiva** 2D/3D con Plotly y Matplotlib
- 💬 **Asistente de IA** educativo con Groq (LLaMA)
- 📄 **Generación de reportes** académicos en PDF

### 🎓 Enfoque Didáctico

El objetivo principal es **enseñar optimización**, no solo resolverla. Cada solución incluye:
- Pasos matemáticos detallados
- Explicaciones en lenguaje natural
- Visualizaciones del proceso de convergencia
- Interpretación de resultados

---

## ✨ Características

### 🔹 Interfaz Dual
| Modo Manual | Modo Asistente IA |
|-------------|-------------------|
| Formularios estructurados por método | Chat en lenguaje natural |
| Control total de parámetros | Detección automática del método |
| Resultados inmediatos | Explicaciones pedagógicas |
| Ideal para práctica | Ideal para aprendizaje |

### 🔹 Capacidades Principales

- ✅ **Análisis automático** de problemas (variables, restricciones, convexidad)
- ✅ **Recomendación inteligente** del método óptimo
- ✅ **Resolución paso a paso** con explicaciones detalladas
- ✅ **Visualización 2D/3D** de funciones y trayectorias
- ✅ **Chat educativo** con historial por sesión
- ✅ **Exportación PDF** con gráficas y desarrollo completo
- ✅ **Renderizado LaTeX** para fórmulas matemáticas
- ✅ **Tiempo real** via WebSockets (Django Channels)

---

## 🛠️ Métodos Soportados

OptiLearn implementa **5 métodos de optimización** cubriendo los casos más comunes de PNL:

### 1. 📐 Cálculo Diferencial (Sin Restricciones)
```
Minimizar/Maximizar f(x)
```
- Calcula gradiente y Hessiano
- Encuentra puntos críticos (∇f = 0)
- Clasifica puntos usando criterio de la segunda derivada
- Determina máximos, mínimos y puntos silla

### 2. ⚖️ Multiplicadores de Lagrange (Restricciones de Igualdad)
```
Minimizar f(x)
sujeto a: g(x) = 0
```
- Construye la función Lagrangiana L(x, λ)
- Resuelve sistema de ecuaciones estacionarias
- Clasifica puntos usando Hessiano orlado
- Visualización de curvas de nivel

### 3. 📊 Condiciones KKT (Restricciones de Desigualdad)
```
Minimizar f(x)
sujeto a: g(x) = 0, h(x) ≤ 0
```
- Aplica condiciones de Karush-Kuhn-Tucker
- Verifica factibilidad primal y dual
- Analiza complementariedad (μ·h(x) = 0)
- Soporta múltiples restricciones

### 4. 🔄 Gradiente Descendente (Método Iterativo)
```
x_{k+1} = x_k - α·∇f(x_k)
```
- Búsqueda de línea (Armijo backtracking)
- Visualización de trayectoria de convergencia
- Métricas por iteración (norma del gradiente, paso)
- Criterios de parada configurables

### 5. 📦 Programación Cuadrática (QP)
```
Minimizar ½x'Qx + c'x
sujeto a: Ax ≤ b, A_eq·x = b_eq
```
- Análisis de convexidad (eigenvalores de Q)
- Múltiples solvers: KKT simbólico, numérico, simplex
- Descomposición de la matriz Q
- Verificación de optimalidad

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  Chat IA    │  │  Forms      │  │  Visualizaciones        │  │
│  │  (WebSocket)│  │  (REST API) │  │  (Plotly/Matplotlib)    │  │
│  └──────┬──────┘  └──────┬──────┘  └────────────┬────────────┘  │
└─────────┼────────────────┼──────────────────────┼───────────────┘
          │                │                      │
          ▼                ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DJANGO BACKEND                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    API Layer                             │    │
│  │  • REST Framework (views.py)                            │    │
│  │  • WebSocket Consumers (consumers.py)                   │    │
│  └──────────────────────────┬──────────────────────────────┘    │
│                             │                                    │
│  ┌──────────────────────────┼──────────────────────────────┐    │
│  │                    CORE MODULES                          │    │
│  │  ┌──────────────┐  ┌─────┴──────┐  ┌─────────────────┐  │    │
│  │  │ analyzer.py  │  │ method_    │  │ recommender_    │  │    │
│  │  │ (Parse/Eval) │  │ detector   │  │ ai.py           │  │    │
│  │  └──────────────┘  └────────────┘  └─────────────────┘  │    │
│  │                                                          │    │
│  │  ┌─────────────────────────────────────────────────┐    │    │
│  │  │              SOLVERS                             │    │    │
│  │  │  • solver_differential.py                       │    │    │
│  │  │  • solver_lagrange.py                           │    │    │
│  │  │  • solver_kkt.py                                │    │    │
│  │  │  • solver_gradiente.py                          │    │    │
│  │  │  • solver_qp_*.py                               │    │    │
│  │  └─────────────────────────────────────────────────┘    │    │
│  │                                                          │    │
│  │  ┌─────────────────────────────────────────────────┐    │    │
│  │  │           VISUALIZERS                            │    │    │
│  │  │  • visualizer_lagrange.py / _3d.py             │    │    │
│  │  │  • visualizer_differential.py / _3d.py         │    │    │
│  │  └─────────────────────────────────────────────────┘    │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │                    AI SERVICE                             │    │
│  │  • groq_service.py (LLaMA via Groq API)                  │    │
│  │  • Prompts contextuales educativos                       │    │
│  │  • Scope guard (limita a temas de PNL)                   │    │
│  └──────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       DATA LAYER                                 │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────────┐     │
│  │  SQLite    │  │  Static    │  │  Temporary Files       │     │
│  │  (DB)      │  │  Files     │  │  (Plots PNG/SVG)       │     │
│  └────────────┘  └────────────┘  └────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

### Stack Tecnológico

| Capa | Tecnología |
|------|------------|
| **Backend** | Django 5.x, Django REST Framework, Django Channels |
| **IA** | Groq API (LLaMA 3), prompts personalizados |
| **Cálculo** | SymPy (simbólico), NumPy/SciPy (numérico) |
| **Visualización** | Plotly (3D interactivo), Matplotlib (2D estático) |
| **Frontend** | Bootstrap 5, JavaScript vanilla, MathJax (LaTeX) |
| **BD** | SQLite (desarrollo), PostgreSQL (producción) |
| **WebSocket** | Django Channels (ASGI) |

---

## 📦 Requisitos

### Requisitos del Sistema
- Python 3.11 o superior
- pip (gestor de paquetes)
- Git

### Dependencias Principales

```txt
Django>=4.2
djangorestframework>=3.15
channels>=4.0
sympy>=1.12
numpy>=1.26
python-dotenv>=1.0
groq>=0.10.0

# Opcionales
plotly>=5.24
matplotlib>=3.9
scipy>=1.11
reportlab>=4.2
```

---

## 🚀 Instalación

### 1. Clonar el Repositorio

```bash
git clone https://github.com/DAMT777/Programacion_No_Lineal.git
cd Programacion_No_Lineal
```

### 2. Crear Entorno Virtual

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Linux/macOS:**
```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

Crear archivo `.env` en `opti_learn/`:

```env
# Django
DJANGO_SECRET_KEY=tu-clave-secreta-aqui
DEBUG=1
ALLOWED_HOSTS=127.0.0.1,localhost

# Groq API (para asistente IA)
GROQ_API_KEY=gsk_tu_api_key_aqui
```

> 💡 **Obtener API Key de Groq:** Visita [console.groq.com](https://console.groq.com) para obtener tu API key gratuita.

### 5. Aplicar Migraciones

```bash
cd opti_learn
python manage.py migrate
```

### 6. Recopilar Archivos Estáticos

```bash
python manage.py collectstatic --noinput
```

### 7. Ejecutar Servidor de Desarrollo

```bash
python manage.py runserver
```

Abre tu navegador en: **http://127.0.0.1:8000**

---

## ⚙️ Configuración

### Variables de Entorno

| Variable | Descripción | Default |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Clave secreta de Django | `dev-insecure-secret-key` |
| `DEBUG` | Modo debug | `1` |
| `ALLOWED_HOSTS` | Hosts permitidos | `127.0.0.1,localhost` |
| `GROQ_API_KEY` | API Key de Groq | - |
| `DATABASE_URL` | URL de base de datos | SQLite |

### Configuración de IA

En `settings.py`:

```python
AI_ASSISTANT = {
    "prompt_path": "opti_app/ai/prompt_contextual.txt",
    "model": "llama-3.3-70b-versatile",
    "temperature": 0.5,
    "max_tokens": 2048,
}
```

---

## 🎮 Uso

### Modo Formulario Manual

1. Selecciona un método en la barra lateral
2. Ingresa la función objetivo
3. Define variables y restricciones (si aplica)
4. Configura parámetros (tolerancia, iteraciones, etc.)
5. Presiona "Resolver"

**Ejemplo - Lagrange:**
```
Función objetivo: x^2 + y^2
Restricción: x + y - 1 = 0
```

### Modo Asistente IA

Escribe tu problema en lenguaje natural:

```
"Minimiza x² + y² sujeto a x + y = 1"
"Encuentra los puntos críticos de f(x,y) = x³ - 3xy + y³"
"Resuelve el problema QP: min ½(x² + y²) + 2x + 3y con x ≥ 0, y ≥ 0"
```

El asistente:
1. Detecta automáticamente el método apropiado
2. Resuelve paso a paso
3. Genera visualizaciones
4. Explica los resultados

---

## 📁 Estructura del Proyecto

```
Proyecto_PNL/
├── 📄 README.md                    # Este archivo
├── 📄 requirements.txt             # Dependencias Python
├── 📄 .gitignore                   # Archivos ignorados por Git
│
└── 📁 opti_learn/                  # Proyecto Django
    ├── 📄 manage.py                # CLI de Django
    ├── 📄 .env                     # Variables de entorno (no versionado)
    │
    ├── 📁 opti_learn/              # Configuración del proyecto
    │   ├── settings.py             # Configuración Django
    │   ├── urls.py                 # URLs principales
    │   ├── asgi.py                 # ASGI (WebSockets)
    │   └── wsgi.py                 # WSGI (HTTP)
    │
    ├── 📁 opti_app/                # Aplicación principal
    │   ├── 📄 models.py            # Modelos de datos
    │   ├── 📄 views.py             # Vistas y API endpoints
    │   ├── 📄 urls.py              # Rutas de la app
    │   ├── 📄 consumers_ai.py      # WebSocket consumers
    │   ├── 📄 routing.py           # Rutas WebSocket
    │   │
    │   ├── 📁 core/                # Lógica de negocio
    │   │   ├── analyzer.py         # Análisis de problemas
    │   │   ├── method_detector.py  # Detección de métodos
    │   │   ├── message_parser.py   # Parser de mensajes
    │   │   ├── recommender_ai.py   # Recomendador IA
    │   │   ├── scope_guard.py      # Validación de alcance
    │   │   ├── solver_differential.py
    │   │   ├── solver_lagrange.py
    │   │   ├── solver_kkt.py
    │   │   ├── solver_gradiente.py
    │   │   ├── solver_cuadratico.py
    │   │   ├── solver_qp_*.py      # Solvers QP
    │   │   └── visualizer_*.py     # Generadores de gráficas
    │   │
    │   ├── 📁 ai/                  # Servicios de IA
    │   │   ├── groq_service.py     # Cliente Groq API
    │   │   └── prompt_contextual.txt
    │   │
    │   ├── 📁 templates/           # Plantillas HTML
    │   │   ├── index.html          # Página principal
    │   │   └── methods/            # Páginas por método
    │   │
    │   ├── 📁 static/              # Archivos estáticos
    │   │   └── opti_app/
    │   │       ├── css/app_v2.css  # Estilos principales
    │   │       └── js/
    │   │           ├── app.js      # Chat IA
    │   │           └── method.js   # Formularios
    │   │
    │   └── 📁 migrations/          # Migraciones de BD
    │
    └── 📁 staticfiles/             # Static compilados (generado)
```

---

## 🤖 Sistema de Detección Inteligente

OptiLearn implementa un **sistema de 6 reglas** para detectar automáticamente qué método usar:

```
┌─────────────────────────────────────────────────────────────┐
│                    ENTRADA DEL USUARIO                       │
│           (Lenguaje natural o expresión matemática)          │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ REGLA 1: ¿Pide proceso iterativo?                           │
│ Keywords: "iterar", "gradiente descendente", "learning rate"│
│ ───────────────────────────────────────────────────────────│
│ SÍ → GRADIENTE DESCENDENTE                                  │
└─────────────────────────────┬───────────────────────────────┘
                              │ NO
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ REGLA 2: ¿Tiene restricciones NO LINEALES de desigualdad?   │
│ Ejemplo: x² + y² ≤ 1                                        │
│ ───────────────────────────────────────────────────────────│
│ SÍ → KKT                                                    │
└─────────────────────────────┬───────────────────────────────┘
                              │ NO
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ REGLA 3: ¿Tiene SOLO restricciones de IGUALDAD?             │
│ Ejemplo: x + y = 1, g(x,y) = 0                             │
│ ───────────────────────────────────────────────────────────│
│ SÍ → LAGRANGE                                               │
└─────────────────────────────┬───────────────────────────────┘
                              │ NO
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ REGLA 4: ¿Función CUADRÁTICA con restricciones LINEALES?    │
│ f = ½x'Qx + c'x,  Ax ≤ b                                   │
│ ───────────────────────────────────────────────────────────│
│ SÍ → PROGRAMACIÓN CUADRÁTICA (QP)                           │
└─────────────────────────────┬───────────────────────────────┘
                              │ NO
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ REGLA 5: ¿Pide derivadas/puntos críticos SIN restricciones? │
│ Keywords: "punto crítico", "máximo", "mínimo", "derivada"  │
│ ───────────────────────────────────────────────────────────│
│ SÍ → CÁLCULO DIFERENCIAL                                    │
└─────────────────────────────┬───────────────────────────────┘
                              │ NO
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ REGLA 6: ANÁLISIS POR ESTRUCTURA                            │
│ • Con desigualdades → KKT                                   │
│ • Con igualdades → LAGRANGE                                 │
│ • Sin restricciones → DIFERENCIAL                           │
└─────────────────────────────────────────────────────────────┘
```

### Prioridades del Detector

| Prioridad | Método | Condición |
|-----------|--------|-----------|
| 1 (Alta) | Gradiente | Keywords iterativos detectados |
| 2 | KKT | Restricciones no lineales de desigualdad |
| 3 | Lagrange | Solo restricciones de igualdad |
| 4 | QP | f cuadrática + restricciones lineales |
| 5 | Diferencial | Keywords de derivadas sin restricciones |
| 6 (Baja) | Por estructura | Análisis del problema |

---

## 🔧 API Reference

### REST Endpoints

#### Parsear Problema
```http
POST /api/problems/parse
Content-Type: application/json

{
  "objective_expr": "x**2 + y**2",
  "constraints": ["x + y - 1 = 0"]
}
```

**Respuesta:**
```json
{
  "variables": ["x", "y"],
  "has_equalities": true,
  "has_inequalities": false,
  "is_quadratic": true,
  "recommended_method": "lagrange"
}
```

#### Resolver - Cálculo Diferencial
```http
POST /api/solve/differential
Content-Type: application/json

{
  "objective": "x**3 - 3*x*y + y**3",
  "variables": ["x", "y"]
}
```

#### Resolver - Lagrange
```http
POST /api/solve/lagrange
Content-Type: application/json

{
  "objective": "x**2 + y**2",
  "constraints_eq": ["x + y - 1"],
  "variables": ["x", "y"]
}
```

#### Resolver - KKT
```http
POST /api/solve/kkt
Content-Type: application/json

{
  "objective": "x**2 + y**2",
  "constraints_eq": [],
  "constraints_ineq": ["x + y - 1"],
  "variables": ["x", "y"]
}
```

#### Resolver - Gradiente
```http
POST /api/solve/gradient
Content-Type: application/json

{
  "objective": "(1-x)**2 + 100*(y-x**2)**2",
  "variables": ["x", "y"],
  "initial_point": [0, 0],
  "max_iter": 1000,
  "tol": 1e-6
}
```

#### Resolver - QP
```http
POST /api/solve/qp
Content-Type: application/json

{
  "Q": [[2, 0], [0, 2]],
  "c": [1, 1],
  "A_ub": [[-1, 0], [0, -1]],
  "b_ub": [0, 0]
}
```

### WebSocket - Chat IA

```javascript
// Conectar
const ws = new WebSocket('ws://localhost:8000/ws/chat/{session_id}/');

// Enviar mensaje
ws.send(JSON.stringify({
  type: 'user_message',
  text: 'Minimiza x² + y² sujeto a x + y = 1'
}));

// Recibir respuesta
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // data.type: 'assistant_message' | 'error' | 'status'
  // data.text: Respuesta del asistente
  // data.payload: Datos adicionales (gráficas, iteraciones)
};
```

---

## 📊 Visualizaciones

OptiLearn genera visualizaciones automáticas según el problema:

### 2D - Curvas de Nivel
- Función objetivo con curvas de nivel
- Punto óptimo destacado
- Restricciones superpuestas (Lagrange/KKT)

### 3D - Superficies
- Superficie de la función objetivo
- Trayectoria de convergencia (Gradiente)
- Punto óptimo con marcador

### Iteraciones (Gradiente)
- Gráfica de convergencia (f vs k)
- Norma del gradiente vs iteración
- Trayectoria en el espacio de variables

---

## 🧪 Testing

```bash
# Ejecutar tests
cd opti_learn
python manage.py test

# Tests específicos
python manage.py test opti_app.tests.test_solvers
python manage.py test opti_app.tests.test_analyzer
```

### Casos de Prueba Incluidos

- ✅ Parsing de expresiones matemáticas
- ✅ Detección de tipos de restricciones
- ✅ Convergencia de solvers en problemas conocidos
- ✅ Clasificación de puntos críticos
- ✅ Integridad de endpoints API

---

## 🤝 Contribución

¡Las contribuciones son bienvenidas! 

### Cómo Contribuir

1. Fork el repositorio
2. Crea una rama feature (`git checkout -b feature/NuevaCaracteristica`)
3. Commit tus cambios (`git commit -m 'Agrega nueva característica'`)
4. Push a la rama (`git push origin feature/NuevaCaracteristica`)
5. Abre un Pull Request

### Áreas de Contribución

- 🐛 Reportar bugs
- 💡 Sugerir nuevas características
- 📖 Mejorar documentación
- 🧪 Agregar tests
- 🎨 Mejorar UI/UX
- ➕ Agregar nuevos métodos de optimización

---

## 👥 Autores

- **Equipo OptiLearn** - *Desarrollo inicial* - [DAMT777](https://github.com/DAMT777)

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

---

## 🙏 Agradecimientos

- [SymPy](https://www.sympy.org/) - Cálculo simbólico
- [Django](https://www.djangoproject.com/) - Framework web
- [Groq](https://groq.com/) - API de LLM ultrarrápida
- [Plotly](https://plotly.com/) - Visualizaciones interactivas
- [MathJax](https://www.mathjax.org/) - Renderizado LaTeX

---

<p align="center">
  <sub>Hecho con ❤️ para la comunidad de Optimización Matemática</sub>
</p>

<p align="center">
  <a href="#-optilearn-web">⬆️ Volver arriba</a>
</p>
