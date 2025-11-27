
# 📐 PROGRAMACIÓN CUADRÁTICA — MÉTODO KKT (SLSQP)


## PASO 1: DEFINICION DEL PROBLEMA

📊 **Función objetivo:**

$$0.04*A**2 + 0.02*B**2 + 0.03*F**2 + 0.01*A*B + 0.015*A*F + 0.005*B*F$$

📌 **Variables de decisión:** $A, B, F$

⚙️ **Restricciones:**

  - $A + B + F - 100 = 0.0$
  - $0.10*A + 0.05*B + 0.08*F - 7.5 \geq 0.0$
  - $A - 20 \geq 0.0$
  - $B - 50 \leq 0.0$
  - $F - 10 \geq 0.0$
  - $F - 40 \leq 0.0$
  - $B + F - 45 \geq 0.0$


## PASO 2: MATRICES

🔢 **Vector $C$ (coeficientes lineales):**

$$C = \begin{bmatrix} 0, 0, 0 \end{bmatrix}$$

🔢 **Matriz $D$ (Hessiana - coeficientes cuadráticos):**

  $$D = \begin{bmatrix} 0.08 & 0.01 & 0.015 \\\\ 0.01 & 0.04 & 0.005 \\\\ 0.015 & 0.005 & 0.06 \end{bmatrix}$$

**Matriz $A_{eq}$ (restricciones igualdad):**
  $$A_{eq} = \begin{bmatrix} 1 & 1 & 1 \end{bmatrix}$$

**Vector $b_{eq}$:**
  $$b_{eq} = \begin{bmatrix} 100 \end{bmatrix}$$

**Matriz $A_{ineq}$ (restricciones desigualdad):**
  $$A_{ineq} = \begin{bmatrix} 1/10 & 0.05 & 0.08 \\\\ 1 & 0 & 0 \\\\ 0 & -1 & 0 \\\\ 0 & 0 & 1 \\\\ 0 & 0 & -1 \\\\ 0 & 1 & 1 \end{bmatrix}$$

**Vector $b_{ineq}$:**
  $$b_{ineq} = \begin{bmatrix} 15/2, 20, -50, 10, -40, 45 \end{bmatrix}$$


## PASO 3: CONVEXIDAD

**Eigenvalores de $D$:**
  - $\lambda_{1} = 0.090501$ (\geq 0)
  - $\lambda_{2} = 0.051978$ (\geq 0)
  - $\lambda_{3} = 0.03752$ (\geq 0)

✔ **El problema es CONVEXO**
  El método garantiza encontrar el óptimo global


## PASO 4: SISTEMA KKT

**Condiciones KKT:**

1. **Estacionariedad**: $\nabla f(x) + A^T\lambda + \mu = 0$
2. **Factibilidad primal**: $Ax = b$, $Gx \leq h$, $x \geq 0$
3. **Factibilidad dual**: $\lambda$ libre, $\mu \geq 0$
4. **Complementariedad**: $\mu_i \cdot x_i = 0$ $\forall i$

**Variables del sistema:**
  - $x$ (decisión): 3
  - $\lambda$ (igualdades): 1
  - $\lambda$ (desigualdades): 6
  - $\mu$ (no negatividad): 3

⚠️ **Nota metodológica:**
Este problema se resolverá mediante **SLSQP** (Sequential Least Squares Programming), 
un método numérico moderno que satisface las condiciones KKT al converger. 
NO corresponde al método Simplex de dos fases del libro, sino a un solver 
de optimización no lineal que maneja restricciones de forma eficiente.


## PASO 5: PROCESO DE OPTIMIZACION

**Método:** Sequential Least Squares Programming (SLSQP)

✔ **Convergencia exitosa**
  - Total de iteraciones: 7

**Punto inicial:**
  $$x^{(0)} = \begin{bmatrix} 10, 10, 10 \end{bmatrix}$$

**Iteraciones del algoritmo:**

**Iteración 0:** _Punto inicial. El algoritmo evalúa la función y restricciones._
  - $x^{(0)} = (33.0833, 33.5833, 100/3)$
  - $f(x^{(0)}) = 132.9198$
  - $||\nabla f|| = 4.7554$

