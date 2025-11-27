# Detector Automático de Métodos de Optimización

Este módulo implementa un sistema automático para determinar qué método de optimización usar basándose en el enunciado de un problema.

## 🎯 Objetivo

Dado un enunciado o ejercicio, el sistema:
1. **Determina automáticamente** qué método usar (Gradiente, KKT, Lagrange, QP, o Diferencial)
2. **Extrae los parámetros** necesarios en formato JSON
3. **Explica por qué** se eligió ese método

## 📋 Las 5 Reglas de Selección

El sistema aplica estas reglas **en orden estricto**:

### Regla 1: Proceso Iterativo → GRADIENTE

**Si el problema menciona pasos repetidos**, usa el método del gradiente.

**Palabras clave:**
- iterar, iterativo, iteración
- descenso del gradiente
- actualizar, paso α
- tasa de aprendizaje
- entrenamiento
- varias iteraciones
- repetir el cálculo

**Ejemplo:**
```
Minimizar f(x,y) = x² + y² usando descenso del gradiente.
Punto inicial: x0 = [1, 1]
α = 0.1
100 iteraciones
```
→ **GRADIENTE**

---

### Regla 2: Restricciones No Lineales → KKT

**Si hay al menos UNA restricción no lineal**, usa condiciones KKT.

**No lineal = tiene:**
- Cuadrados: x², y²
- Productos de variables: xy
- Raíces: √x
- Divisiones: x/y
- Cualquier cosa que NO sea solo sumar/restar/multiplicar por números

**Ejemplo:**
```
Minimizar f(x,y) = x + y
sujeto a:
  x² + y² ≤ 10    ← NO LINEAL (tiene cuadrados)
  x ≥ 0
```
→ **KKT**

---

### Regla 3: Solo Igualdades → LAGRANGE

**Si todas las restricciones son igualdades**, usa multiplicadores de Lagrange.

**Requisitos:**
- Debe haber al menos UNA restricción
- TODAS deben ser igualdades (=)
- NINGUNA puede ser desigualdad (≤, ≥)

**Ejemplo:**
```
Minimizar f(x,y,z) = x² + y² + z²
sujeto a:
  x + y + z = 100    ← IGUALDAD
  2x - y = 10        ← IGUALDAD
```
→ **LAGRANGE**

---

### Regla 4: Función Cuadrática + Restricciones Lineales → QP

**Si la función objetivo es cuadrática Y todas las restricciones son lineales**, usa Programación Cuadrática.

**Requisitos:**
- Función objetivo tiene términos cuadráticos (x², y²)
- TODAS las restricciones son lineales (solo x, y, constantes)
- Debe haber AL MENOS una restricción

**Ejemplo:**
```
Minimizar f(x,y) = x² + y² + xy - 4x - 5y
sujeto a:
  x + y ≤ 10       ← LINEAL
  2x + y ≤ 15      ← LINEAL
  x ≥ 0            ← LINEAL
```
→ **QP**

---

### Regla 5: Sin Restricciones

**Si NO hay restricciones:**

#### 5a: Pide derivadas → DIFERENCIAL
Si menciona: puntos críticos, derivadas, máximos, mínimos, equilibrio

**Ejemplo:**
```
Encontrar los puntos críticos de f(x,y) = x³ - 3xy + y²
Calcular las derivadas parciales.
```
→ **DIFERENCIAL**

#### 5b: Solo optimización → GRADIENTE
Si solo dice minimizar/maximizar sin mencionar derivadas

**Ejemplo:**
```
Minimizar f(x,y) = x² + 2y² - 4x - 6y + 10
```
→ **GRADIENTE**

---

## 💻 Uso del Sistema

### Uso Básico

```python
from opti_app.core.message_parser import parse_and_determine_method

# Tu problema
problema = """
Minimizar f(x,y) = x² + y²
sujeto a:
  x² + y ≤ 10
  x ≥ 0
"""

# Analizar
resultado = parse_and_determine_method(problema)

# Ver resultados
print(f"Método: {resultado['method']}")
print(f"Razón: {resultado['method_explanation']['reason']}")
print(f"Parámetros: {resultado['solver_params']}")
```

### Salida Ejemplo

```json
{
  "method": "kkt",
  "method_explanation": {
    "reason": "El problema tiene al menos una restricción no lineal (con cuadrados, productos de variables, raíces, etc.)",
    "rule_applied": 2
  },
  "solver_params": {
    "method": "kkt",
    "objective": "x**2 + y**2",
    "variables": ["x", "y"],
    "constraints": [
      {
        "kind": "le",
        "expr": "(x**2 + y) - (10)"
      },
      {
        "kind": "ge",
        "expr": "(x) - (0)"
      }
    ],
    "tol": 1e-06
  },
  "raw_data": {
    "objective_expr": "x**2 + y**2",
    "variables": ["x", "y"],
    "constraints": [...]
  }
}
```

## 🔧 API Detallada

### `parse_and_determine_method(text: str)`

Función principal que analiza un problema completo.

**Parámetros:**
- `text`: Texto completo del problema

**Retorna:**
```python
{
    'method': str,  # 'gradient', 'kkt', 'lagrange', 'qp', 'differential'
    'method_explanation': {
        'reason': str,  # Por qué se eligió este método
        'rule_applied': int  # Qué regla se aplicó (1-5)
    },
    'solver_params': {
        'method': str,
        'objective': str,
        'variables': List[str],
        'constraints': List[Dict],  # Si aplica
        'x0': List[float],  # Si aplica
        'tol': float,  # Si aplica
        'max_iter': int,  # Si aplica
        ...
    },
    'raw_data': Dict  # Datos parseados originales
}
```

