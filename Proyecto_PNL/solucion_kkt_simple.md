# 🎯 CONDICIONES KKT — MÉTODO ANALÍTICO

## PASO 1: PRESENTACIÓN DEL PROBLEMA

🎲 **Resolvamos este problema como un rompecabezas matemático paso a paso**

📊 **Función objetivo (Minimizar):**

$$f(x) = x^{2} + y^{2}$$

📌 **Variables de decisión:** $x, y$

⚙️ **Restricciones:**

  - Igualdad 1: $x + y - 1 = 0$

---

## PASO 2: CONSTRUCCIÓN DE LA LAGRANGIANA

🧩 **Combinamos la función objetivo con las restricciones:**

$$\mathcal{L}(x, \lambda, \mu) = f(x) + \sum_{i} \lambda_i g_i(x) + \sum_{j} \mu_j h_j(x)$$

**Lagrangiana completa:**

$$\mathcal{L} = \mu_{0} \left(x + y - 1\right) + x^{2} + y^{2}$$

Multiplicadores de igualdad: $\mu_{0}$

---

## PASO 3: GRADIENTE DE LA LAGRANGIANA

🔍 **Cada derivada es como un sensor que mide el balance de cada variable:**

$$\frac{\partial \mathcal{L}}{\partial x} = \mu_{0} + 2 x = 0$$

$$\frac{\partial \mathcal{L}}{\partial y} = \mu_{0} + 2 y = 0$$

---

## PASO 4: CONDICIONES KKT

✅ **Las cuatro condiciones que debe cumplir toda solución óptima:**

### 1️⃣ Estacionariedad

El gradiente de la Lagrangiana debe ser cero:

$$\nabla \mathcal{L} = 0$$

💡 *Es el punto donde objetivo y restricciones se compensan exactamente.*

### 2️⃣ Factibilidad Primal

El punto debe respetar las reglas originales:

$$h_j(x) = 0 \quad \forall j$$

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

🔀 **Probamos 1 configuraciones posibles de restricciones activas/inactivas:**

**Caso 1:**

---

## PASO 6: RESOLUCIÓN POR CASOS

🧮 **Resolvemos el sistema de ecuaciones para cada caso:**

✓ Casos válidos encontrados: **1**

---

## PASO 7: EVALUACIÓN DE CANDIDATOS

🏆 **Comparamos todos los candidatos válidos:**

| Candidato | Variables | Valor Objetivo | Estado |
|-----------|-----------|----------------|--------|
| 1 | x=1/2, y=1/2 | 1/2 | ✅ ÓPTIMO |

---

## PASO 8: SOLUCIÓN FINAL

🎉 **¡Esta es la mejor solución que respeta todas las reglas!**

### 📊 Variables óptimas:

- $x^* = 1/2$
- $y^* = 1/2$

### 🎯 Valor óptimo:

$$f(x^*) = 1/2$$

*Mínimo alcanzado.*

### 🔢 Multiplicadores de Lagrange:

- $\mu_{0} = -1$

---

## PASO 9: INTERPRETACIÓN PEDAGÓGICA

🌟 **Conclusión:**

Encontramos el punto donde la función objetivo y las restricciones conviven en **perfecto equilibrio**.

✨ No hay restricciones activas: la solución está en el **interior** de la región factible.

**¿Por qué es válida la solución?**

Cumple las **4 condiciones KKT**:
1. ✅ Gradiente en equilibrio (estacionariedad)
2. ✅ Respeta todas las restricciones (factibilidad primal)
3. ✅ Multiplicadores no negativos (factibilidad dual)
4. ✅ Complementariedad perfecta (solo actúan las restricciones presionadas)


---

### ✓ Procedimiento KKT completado exitosamente