**Iteración 1:** _Búsqueda de dirección de descenso que reduzca la función objetivo._
  - $x^{(1)} = (32.2643, 34.404, 33.3317)$
  - $f(x^{(1)}) = 131.6075$
  - $||\nabla f|| = 4.7186$

**Iteración 2:** _Búsqueda de dirección de descenso que reduzca la función objetivo._
  - $x^{(2)} = (29.989, 36.6593, 33.3517)$
  - $f(x^{(2)}) = 128.3315$
  - $||\nabla f|| = 4.6198$

**Iteración 3:** _Búsqueda de dirección de descenso que reduzca la función objetivo._
  - $x^{(3)} = (29.9496, 36.633, 33.4174)$
  - $f(x^{(3)}) = 128.3252$
  - $||\nabla f|| = 4.6194$

**Iteración 4:** _Búsqueda de dirección de descenso que reduzca la función objetivo._
  - $x^{(4)} = (29.7627, 36.5085, 33.7288)$
  - $f(x^{(4)}) = 128.2999$
  - $||\nabla f|| = 4.6178$

**Iteración 5:** _Búsqueda de dirección de descenso que reduzca la función objetivo._
  - $x^{(5)} = (29.2307, 36.1538, 34.6154)$
  - $f(x^{(5)}) = 128.2692$
  - $||\nabla f|| = 4.6137$

**Iteración 6:** _Búsqueda de dirección de descenso que reduzca la función objetivo._
  - $x^{(6)} = (29.2307, 36.1538, 34.6154)$
  - $f(x^{(6)}) = 128.2692$
  - $||\nabla f|| = 4.6137$

**Solución óptima encontrada:**
  - $A^* = 29.2307$
  - $B^* = 36.1538$
  - $F^* = 34.6154$

**Valor objetivo óptimo:**
  $$f(x^*) = 128.2692$$


## PASO 6: VERIFICACION KKT

**Verificación de condiciones KKT:**

**Gradiente en solución óptima:**
  $$\nabla f(x^*) = \begin{bmatrix} 3.2192, 1.9115, 2.6962 \end{bmatrix}$$

**Factibilidad primal:**
  - Residual igualdades: $0$
  - Violación desigualdades: $-25.76925154$
  - No negatividad: ✔ Satisfecha


## PASO 7: SOLUCION OPTIMA

**SOLUCIÓN ÓPTIMA:**

  - $A^* = 29.2307$
  - $B^* = 36.1538$
  - $F^* = 34.6154$

**Riesgo mínimo (varianza):**
  $$f(x^*) = 128.2692$$

**Multiplicadores de Lagrange (estimados):**

*Restricciones de igualdad ($\lambda_{eq}$):*
  - $\lambda_{1} = -2.609$

*Restricciones de desigualdad ($\lambda_{ineq}$):*
  - $\lambda_{1} = 4.6058$ (restricción activa)

*No-negatividad ($\mu$):*
  - Ninguna variable en límite ($\mu_i = 0$)


---

## 💡 CONCLUSIÓN E INTERPRETACIÓN

**Resumen de resultados:**

  • **A** = 29.2307
  • **B** = 36.1538
  • **F** = 34.6154

  • **Valor óptimo**: $f(x^*) = 128.2692$

**Interpretación:**

Este es un **problema de optimización de cartera de inversión** que busca
minimizar el riesgo (varianza) sujeto a restricciones de rendimiento y límites.

📈 **Decisión óptima de inversión:**
  • Invertir **29.2307** unidades monetarias en A (≈ 29.23% del total)
  • Invertir **36.1538** unidades monetarias en B (≈ 36.15% del total)
  • Invertir **34.6154** unidades monetarias en F (≈ 34.62% del total)

📉 **Riesgo mínimo alcanzable**: 128.2692

Esta distribución garantiza el **menor riesgo posible** mientras cumple con
todas las restricciones de rendimiento, diversificación y límites de inversión.


🔒 **Restricciones activas** (que limitan la solución óptima):
  • Restricción 1: $0.10*A + 0.05*B + 0.08*F - 7.5 \geq 0$

Estas restricciones están **'saturadas'** en el óptimo (se cumplen con igualdad).
Relajarlas (aumentar su límite) podría mejorar el valor óptimo.

---

### ✓ Procedimiento completado exitosamente
