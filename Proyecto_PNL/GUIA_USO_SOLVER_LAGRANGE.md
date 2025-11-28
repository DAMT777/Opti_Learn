# 🎯 GUÍA DE USO: SOLVER DE MULTIPLICADORES DE LAGRANGE

## 📘 ¿Qué es el Método de Lagrange?

El método de **Multiplicadores de Lagrange** resuelve problemas de optimización con restricciones de igualdad:

```
Minimizar (o maximizar): f(x, y, ...)
Sujeto a: g₁(x, y, ...) = 0
          g₂(x, y, ...) = 0
          ...
```

### 🔑 Idea Central

Transformar el problema restringido en uno sin restricciones usando la **Lagrangiana**:

```
L(x, y, λ) = f(x, y) - λ · g(x, y)
```

El punto óptimo (x*, y*, λ*) satisface: **∇L = 0**

---

## 🚀 Inicio Rápido

### 1. Importar el Solver

```python
from opti_app.core.solver_lagrange import solve_with_lagrange_method
```

### 2. Definir el Problema

```python
# Función objetivo
objective = "x**2 + y**2"

# Variables
variables = ["x", "y"]

# Restricciones de igualdad (deben ser = 0)
constraints = ["x + y - 1"]  # Representa: x + y = 1
```

### 3. Resolver

```python
result = solve_with_lagrange_method(
    objective_expression=objective,
    variable_names=variables,
    equality_constraints=constraints
)
```

### 4. Obtener Resultados

```python
print(result['status'])      # 'success' o 'error'
print(result['solution'])    # {'x': 0.5, 'y': 0.5, 'lambda': 1}
print(result['explanation']) # Markdown completo con 9 pasos
```

---

## 📋 Ejemplos Completos

### Ejemplo 1: Problema Básico

**Enunciado:**
> Minimizar f(x, y) = x² + y²  
> Sujeto a: x + y = 1

```python
result = solve_with_lagrange_method(
    objective_expression="x**2 + y**2",
    variable_names=["x", "y"],
    equality_constraints=["x + y - 1"]
)

# Solución: x* = 0.5, y* = 0.5, f* = 0.5
```

### Ejemplo 2: Problema Geométrico

**Enunciado:**
> Encontrar el punto de la recta x + 2y = 4 más cercano a (1, 2)

```python
result = solve_with_lagrange_method(
    objective_expression="(x - 1)**2 + (y - 2)**2",
    variable_names=["x", "y"],
    equality_constraints=["x + 2*y - 4"]
)

# Solución: x* = 0.8, y* = 1.6, distancia* = 0.2
```

### Ejemplo 3: Problema con 3 Variables

**Enunciado:**
> Minimizar f(x, y, z) = x² + y² + z²  
> Sujeto a: x + y + z = 3

```python
result = solve_with_lagrange_method(
    objective_expression="x**2 + y**2 + z**2",
    variable_names=["x", "y", "z"],
    equality_constraints=["x + y + z - 3"]
)

# Solución: x* = 1, y* = 1, z* = 1, f* = 3
```

### Ejemplo 4: Múltiples Restricciones

**Enunciado:**
> Minimizar f(x, y) = x² + y²  
> Sujeto a: x + y = 2  
>           x - y = 0

```python
result = solve_with_lagrange_method(
    objective_expression="x**2 + y**2",
    variable_names=["x", "y"],
    equality_constraints=[
        "x + y - 2",
        "x - y"
    ]
)

# Solución: x* = 1, y* = 1, f* = 2
```

---

## 🎓 Los 9 Pasos Pedagógicos

El solver genera una explicación completa siguiendo estos pasos:

### PASO 1: Presentación del Problema
- Muestra f(x, y)
- Lista restricciones gᵢ(x, y) = 0
- Identifica variables

### PASO 2: Construcción de la Lagrangiana
- Formula: L(x, y, λ) = f(x, y) - Σλᵢgᵢ(x, y)
- Explica el rol de λ

### PASO 3: Derivadas Parciales
- Calcula: ∂L/∂x, ∂L/∂y, ∂L/∂λ
- Iguala todo a cero

### PASO 4: Sistema de Ecuaciones
- Presenta el sistema completo
- Cuenta ecuaciones vs incógnitas

### PASO 5: Resolución del Sistema
- Resuelve simbólicamente
- Muestra x*, y*, λ*

### PASO 6: Análisis del Hessiano
- Calcula matriz H_f
- Clasifica: mínimo/máximo/silla

### PASO 7: Valor Óptimo
- Evalúa f(x*, y*)
- Confirma naturaleza del punto

### PASO 8: Interpretación Pedagógica
- Explica significado de λ
- Valida factibilidad

### PASO 9: Resumen Final
- Checklist de validación
- Tabla con resultados

---

## 📊 Estructura del Resultado

