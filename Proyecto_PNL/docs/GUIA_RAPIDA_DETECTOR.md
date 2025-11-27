# 🎯 Guía Rápida: Detector de Métodos

## Cómo usar el sistema en 3 pasos

### 1️⃣ Importar la función

```python
from opti_app.core.message_parser import parse_and_determine_method
```

### 2️⃣ Analizar tu problema

```python
mi_problema = """
Minimizar f(x,y) = x² + y²
sujeto a:
  x² + y ≤ 10
  x ≥ 0
"""

resultado = parse_and_determine_method(mi_problema)
```

### 3️⃣ Ver el resultado

```python
print(f"Usar método: {resultado['method']}")
print(f"Porque: {resultado['method_explanation']['reason']}")

# Parámetros listos para el solver
params = resultado['solver_params']
```

---

## 📊 Tabla de Decisión Rápida

| ¿Qué tiene tu problema? | Método | Regla |
|------------------------|--------|-------|
| Menciona "iteraciones", "descenso", "paso α" | **GRADIENTE** | 1 |
| Restricciones con x², xy, √x | **KKT** | 2 |
| Solo restricciones con "=" | **LAGRANGE** | 3 |
| Función con x² + restricciones lineales | **QP** | 4 |
| Sin restricciones + "derivadas" | **DIFERENCIAL** | 5 |
| Sin restricciones + "minimizar" | **GRADIENTE** | 5 |

---

## 🎓 Ejemplos Prácticos

### Ejemplo 1: Entrenamiento iterativo → GRADIENTE

```python
problema = """
Entrenar un modelo minimizando f(w1, w2) = w1² + w2²
Usar descenso del gradiente con tasa de aprendizaje α = 0.01
100 iteraciones desde w0 = [1, 1]
"""

resultado = parse_and_determine_method(problema)

# Salida:
# método: 'gradient'
# razón: "El problema menciona un proceso iterativo (palabras como 'iterar', 'actualizar', 'paso α', etc.)"
# regla: 1
```

**JSON generado:**
```json
{
  "method": "gradient",
  "objective": "w1**2 + w2**2",
  "variables": ["w1", "w2"],
  "x0": [1.0, 1.0],
  "tol": 1e-06,
  "max_iter": 100,
  "alpha": 0.01
}
```

---

### Ejemplo 2: Restricción circular → KKT

```python
problema = """
Un ingeniero debe minimizar el costo C(x,y) = 50x + 80y
donde x, y son cantidades de materiales.
Restricción de capacidad: x² + y² ≤ 100
También debe cumplir: x + y ≥ 10
"""

resultado = parse_and_determine_method(problema)

# Salida:
# método: 'kkt'
# razón: "El problema tiene al menos una restricción no lineal (con cuadrados, productos de variables, raíces, etc.)"
# regla: 2
```

**Por qué KKT:** La restricción `x² + y² ≤ 100` es **no lineal** (tiene cuadrados).

---

### Ejemplo 3: Presupuesto exacto → LAGRANGE

```python
problema = """
Una empresa debe maximizar utilidad U(x,y) = 10x + 15y
El presupuesto debe gastarse EXACTAMENTE: 2x + 3y = 100
La producción debe ser EXACTAMENTE: x + y = 40
"""

resultado = parse_and_determine_method(problema)

# Salida:
# método: 'lagrange'
# razón: "El problema tiene solo restricciones de igualdad (sin desigualdades)"
# regla: 3
```

**Por qué Lagrange:** TODAS las restricciones son igualdades (=), no hay desigualdades (≤, ≥).

---

### Ejemplo 4: Minimizar distancia → QP

```python
problema = """
Minimizar la distancia al origen: f(x,y) = x² + y²
sujeto a:
  x + y ≤ 10
  2x + 3y ≤ 20
  x ≥ 0
  y ≥ 0
"""

resultado = parse_and_determine_method(problema)

# Salida:
# método: 'qp'
# razón: "La función objetivo es cuadrática y todas las restricciones son lineales"
# regla: 4
```

**Por qué QP:**
- Función objetivo tiene términos cuadráticos (x², y²) ✅
- TODAS las restricciones son lineales ✅
- Hay al menos una restricción ✅

---

### Ejemplo 5a: Análisis matemático → DIFERENCIAL

```python
problema = """
Analizar la función f(x,y) = x³ - 3xy + y²
Encontrar los puntos críticos calculando las derivadas parciales.
Clasificar cada punto usando el Hessiano.
"""

resultado = parse_and_determine_method(problema)

# Salida:
# método: 'differential'
# razón: "No hay restricciones y el problema pide calcular derivadas, puntos críticos o extremos"
# regla: 5
```

