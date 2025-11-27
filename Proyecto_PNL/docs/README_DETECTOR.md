# 🎯 Sistema de Detección Automática de Métodos

## ✅ Implementación Completa

Se ha implementado un sistema completo que determina automáticamente qué método de optimización usar basándose en el enunciado del problema y extrae los parámetros necesarios en formato JSON.

## 📁 Archivos Creados/Modificados

### Nuevos Archivos

1. **`opti_app/core/method_detector.py`** (NUEVO)
   - Módulo principal con las 5 reglas de detección
   - Funciones para determinar método y extraer parámetros JSON
   - Explicaciones automáticas de por qué se eligió cada método

2. **`opti_app/core/test_method_detector.py`** (NUEVO)
   - Suite de pruebas con ejemplos de cada regla
   - Casos de uso prácticos
   - Script ejecutable para validación

3. **`docs/DETECTOR_METODOS.md`** (NUEVO)
   - Documentación técnica completa
   - API detallada
   - Explicación de las 5 reglas

4. **`docs/GUIA_RAPIDA_DETECTOR.md`** (NUEVO)
   - Guía visual con ejemplos
   - Tabla de decisión rápida
   - Casos especiales y debugging

### Archivos Modificados

1. **`opti_app/core/message_parser.py`**
   - Añadida función `parse_and_determine_method()`
   - Integración con el detector de métodos

2. **`opti_app/core/ai_prompts.py`**
   - Actualizado `PROMPT_MAESTRO` con las 5 reglas
   - Añadido `PROMPT_METHOD_SELECTION` con instrucciones detalladas

3. **`opti_app/ai/prompt_contextual.txt`**
   - Reemplazadas reglas antiguas con las 5 reglas estrictas
   - Actualizado formato JSON de salida
   - Incluida explicación del método elegido

## 🎯 Las 5 Reglas (Aplicar en Orden)

### Regla 1: Proceso Iterativo → GRADIENTE
Si menciona: iterar, actualizar, paso α, tasa de aprendizaje, entrenamiento, iteraciones

### Regla 2: Restricciones No Lineales → KKT
Si hay restricciones con: x², xy, √x, x/y, etc.

### Regla 3: Solo Igualdades → LAGRANGE
Si TODAS las restricciones son "=" y NO hay "≤" ni "≥"

### Regla 4: Cuadrática + Restricciones Lineales → QP
Si función tiene x² Y todas las restricciones son lineales Y hay al menos una

### Regla 5: Sin Restricciones
- Si pide derivadas/puntos críticos → DIFERENCIAL
- Si solo dice minimizar/maximizar → GRADIENTE

## 🚀 Uso Básico

```python
from opti_app.core.message_parser import parse_and_determine_method

problema = """
Minimizar f(x,y) = x² + y²
sujeto a:
  x² + y ≤ 10
  x ≥ 0
"""

resultado = parse_and_determine_method(problema)

# Salida:
{
  "method": "kkt",
  "method_explanation": {
    "reason": "El problema tiene restricciones no lineales (x², y²)",
    "rule_applied": 2
  },
  "solver_params": {
    "method": "kkt",
    "objective": "x**2 + y**2",
    "variables": ["x", "y"],
    "constraints": [
      {"kind": "le", "expr": "(x**2 + y) - (10)"},
      {"kind": "ge", "expr": "(x) - (0)"}
    ],
    "tol": 1e-6
  },
  "raw_data": {...}
}
```

## 📊 Tabla de Decisión Rápida

| Características del Problema | Método | Regla |
|------------------------------|--------|-------|
| Menciona "iteraciones", "paso α" | **GRADIENTE** | 1 |
| Restricciones con x², xy, √x | **KKT** | 2 |
| Solo restricciones con "=" | **LAGRANGE** | 3 |
| f(x) cuadrática + restricciones lineales | **QP** | 4 |
| Sin restricciones + "derivadas" | **DIFERENCIAL** | 5 |
| Sin restricciones + "minimizar" | **GRADIENTE** | 5 |

