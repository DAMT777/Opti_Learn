# 🎯 GUÍA DE USO - SOLVER KKT

## ✅ Estado: Completamente Funcional

El solver de **Condiciones KKT** ya está integrado y listo para usar en OptiLearn.

---

## 🚀 Cómo Usar en la Aplicación Web

### 1. Iniciar el Servidor

```bash
cd opti_learn
python manage.py runserver 8001
```

### 2. Abrir el Navegador

```
http://127.0.0.1:8001/
```

### 3. Enviar un Problema

El sistema **detectará automáticamente** si debe usar KKT. Solo escribe el problema en lenguaje natural.

---

## 📝 Ejemplos de Problemas

### Ejemplo 1: Problema con Igualdad

```
Minimizar f(x,y) = x² + y²
Sujeto a: x + y = 1
```

**Resultado esperado:**
- Método detectado: KKT
- Solución: x=0.5, y=0.5
- Valor óptimo: f=0.5
- Explicación completa en 9 pasos

---

### Ejemplo 2: Problema con Desigualdades

```
Minimizar la distancia f(x,y) = (x-3)² + (y-3)²
Sujeto a:
  x + y ≤ 4
  x ≥ 0
  y ≥ 0
```

**Resultado esperado:**
- Método detectado: KKT
- Solución: x=2, y=2
- Restricción activa: x+y=4
- Multiplicador: λ₀ indica presión de restricción

---

### Ejemplo 3: Maximización de Beneficio

```
Maximizar el beneficio B(x,y) = 60x + 50y
donde x = unidades del producto A
      y = unidades del producto B

Restricciones:
  3x + 2y ≤ 120  (horas de trabajo disponibles)
  x + 2y ≤ 80    (materiales disponibles)
  x ≥ 0, y ≥ 0   (no negatividad)
```

**Resultado esperado:**
- Método detectado: KKT
- Solución: x=20, y=30
- Beneficio máximo: $2700
- Restricciones activas: ambas (horas y materiales)
- Interpretación económica completa

---

### Ejemplo 4: Cartera de Inversiones

```
Minimizar el riesgo R = 0.04A² + 0.02B² + 0.01AB
donde A = inversión en acciones
      B = inversión en bonos

Restricciones:
  A + B = 100     (presupuesto total)
  A ≥ 20          (mínimo en acciones)
  B ≥ 50          (mínimo en bonos)
```

**Resultado esperado:**
- Método detectado: KKT
- Solución: A=30, B=70
- Riesgo mínimo: 155
- Distribución óptima del portafolio

---

## 🎓 ¿Qué Verás en la Explicación?

El solver KKT genera una explicación completa en **9 pasos pedagógicos**:

### 🟦 Paso 1: Presentación del Problema
```markdown
📊 **Función objetivo (Minimizar):**
$$f(x) = x^{2} + y^{2}$$

📌 **Variables de decisión:** $x, y$

⚙️ **Restricciones:**
  - Igualdad 1: $x + y - 1 = 0$
```

### 🟩 Paso 2: Construcción de la Lagrangiana
```markdown
**Lagrangiana completa:**
$$\mathcal{L} = \mu_{0} (x + y - 1) + x^{2} + y^{2}$$

Multiplicadores de igualdad: $\mu_{0}$
```

### 🟧 Paso 3: Gradiente de la Lagrangiana
```markdown
🔍 **Cada derivada es como un sensor que mide el balance:**

$$\frac{\partial \mathcal{L}}{\partial x} = \mu_{0} + 2x = 0$$
$$\frac{\partial \mathcal{L}}{\partial y} = \mu_{0} + 2y = 0$$
```

### 🟥 Paso 4: Condiciones KKT

Las 4 condiciones explicadas en detalle:
1. ✅ **Estacionariedad** - Gradiente en cero
2. ✅ **Factibilidad Primal** - Respeta restricciones
3. ✅ **Factibilidad Dual** - λ ≥ 0
4. ✅ **Complementariedad** - λ·g(x) = 0

### 🟪 Paso 5: Clasificación de Casos
```markdown
🔀 **Probamos N configuraciones posibles:**

**Caso 1:** Restricción 1 activa, Restricción 2 inactiva
**Caso 2:** Ambas activas
...
```

### 🟫 Paso 6: Resolución por Casos
```markdown
🧮 **Resolvemos el sistema de ecuaciones para cada caso**
✓ Casos válidos encontrados: **1**
```

### 🟨 Paso 7: Evaluación de Candidatos
```markdown
| Candidato | Variables | Valor Objetivo | Estado |
|-----------|-----------|----------------|--------|
| 1 | x=1, y=1 | 2.0 | ✅ ÓPTIMO |
```

