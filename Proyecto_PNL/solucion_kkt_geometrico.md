# 🎯 CONDICIONES KKT — MÉTODO ANALÍTICO

## PASO 1: PRESENTACIÓN DEL PROBLEMA

**Resolvamos este problema paso a paso usando condiciones KKT:**

**Función objetivo (Minimizar):**

$$f(x) = x^{2} + y^{2}$$

**Variables de decisión:** $x, y$

**Restricciones:**

  - Desigualdad 1: $- x - y + 2 \leq 0$
  - Desigualdad 2: $- x \leq 0$
  - Desigualdad 3: $- y \leq 0$

---

## PASO 2: CONSTRUCCIÓN DE LA LAGRANGIANA

**Combinamos la función objetivo con las restricciones:**

$$\mathcal{L}(x, \lambda, \mu) = f(x) + \sum_{i} \lambda_i g_i(x) + \sum_{j} \mu_j h_j(x)$$

**Lagrangiana completa:**

$$\mathcal{L} = \lambda_{0} \left(- x - y + 2\right) - \lambda_{1} x - \lambda_{2} y + x^{2} + y^{2}$$

Multiplicadores de desigualdad: $\lambda_{0}$, $\lambda_{1}$, $\lambda_{2}$

---

## PASO 3: GRADIENTE DE LA LAGRANGIANA

**Calculamos las derivadas parciales (condiciones de primer orden):**

$$\frac{\partial \mathcal{L}}{\partial x} = - \lambda_{0} - \lambda_{1} + 2 x = 0$$

$$\frac{\partial \mathcal{L}}{\partial y} = - \lambda_{0} - \lambda_{2} + 2 y = 0$$

---

## PASO 4: CONDICIONES KKT

**Las cuatro condiciones que debe cumplir toda solución óptima:**

### (1) Estacionariedad

El gradiente de la Lagrangiana debe ser cero:

$$\nabla \mathcal{L} = 0$$

*Es el punto donde objetivo y restricciones se compensan exactamente.*

### (2) Factibilidad Primal

El punto debe respetar las restricciones originales:

$$g_i(x) \leq 0 \quad \forall i$$

*La solución debe estar en la región factible.*

### (3) Factibilidad Dual

Los multiplicadores de desigualdades deben ser no negativos:

$$\lambda_i \geq 0 \quad \forall i$$

*Representan fuerzas de presión; no pueden ser negativas.*

### (4) Complementariedad

Solo actúan las restricciones que tocan el límite:

$$\lambda_i \cdot g_i(x) = 0 \quad \forall i$$

*Si una restricción no está activa ($g_i(x) < 0$), su multiplicador debe ser cero ($\lambda_i = 0$).*

---

## PASO 5: CLASIFICACIÓN DE CASOS

**Probamos 8 configuraciones posibles de restricciones activas/inactivas:**

Para cada restricción de desigualdad $g_i(x) \leq 0$, exploramos dos escenarios:

- **Restricción NO activa**: $\lambda_i = 0$ (no presiona la solución)
- **Restricción ACTIVA**: $g_i(x) = 0$ (toca el límite)

**Caso 1:**
  - Todas las restricciones inactivas ($\lambda_i = 0$ para todo $i$)
  - Buscamos solución en el interior de la región factible

**Caso 2:**
  - Activas: restricciones 3 → $g_i(x) = 0$
  - Inactivas: restricciones 1, 2 → $\lambda_i = 0$

**Caso 3:**
  - Activas: restricciones 2 → $g_i(x) = 0$
  - Inactivas: restricciones 1, 3 → $\lambda_i = 0$

**Caso 4:**
  - Activas: restricciones 2, 3 → $g_i(x) = 0$
  - Inactivas: restricciones 1 → $\lambda_i = 0$

**Caso 5:**
  - Activas: restricciones 1 → $g_i(x) = 0$
  - Inactivas: restricciones 2, 3 → $\lambda_i = 0$

**Caso 6:**
  - Activas: restricciones 1, 3 → $g_i(x) = 0$
  - Inactivas: restricciones 2 → $\lambda_i = 0$

*(Y 2 casos adicionales...)*

---

## PASO 6: RESOLUCIÓN POR CASOS

**Para cada caso, resolvemos el sistema de ecuaciones:**

1. Ecuaciones de estacionariedad: $\nabla \mathcal{L} = 0$
2. Restricciones de igualdad: $h_j(x) = 0$
3. Restricciones activas: $g_i(x) = 0$ (para las marcadas como activas)
4. Multiplicadores inactivos: $\lambda_i = 0$ (para las marcadas como inactivas)

**Ejemplo de resolución (primer caso válido):**

- Caso con restricciones activas [0]:
  - Resolver sistema combinado de estacionariedad y restricciones activas
  - Solución candidata: $x=1, y=1$
  - Verificar condiciones KKT... ✓

**Resultado del análisis:**

- Casos válidos (cumplen las 4 condiciones KKT): **1**
- Casos descartados (violan alguna condición): 7

---

## PASO 7: EVALUACIÓN DE CANDIDATOS

**Comparamos todos los candidatos válidos y seleccionamos el óptimo:**

| Candidato | Variables | Valor Objetivo | Estado |
|-----------|-----------|----------------|--------|
| 1 | x=1, y=1 | 2 | ✅ ÓPTIMO |

---

## PASO 8: SOLUCIÓN FINAL

**Solución óptima que cumple todas las condiciones KKT:**

### Variables óptimas

- $x^* = 1$
- $y^* = 1$

### Valor óptimo

$$f(x^*) = 2$$

*Mínimo alcanzado.*

### Restricciones activas

- Restricción 1: $- x - y + 2 = 0$
  - $\lambda_{0} = 2$

### Multiplicadores de Lagrange

- $\lambda_{0} = 2$ (activa)
- $\lambda_{1} = 0$ (inactiva)
- $\lambda_{2} = 0$ (inactiva)

### 📐 Análisis de Convexidad (Hessiana)

Para garantizar que el punto hallado es óptimo, analizamos la matriz Hessiana:

**Matriz Hessiana** $H = \nabla^2 f(x)$:

$$H = \left[\begin{matrix}2 & 0\\0 & 2\end{matrix}\right]$$

**Clasificación:** La Hessiana es *definida positiva*.

**Valores propios:** $\lambda = [2]$

**Interpretación:** La función objetivo es *convexa estricta*.

✓ Como la función es estrictamente convexa y se cumplen las condiciones KKT, 
el punto hallado es un **mínimo global único**.

---

## PASO 9: INTERPRETACIÓN PEDAGÓGICA

🌟 **Conclusión:**

Encontramos el punto donde la función objetivo y las restricciones conviven en **perfecto equilibrio**.

Las restricciones **activas** (que tocan el límite) son: 1

Estas restricciones están **presionando** la solución óptima. Sus multiplicadores λ indican:

- $\lambda_{0} = 2$: Sensibilidad del objetivo ante cambios en esta restricción

**¿Por qué es válida la solución?**

Cumple las **4 condiciones KKT**:
1. ✅ Gradiente en equilibrio (estacionariedad)
2. ✅ Respeta todas las restricciones (factibilidad primal)
3. ✅ Multiplicadores no negativos (factibilidad dual)
4. ✅ Complementariedad perfecta (solo actúan las restricciones presionadas)


---

### ✓ Procedimiento KKT completado exitosamente