```python
result = {
    'method': 'lagrange',
    'status': 'success',  # o 'error'
    'explanation': "# 🎯 MÉTODO DE MULTIPLICADORES...",  # Markdown
    'solution': {
        'x': 0.5,
        'y': 0.5,
        'lambda': 1.0
    },
    'steps': {
        'step1': {...},  # Datos de presentación
        'step2': {...},  # Lagrangiana
        'step3': {...},  # Gradientes
        'step4': {...},  # Sistema
        'step5': {...},  # Soluciones
        'step6': {...},  # Hessiano
        'step7': {...}   # Valor óptimo
    }
}
```

---

## 🔧 Formato de Restricciones

### ✅ Correcto

Las restricciones deben estar en forma: **g(x, y) = 0**

```python
# Si la restricción es: x + y = 1
# Escribir como: x + y - 1 = 0
constraints = ["x + y - 1"]

# Si la restricción es: 2x + 3y = 6
# Escribir como: 2x + 3y - 6 = 0
constraints = ["2*x + 3*y - 6"]
```

### ❌ Incorrecto

```python
# NO usar igualdades explícitas
constraints = ["x + y == 1"]  # ❌

# NO usar desigualdades (usar KKT en su lugar)
constraints = ["x + y <= 1"]  # ❌
```

---

## 💡 Interpretación de Resultados

### Multiplicador λ

El valor de λ* indica:

- **λ grande**: La restricción está "apretando" mucho el óptimo
- **λ pequeño**: La restricción tiene poco impacto
- **λ negativo**: Relajar la restricción empeoraría el objetivo

**Interpretación matemática:**

```
λ* ≈ ∂f*/∂c
```

Es decir, cuánto cambia el valor óptimo si modificamos la restricción.

### Naturaleza del Punto

El Hessiano H_f determina:

| Eigenvalues | Clasificación | Naturaleza |
|-------------|---------------|------------|
| Todos > 0 | Def. positiva | **Mínimo local** |
| Todos < 0 | Def. negativa | **Máximo local** |
| Mixtos | Indefinida | **Punto silla** |

---

## 🎯 Casos de Uso Recomendados

### ✅ Ideal para:

- **Problemas de distancia mínima** (punto a curva/plano)
- **Optimización con presupuestos** (restricción lineal)
- **Geometría analítica** (elipses, parábolas con restricciones)
- **Problemas de 2-4 variables** con restricciones simples

### ⚠️ No usar para:

- **Desigualdades** (usar `solver_kkt.py` en su lugar)
- **Problemas cuadráticos grandes** (usar `solver_qp_kkt.py`)
- **Restricciones muy no lineales** (puede no encontrar solución simbólica)

---

## 🧪 Testing

### Ejecutar Tests

```bash
python test_lagrange_solver.py
```

**Salida esperada:**
```
============================================================
TEST 1: Problema básico de Lagrange
============================================================

Status: success
Explicación guardada en: solucion_lagrange_basico.md
...
```

### Archivos Generados

- `solucion_lagrange_basico.md`
- `solucion_lagrange_nolineal.md`
- `solucion_lagrange_geometrico.md`

---

## 🌐 Uso en la Aplicación Web

### Flujo Completo

1. **Usuario envía problema** vía WebSocket
2. **Detector de métodos** identifica 'lagrange'
3. **Consumer** invoca `solve_lagrange_payload()`
4. **Solver** ejecuta 9 pasos y genera Markdown
5. **Cliente** renderiza con MathJax

### Ejemplo de Mensaje

```json
{
  "action": "solve",
  "payload": {
    "problema": {
      "objective_expr": "x**2 + y**2",
      "constraints": [
        {"expr": "x + y - 1", "kind": "eq"}
      ]
    },
    "meta": {
      "variables": ["x", "y"]
    }
  }
}
```

---

## 📚 Referencias Matemáticas

### Condiciones de Optimalidad

**Condiciones de primer orden (necesarias):**
```
∇_x L(x*, λ*) = 0
∇_λ L(x*, λ*) = 0
```

**Condiciones de segundo orden (suficientes):**
```
H_f definida positiva → mínimo local
H_f definida negativa → máximo local
```

### Teorema de Lagrange

> Si x* es solución del problema restringido y la restricción es regular  
> en x*, entonces existe λ* tal que (x*, λ*) satisface ∇L = 0.

---

## 🆘 Solución de Problemas

### Error: "No se encontró solución simbólica"

**Causa:** SymPy no puede resolver el sistema de ecuaciones.

**Solución:**
- Simplificar la función objetivo
- Verificar que las restricciones sean bien condicionadas
- Considerar usar método numérico (KKT o QP)

### Error: "Hessiano no evaluable numéricamente"

**Causa:** La solución contiene símbolos no resueltos.

**Solución:**
- Revisar si el sistema tiene solución única
- Verificar condiciones de regularidad

---

## 📞 Soporte

Para problemas o dudas:

1. Revisar ejemplos en `test_lagrange_solver.py`
2. Consultar documentación en `RESUMEN_SOLVER_LAGRANGE.md`
3. Verificar formato de restricciones (deben ser = 0)

---

**Fecha de creación:** 27 de noviembre de 2025  
**Versión:** 1.0  
**Autor:** OptiLearn Development Team