### 🟦 Paso 8: Solución Final
```markdown
### 📊 Variables óptimas:
- $x^* = 1$
- $y^* = 1$

### 🎯 Valor óptimo:
$$f(x^*) = 2$$

### ⚡ Restricciones activas:
- Restricción 1: $x + y - 2 = 0$ con $\lambda_{0} = 2$
```

### 🟣 Paso 9: Interpretación Pedagógica
```markdown
🌟 **Conclusión:**
Encontramos el punto donde la función objetivo y las 
restricciones conviven en **perfecto equilibrio**.

**¿Por qué es válida la solución?**
Cumple las **4 condiciones KKT**:
1. ✅ Gradiente en equilibrio
2. ✅ Respeta todas las restricciones
3. ✅ Multiplicadores no negativos
4. ✅ Complementariedad perfecta
```

---

## 🔬 Casos de Uso Típicos

### ✅ Cuándo el sistema usa KKT automáticamente:

1. **Problemas con restricciones mixtas** (igualdades + desigualdades)
2. **Funciones no lineales** con restricciones
3. **Optimización con cotas** (límites superiores/inferiores)
4. **Problemas económicos** (producción, asignación de recursos)
5. **Problemas de ingeniería** (diseño óptimo con limitaciones)

### ❌ Cuándo NO se usa KKT:

- Problemas sin restricciones → usa **Gradiente**
- Problemas cuadráticos puros → usa **QP**
- Problemas lineales simples → podría usar otros métodos

---

## 🧪 Verificación Manual (desde terminal)

Si quieres probar el solver directamente sin el servidor web:

```bash
cd c:\Users\diego\OneDrive\Documentos\Programacion_No_Lineal\Proyecto_PNL

# Ejecutar tests
python test_kkt_final.py
```

Esto generará archivos `.md` con las soluciones completas:
- `solucion_kkt_cartera.md`
- `solucion_kkt_geometrico.md`
- `solucion_kkt_negocio.md`

---

## 📊 Comparación con Otros Solvers

| Característica | Gradiente | Lagrange | **KKT** | QP |
|----------------|-----------|----------|---------|-----|
| Restricciones igualdad | ❌ | ✅ | ✅ | ✅ |
| Restricciones desigualdad | ❌ | ❌ | ✅ | ✅ |
| Funciones no lineales | ✅ | ✅ | ✅ | Solo cuadráticas |
| Análisis de casos | ❌ | ❌ | ✅ | ❌ |
| Multiplicadores λ/μ | ❌ | ✅ | ✅ | ✅ |
| Restricciones activas | ❌ | ❌ | ✅ | ✅ |
| Método | Numérico | Simbólico | **Simbólico** | Numérico |
| Explicación pedagógica | 7 pasos | 5 pasos | **9 pasos** | 7 pasos |

---

## 💡 Tips para Mejores Resultados

### ✅ Escribir problemas claramente:

**Bueno:**
```
Minimizar f(x,y) = x² + y²
Sujeto a: x + y = 1
          x ≥ 0
```

**Evitar:**
```
minimiza cuadrados con suma 1
```

### ✅ Especificar restricciones explícitamente:

**Bueno:**
```
Maximizar B = 50x + 40y
Restricciones:
  2x + y ≤ 100
  x + 2y ≤ 80
  x ≥ 0
  y ≥ 0
```

### ✅ Usar nombres de variables descriptivos:

**Bueno:**
```
Variables: A (inversión en acciones), B (inversión en bonos)
```

---

## 🎯 Próximos Pasos

1. **Prueba el solver** con diferentes tipos de problemas
2. **Revisa las explicaciones** paso a paso para aprender KKT
3. **Compara resultados** con soluciones conocidas
4. **Experimenta** con restricciones activas/inactivas

---

## 📚 Recursos Adicionales

- **Documentación técnica**: `RESUMEN_SOLVER_KKT.md`
- **Archivos de ejemplo**: `solucion_kkt_*.md`
- **Código fuente**: `opti_learn/opti_app/core/solver_kkt.py`
- **Tests**: `test_kkt_final.py`, `test_kkt_solver.py`

---

## ✅ Checklist de Verificación

Antes de usar el solver, verifica:

- [ ] Servidor Django corriendo en puerto 8001
- [ ] Navegador abierto en `http://127.0.0.1:8001/`
- [ ] Problema escrito claramente
- [ ] Variables y restricciones identificadas

Después de obtener resultados:

- [ ] Revisar los 9 pasos de la explicación
- [ ] Verificar valores óptimos
- [ ] Entender restricciones activas
- [ ] Interpretar multiplicadores λ y μ

---

**¡El solver KKT está listo para enseñar optimización de forma pedagógica y lúdica!** 🎓

---

*Última actualización: 27 de noviembre de 2025*