**Por qué Diferencial:**
- No hay restricciones ✅
- Menciona "puntos críticos", "derivadas" ✅

---

### Ejemplo 5b: Optimización simple → GRADIENTE

```python
problema = """
Minimizar f(x,y) = x² + 2y² - 4x - 6y + 10
"""

resultado = parse_and_determine_method(problema)

# Salida:
# método: 'gradient'
# razón: "No hay restricciones y se busca optimizar (minimizar/maximizar)"
# regla: 5
```

**Por qué Gradiente:**
- No hay restricciones ✅
- NO menciona derivadas explícitamente ✅
- Solo pide minimizar ✅

---

## 🔍 Casos Especiales

### ¿Qué pasa si hay restricciones lineales mixtas?

```python
problema = """
Minimizar f(x,y) = x + y
sujeto a:
  x + y ≤ 10
  x - y = 5
"""
# Resultado: GRADIENTE (por defecto para restricciones lineales mixtas)
```

### ¿Qué pasa si la función NO es cuadrática pero las restricciones son lineales?

```python
problema = """
Minimizar f(x,y) = x³ + y
sujeto a:
  x + y ≤ 10
"""
# Resultado: GRADIENTE (no cumple requisito de QP porque función no es cuadrática)
```

### ¿Qué pasa si tengo UNA igualdad y UNA desigualdad?

```python
problema = """
Minimizar f(x,y) = x² + y²
sujeto a:
  x + y = 10   ← igualdad
  x ≤ 5        ← desigualdad
"""
# Resultado: QP (no Lagrange porque hay desigualdades)
```

---

## 🎯 Checklist de Debugging

Si el método detectado no es el que esperas, verifica:

- [ ] **Para GRADIENTE (Regla 1):** ¿Menciona "iterar", "actualizar", "paso α"?
- [ ] **Para KKT (Regla 2):** ¿Hay al menos UNA restricción con x², xy, √x, etc.?
- [ ] **Para LAGRANGE (Regla 3):** ¿TODAS las restricciones son "=" y NINGUNA es "≤" o "≥"?
- [ ] **Para QP (Regla 4):** ¿La función tiene x² Y todas las restricciones son lineales?
- [ ] **Para DIFERENCIAL (Regla 5):** ¿NO hay restricciones Y menciona "derivadas"?

---

## 💡 Tips Pro

### Especifica variables explícitamente

```python
# ✅ BIEN
problema = """
Variables: x, y, z
Minimizar f(x,y,z) = ...
"""

# ❌ Puede confundirse
problema = """
Minimizar cost = ...  # ¿cost es la variable?
```

### Usa punto inicial cuando sea relevante

```python
problema = """
Minimizar f(x,y) = x² + y²
x0 = [1.0, 1.0]  # Punto inicial
"""
```

### Especifica tolerancia para problemas numéricos

```python
problema = """
Minimizar f(x,y) = ...
tol = 1e-8  # Tolerancia deseada
"""
```

---

## 🚀 Integración con tu código

### En una vista Django

```python
from opti_app.core.message_parser import parse_and_determine_method

def resolver_problema(request):
    problema_usuario = request.POST.get('problema')
    
    # Analizar y determinar método
    analisis = parse_and_determine_method(problema_usuario)
    
    if not analisis:
        return JsonResponse({'error': 'No se pudo parsear el problema'})
    
    # Usar el método detectado
    metodo = analisis['method']
    params = analisis['solver_params']
    
    # Llamar al solver correspondiente
    if metodo == 'gradient':
        resultado = resolver_gradiente(**params)
    elif metodo == 'kkt':
        resultado = resolver_kkt(**params)
    # ... etc.
    
    return JsonResponse({
        'metodo': metodo,
        'razon': analisis['method_explanation']['reason'],
        'resultado': resultado
    })
```

### Con el asistente IA

```python
from opti_app.core import groq_service
from opti_app.core.ai_prompts import PROMPT_METHOD_SELECTION

# El asistente también usa las mismas reglas
messages = [
    {"role": "system", "content": PROMPT_METHOD_SELECTION},
    {"role": "user", "content": problema_usuario}
]

respuesta_ia = groq_service.chat_completion(messages)
```

---

## 📚 Más Recursos

- **Documentación completa:** `docs/DETECTOR_METODOS.md`
- **Código fuente:** `opti_app/core/method_detector.py`
- **Pruebas:** `opti_app/core/test_method_detector.py`
- **Parser:** `opti_app/core/message_parser.py`