## 🧪 Ejecutar Pruebas

```bash
cd Proyecto_PNL/opti_learn/opti_app/core
python test_method_detector.py
```

Esto ejecutará ejemplos de cada una de las 5 reglas.

## 📚 Documentación

- **Documentación completa:** `docs/DETECTOR_METODOS.md`
- **Guía rápida:** `docs/GUIA_RAPIDA_DETECTOR.md`
- **Código fuente:** `opti_app/core/method_detector.py`

## 🎓 Ejemplos Prácticos

### Ejemplo 1: GRADIENTE (Regla 1)
```python
"Minimizar f(x,y) = x² + y² usando descenso del gradiente con α=0.01"
→ GRADIENTE (menciona proceso iterativo)
```

### Ejemplo 2: KKT (Regla 2)
```python
"Minimizar f(x,y) = x + y sujeto a x² + y² ≤ 10"
→ KKT (restricción no lineal: x² + y²)
```

### Ejemplo 3: LAGRANGE (Regla 3)
```python
"Minimizar f(x,y) = x² + y² sujeto a x + y = 10"
→ LAGRANGE (solo igualdades)
```

### Ejemplo 4: QP (Regla 4)
```python
"Minimizar f(x,y) = x² + y² sujeto a x + y ≤ 10, x ≥ 0"
→ QP (función cuadrática + restricciones lineales)
```

### Ejemplo 5: DIFERENCIAL (Regla 5)
```python
"Encontrar puntos críticos de f(x,y) = x³ - 3xy + y²"
→ DIFERENCIAL (sin restricciones, pide puntos críticos)
```

## 🔧 Funciones Principales

### `parse_and_determine_method(text)`
Función principal que analiza un problema y devuelve método + parámetros JSON.

### `method_detector.determine_method(text, objective_expr, constraints)`
Determina solo el método aplicando las 5 reglas.

### `method_detector.explain_method_choice(...)`
Devuelve el método con explicación de por qué se eligió.

### `method_detector.extract_solver_parameters(...)`
Extrae parámetros en formato JSON según el método.

### `method_detector.analyze_problem(text, parsed_data)`
Análisis completo: método + explicación + parámetros + datos raw.

## 💡 Características Clave

✅ **5 reglas claras y en orden** - Sin ambigüedades
✅ **Detección automática** - No requiere input manual del método
✅ **Explicación incluida** - Dice por qué eligió ese método
✅ **JSON listo para solver** - Parámetros extraídos automáticamente
✅ **Integrado con IA** - Prompts actualizados con las mismas reglas
✅ **Bien documentado** - Guías, ejemplos y referencias
✅ **Suite de pruebas** - Validación de cada regla

## 🎯 Integración con el Sistema

El sistema se integra perfectamente con:

1. **Parser existente** (`message_parser.py`)
2. **Prompts de IA** (`ai_prompts.py`, `prompt_contextual.txt`)
3. **Servicio Groq** (`groq_service.py`)
4. **Solvers** (pueden recibir el JSON directamente)

## 🔍 Debugging

Si el método detectado no es el esperado:

1. Verifica que se cumplan EXACTAMENTE los criterios de la regla
2. Recuerda que las reglas se aplican EN ORDEN
3. Para LAGRANGE: NO puede haber desigualdades
4. Para QP: TODAS las restricciones deben ser lineales
5. Para KKT: Debe haber AL MENOS una restricción no lineal

## 📝 Próximos Pasos

Para usar el sistema:

1. Importa la función: `from opti_app.core.message_parser import parse_and_determine_method`
2. Pasa el texto del problema
3. Obtén el método + JSON con parámetros
4. Usa el JSON para llamar al solver correspondiente

## 👥 Créditos

Sistema desarrollado para OptiLearn Web por:
- Diego Alejandro Machado Tovar
- Juan Carlos Barrera Guevara
- Jesus Gregorio Delgado

Universidad de los Llanos - Optimización No Lineal

---

**Fecha de implementación:** 26 de noviembre de 2025
**Versión:** 1.0.0
