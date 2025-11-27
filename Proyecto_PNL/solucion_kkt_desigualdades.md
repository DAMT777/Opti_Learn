# 🎯 CONDICIONES KKT — MÉTODO ANALÍTICO

## PASO 1: PRESENTACIÓN DEL PROBLEMA

🎲 **Resolvamos este problema como un rompecabezas matemático paso a paso**

📊 **Función objetivo (Minimizar):**

$$f(x) = \left(x - 2\right)^{2} + \left(y - 2\right)^{2}$$

📌 **Variables de decisión:** $x, y$

⚙️ **Restricciones:**

  - Desigualdad 1: $x + y - 2 \leq 0$
  - Desigualdad 2: $- x \leq 0$
  - Desigualdad 3: $- y \leq 0$

---

## PASO 2: CONSTRUCCIÓN DE LA LAGRANGIANA

🧩 **Combinamos la función objetivo con las restricciones:**

$$\mathcal{L}(x, \lambda, \mu) = f(x) + \sum_{i} \lambda_i g_i(x) + \sum_{j} \mu_j h_j(x)$$

**Lagrangiana completa:**

$$\mathcal{L} = \lambda_{0} \left(x + y - 2\right) - \lambda_{1} x - \lambda_{2} y + \left(x - 2\right)^{2} + \left(y - 2\right)^{2}$$

Multiplicadores de desigualdad: $\lambda_{0}$, $\lambda_{1}$, $\lambda_{2}$

---

## PASO 3: GRADIENTE DE LA LAGRANGIANA

🔍 **Cada derivada es como un sensor que mide el balance de cada variable:**

$$\frac{\partial \mathcal{L}}{\partial x} = \lambda_{0} - \lambda_{1} + 2 x - 4 = 0$$

$$\frac{\partial \mathcal{L}}{\partial y} = \lambda_{0} - \lambda_{2} + 2 y - 4 = 0$$

---

## PASO 4: CONDICIONES KKT

✅ **Las cuatro condiciones que debe cumplir toda solución óptima:**

### 1️⃣ Estacionariedad

El gradiente de la Lagrangiana debe ser cero:

$$\nabla \mathcal{L} = 0$$

💡 *Es el punto donde objetivo y restricciones se compensan exactamente.*

### 2️⃣ Factibilidad Primal

El punto debe respetar las reglas originales:

$$g_i(x) \leq 0 \quad \forall i$$

💡 *La solución debe estar en la región factible.*

### 3️⃣ Factibilidad Dual

Los multiplicadores nunca son negativos:

$$\lambda_i \geq 0 \quad \forall i$$

💡 *Representan fuerzas de presión, no pueden ser negativas.*

### 4️⃣ Complementariedad

Solo actúan las restricciones que tocan el límite:

$$\lambda_i \cdot g_i(x) = 0 \quad \forall i$$

💡 *Si una restricción no está activa (g<0), su λ debe ser cero.*

---

## PASO 5: CLASIFICACIÓN DE CASOS

🔀 **Probamos 8 configuraciones posibles de restricciones activas/inactivas:**

**Caso 1:**
  - Inactivas: restricciones 1, 2, 3

**Caso 2:**
  - Activas: restricciones 3
  - Inactivas: restricciones 1, 2

**Caso 3:**
  - Activas: restricciones 2
  - Inactivas: restricciones 1, 3

**Caso 4:**
  - Activas: restricciones 2, 3
  - Inactivas: restricciones 1

**Caso 5:**
  - Activas: restricciones 1
  - Inactivas: restricciones 2, 3

**Caso 6:**
  - Activas: restricciones 1, 3
  - Inactivas: restricciones 2

**Caso 7:**
  - Activas: restricciones 1, 2
  - Inactivas: restricciones 3

**Caso 8:**
  - Activas: restricciones 1, 2, 3

---

## PASO 6: RESOLUCIÓN POR CASOS

🧮 **Resolvemos el sistema de ecuaciones para cada caso:**

✓ Casos válidos encontrados: **1**

---

## PASO 7: EVALUACIÓN DE CANDIDATOS

🏆 **Comparamos todos los candidatos válidos:**

| Candidato | Variables | Valor Objetivo | Estado |
|-----------|-----------|----------------|--------|
| 1 | x=1, y=1 | 2 | ✅ ÓPTIMO |

---

## PASO 8: SOLUCIÓN FINAL

🎉 **¡Esta es la mejor solución que respeta todas las reglas!**

### 📊 Variables óptimas:

- $x^* = 1$
- $y^* = 1$

### 🎯 Valor óptimo:

$$f(x^*) = 2$$

*Mínimo alcanzado.*

### ⚡ Restricciones activas:

- Restricción 1: $x + y - 2 = 0$
  - $\lambda_{0} = 2$

### 🔢 Multiplicadores de Lagrange:

- $\lambda_{0} = 2$ (activa)
- $\lambda_{1} = 0$ (inactiva)
- $\lambda_{2} = 0$ (inactiva)

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
