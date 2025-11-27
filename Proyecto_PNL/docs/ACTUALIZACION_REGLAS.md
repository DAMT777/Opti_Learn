# 🔄 Actualización de Reglas - Detección por Estructura Matemática

## Cambios Realizados

Se han actualizado las reglas de detección de métodos para clasificar problemas **QP** basándose en su **estructura matemática** en lugar de palabras clave explícitas.

## ❌ Problema Anterior (Versión 2.0.0)

**Antes**, la Regla 4 requería mención explícita:
- Solo se clasificaba como QP si el texto decía "Programación Cuadrática", "QP", etc.
- Problemas con estructura QP válida (función cuadrática + restricciones lineales) se clasificaban como KKT

### Ejemplo del Problema:
```
Una empresa debe determinar la cantidad óptima de mezcla de ingredientes A y B
para minimizar el costo energético (que crece cuadráticamente: x² + y²)
sujeto a: x + y = 100, 20 ≤ x ≤ 70, y ≤ 60, 0.25x + 0.35y ≥ 28
```

- **Antes (v2.0.0):** Se detectaba como KKT ❌ (por Regla 5: tiene desigualdades)
- **Esperado:** Debe ser QP ✅ (función cuadrática + restricciones lineales)

## ✅ Solución Implementada (Versión 3.0.0)

Se modificó la **Regla 4** para detectar QP por **estructura matemática**:

### Reglas Actualizadas (en orden):

1. **Iterativo** → GRADIENTE
2. **Restricciones no lineales** → KKT
3. **Solo igualdades** → LAGRANGE
4. **Función CUADRÁTICA + Restricciones LINEALES** → QP
5. **Hay desigualdades (≤ o ≥)** → KKT
6. **Sin restricciones** → DIFERENCIAL/GRADIENTE

### Regla 4 Actualizada: QP por Estructura

**QP se detecta cuando:**
1. ✅ Función objetivo es **cuadrática** (grado 2: x², y², xy)
2. ✅ **TODAS** las restricciones son **lineales** (grado 1: ax + by ≤ c)
3. ✅ Hay **al menos una restricción**

**Ejemplos válidos de QP:**
- `minimizar x² + y² sujeto a x + y = 100, x ≥ 20`
- `minimizar 3x² + 2xy + y² sujeto a 2x + 3y ≤ 50, x ≥ 0`
- `minimizar costo_cuadrático(x,y) = x² + 4y² sujeto a x + y ≤ 100`

**NO es QP:**
- `x² + y² ≤ 10` → restricción no lineal → **KKT** (Regla 2)
- `x³ + y sujeto a x + y = 10` → función cúbica → **KKT**

## 📊 Comparación de Resultados

### Problema 1: Alimentos Balanceados (Caso Real)
```
Minimizar costo energético: x² + y²
sujeto a: x + y = 100, 20 ≤ x ≤ 70, y ≤ 60, 0.25x + 0.35y ≥ 28, x ≤ 65, y ≤ 65
```

| Antes (v2.0.0) | Después (v3.0.0) |
|----------------|------------------|
| **KKT** (Regla 5) ❌ | **QP** (Regla 4) ✅ |
| "Tiene desigualdades" | "Función cuadrática + restricciones lineales" |

### Problema 2: Logística con Restricciones No Lineales
```
Minimizar C(x,y) = x² + 4y²
sujeto a: x² + y ≤ 20, x ≥ 0, y ≥ 0
```

| Antes (v2.0.0) | Después (v3.0.0) |
|----------------|------------------|
| **KKT** (Regla 2) ✅ | **KKT** (Regla 2) ✅ |
| "Restricciones no lineales (x²)" | "Restricciones no lineales (x²)" |

### Problema 3: Solo Igualdades
```
Minimizar f(x,y) = x² + y²
sujeto a: x + y = 100
```

| Antes (v2.0.0) | Después (v3.0.0) |
|----------------|------------------|
| **LAGRANGE** (Regla 3) ✅ | **LAGRANGE** (Regla 3) ✅ |
| Sin cambios | Sin cambios |

### Problema 4: Menciona QP Explícitamente
```
Resolver el siguiente problema de Programación Cuadrática:
Minimizar f(x,y) = x² + y²
sujeto a: x + y ≤ 100
```

| Antes (v2.0.0) | Después (v3.0.0) |
|----------------|------------------|
| **QP** (Regla 4) ✅ | **QP** (Regla 4) ✅ |
| "Menciona QP" | "Función cuadrática + restricciones lineales" |

## 🔍 Detalles Técnicos

### Función Modificada

```python
def _is_explicit_qp(text: str, objective_expr: str, constraints: List[Dict[str, Any]]) -> bool:
    """
    REGLA 4: Determina si el problema es de Programación Cuadrática.
    
    QP se identifica cuando:
    1. La función objetivo es cuadrática (grado 2)
    2. TODAS las restricciones son lineales (grado 1)
    3. Hay al menos una restricción
    
    Esto es independiente de si el texto menciona "QP" o no.
    La estructura matemática define el método.
    """
    # Verificar estructura matemática: objetivo cuadrático + restricciones lineales
    return _is_qp_problem(objective_expr, constraints)
```

**Cambio principal:** Se eliminó la verificación de palabras clave (`qp_keywords`). Ahora solo se evalúa la estructura matemática.