### Funciones del Módulo `method_detector`

```python
from opti_app.core import method_detector

# Determinar solo el método
method = method_detector.determine_method(
    text="...",
    objective_expr="x**2 + y**2",
    constraints=[...]
)
# Retorna: 'gradient', 'kkt', 'lagrange', 'qp', o 'differential'

# Obtener explicación detallada
explanation = method_detector.explain_method_choice(
    text="...",
    objective_expr="...",
    constraints=[...]
)
# Retorna: {'method': ..., 'reason': ..., 'rule_applied': ...}

# Extraer parámetros para solver
params = method_detector.extract_solver_parameters(
    method='kkt',
    objective_expr='x**2 + y**2',
    constraints=[...],
    variables=['x', 'y'],
    x0=[1.0, 1.0],
    tol=1e-6
)
```

## 📝 Parámetros Extraídos por Método

### GRADIENTE
```json
{
  "method": "gradient",
  "objective": "...",
  "variables": [...],
  "constraints": [...],
  "x0": [0.0, 0.0],
  "tol": 1e-6,
  "max_iter": 1000,
  "alpha": 0.01
}
```

### KKT
```json
{
  "method": "kkt",
  "objective": "...",
  "variables": [...],
  "constraints": [...],
  "x0": [...],  // opcional
  "tol": 1e-6
}
```

### LAGRANGE
```json
{
  "method": "lagrange",
  "objective": "...",
  "variables": [...],
  "constraints": [...],
  "x0": [...],  // opcional
  "tol": 1e-6
}
```

### QP (Programación Cuadrática)
```json
{
  "method": "qp",
  "objective": "...",
  "variables": [...],
  "constraints": [...],
  "x0": [0.0, 0.0],
  "tol": 1e-6
}
```

### DIFERENCIAL
```json
{
  "method": "differential",
  "objective": "...",
  "variables": [...],
  "x0": [...]  // opcional
}
```

## 🧪 Pruebas

Ejecuta el script de pruebas para ver ejemplos de cada regla:

```bash
cd opti_learn/opti_app/core
python test_method_detector.py
```

## 🎓 Ejemplos de Uso

### Ejemplo 1: Problema con iteraciones

```python
problema = """
Minimizar f(x,y) = x² + y²
usando descenso del gradiente con α = 0.01
Realizar 100 iteraciones desde x0 = [1, 1]
"""

resultado = parse_and_determine_method(problema)
# método: 'gradient'
# razón: "El problema menciona un proceso iterativo"
# regla: 1
```

### Ejemplo 2: Problema con restricción no lineal

```python
problema = """
Maximizar f(x,y) = 2x + 3y
sujeto a: xy ≤ 100
"""

resultado = parse_and_determine_method(problema)
# método: 'kkt'
# razón: "El problema tiene al menos una restricción no lineal"
# regla: 2
```

### Ejemplo 3: Solo igualdades

```python
problema = """
Minimizar f(x,y,z) = x² + y² + z²
sujeto a:
  x + y + z = 100
  x - y = 0
"""

resultado = parse_and_determine_method(problema)
# método: 'lagrange'
# razón: "El problema tiene solo restricciones de igualdad"
# regla: 3
```

## 🔍 Cómo Funciona Internamente

1. **Parsing**: Se extrae la función objetivo, restricciones, variables, etc.
2. **Detección de método**: Se aplican las 5 reglas en orden
3. **Extracción de parámetros**: Se construye el JSON según el método
4. **Validación**: Se verifican las expresiones con SymPy

### Flujo de Decisión

```
¿Menciona proceso iterativo? → GRADIENTE
     ↓ No
¿Hay restricciones no lineales? → KKT
     ↓ No
¿Solo hay igualdades? → LAGRANGE
     ↓ No
¿Función cuadrática + restricciones lineales? → QP
     ↓ No
¿Hay restricciones?
     ↓ No
¿Pide derivadas? → DIFERENCIAL
     ↓ No
GRADIENTE (por defecto)
```

## ⚙️ Integración con el Asistente IA

Los prompts en `ai_prompts.py` han sido actualizados para que la IA también use estas reglas:

```python
from opti_app.core.ai_prompts import PROMPT_METHOD_SELECTION

# Este prompt le indica a la IA cómo elegir el método
messages = [
    {"role": "system", "content": PROMPT_METHOD_SELECTION},
    {"role": "user", "content": problema_usuario}
]
```

## 📚 Referencias

- **message_parser.py**: Parsing de texto a estructura
- **method_detector.py**: Detección de método y extracción de parámetros
- **ai_prompts.py**: Prompts para el asistente IA
- **test_method_detector.py**: Suite de pruebas

## 🐛 Troubleshooting

### El método detectado no es el esperado

Verifica que el problema cumpla EXACTAMENTE los criterios de la regla:
- Para LAGRANGE: NO puede haber desigualdades
- Para QP: TODAS las restricciones deben ser lineales
- Para KKT: Debe haber al menos UNA restricción no lineal

### No se extraen los parámetros

Asegúrate de que el problema esté bien formateado:
```
Minimizar f(x,y) = ...
sujeto a:
  restricción1
  restricción2
```

### Variables no detectadas

Especifica explícitamente:
```
Variables: x, y, z
```

O usa nombres estándar (x, y, z, etc.)