### Funciones Auxiliares Existentes

```python
def _is_quadratic_objective(expr_str: str) -> bool:
    """Verifica que la función sea cuadrática (grado máximo = 2)"""
    # Usa sympy para determinar el grado del polinomio
    # Retorna True si el grado total es exactamente 2

def _has_only_linear_constraints(constraints: List[Dict[str, Any]]) -> bool:
    """Verifica que todas las restricciones sean lineales (grado 1)"""
    # Llama a _is_nonlinear_expression() para cada restricción
    # Retorna True si ninguna es no lineal

def _is_qp_problem(objective_expr: str, constraints: List[Dict[str, Any]]) -> bool:
    """Combina las verificaciones anteriores"""
    # 1. Hay restricciones
    # 2. Función objetivo cuadrática
    # 3. Todas restricciones lineales
```

### Flujo de Decisión Actualizado

```
Entrada: Problema de optimización
    │
    ├─ ¿Iterativo? → GRADIENTE (Regla 1)
    │
    ├─ ¿Restricciones no lineales? → KKT (Regla 2)
    │
    ├─ ¿Solo igualdades? → LAGRANGE (Regla 3)
    │
    ├─ ¿Función cuadrática + restricciones lineales? → QP (Regla 4) ⭐ NUEVO
    │
    ├─ ¿Hay desigualdades? → KKT (Regla 5)
    │
    └─ ¿Sin restricciones?
        ├─ Pide derivadas → DIFERENCIAL (Regla 6)
        └─ Solo optimizar → GRADIENTE (Regla 6)
```

**Cambio clave:** La Regla 4 ahora se ejecuta ANTES de la Regla 5, capturando problemas QP válidos antes de que se clasifiquen como KKT por tener desigualdades.

## 📝 Archivos Modificados

1. **`method_detector.py`**
   - Modificada función `_is_explicit_qp()` para eliminar verificación de palabras clave
   - Ahora detecta QP puramente por estructura matemática
   - Actualizada función `explain_method_choice()` con nuevo mensaje

2. **`ai_prompts.py`**
   - Actualizado `PROMPT_MAESTRO` con nueva Regla 4
   - Actualizado `PROMPT_METHOD_SELECTION` para reflejar detección por estructura

3. **`ACTUALIZACION_REGLAS.md`** (este archivo)
   - Documentado el cambio de versión 2.0.0 → 3.0.0
   - Actualizada lógica y ejemplos

## ✅ Tests de Validación

Para validar el cambio, prueba con:

```bash
cd opti_learn
python manage.py shell
```

```python
from opti_app.core import method_detector

# Test 1: Alimentos balanceados (debe ser QP)
text1 = """
Minimizar costo energético x² + y²
sujeto a: x + y = 100, 20 ≤ x ≤ 70, y ≤ 60
"""
result1 = method_detector.explain_method_choice(text1, "x**2 + y**2", [
    {'expr': 'x + y - 100', 'kind': 'eq'},
    {'expr': 'x - 20', 'kind': 'ge'},
    {'expr': '70 - x', 'kind': 'ge'},
])
print(f"Test 1: {result1['method']}")  # Debe ser 'qp'

# Test 2: Restricción no lineal (debe ser KKT)
result2 = method_detector.explain_method_choice("", "x**2 + y**2", [
    {'expr': 'x**2 + y - 10', 'kind': 'le'}
])
print(f"Test 2: {result2['method']}")  # Debe ser 'kkt'
```

**Resultados esperados:**

✅ Test 1: **qp** (función cuadrática + restricciones lineales)  
✅ Test 2: **kkt** (restricción no lineal x²)

## 🎯 Resumen de la Lógica (v3.0.0)

**Para que un problema sea QP:**
1. ✅ Función objetivo cuadrática (grado 2)
2. ✅ TODAS las restricciones lineales (grado 1)
3. ✅ Al menos una restricción

**NO importa:**
- ❌ Si menciona "QP" o "Programación Cuadrática" (opcional)
- ❌ Si tiene igualdades, desigualdades o ambas
- ❌ El contexto del problema (alimentos, logística, etc.)

**Solo importa la estructura matemática.**

## 📌 Ventajas del Nuevo Enfoque

1. **Más robusto:** No depende del vocabulario del usuario
2. **Matemáticamente correcto:** QP se define por estructura, no por palabras
3. **Cubre más casos:** Problemas reales que no mencionan "QP" pero son QP
4. **Elimina falsos KKT:** Problemas cuadráticos lineales ya no van a KKT incorrectamente

## ⚠️ Cambios de Comportamiento

### Problemas que ANTES iban a KKT y AHORA van a QP:

```
minimizar x² + y² sujeto a x + y ≤ 100, x ≥ 0
```
- v2.0.0: **KKT** (por Regla 5: tiene desigualdades)
- v3.0.0: **QP** (por Regla 4: cuadrática + lineal)

### Problemas que siguen siendo KKT:

```
minimizar x² + y² sujeto a x² + y ≤ 10
```
- v2.0.0: **KKT** (por Regla 2: restricción no lineal)
- v3.0.0: **KKT** (por Regla 2: restricción no lineal)

---

**Fecha:** 26 de noviembre de 2025  
**Versión:** 3.0.0  
**Status:** ✅ Implementado
