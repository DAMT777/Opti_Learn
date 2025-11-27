PROGRAMACION CUADRATICA - METODO KKT
================================================================================

▸ PASO 1: DEFINICION DEL PROBLEMA
--------------------------------------------------------------------------------

Función objetivo:
  $$0.04*A**2 + 0.02*B**2 + 0.03*F**2 + 0.01*A*B + 0.015*A*F + 0.005*B*F$$

Variables: $A, B, F$

**Restricciones:**
  - $A + B + F = 100.0$
  - $-0.10*A - 0.05*B - 0.08*F ≤ -7.5$
  - $-A ≤ -20.0$
  - $B ≤ 50.0$
  - $-F ≤ -10.0$
  - $F ≤ 40.0$
  - $-B - F ≤ -45.0$

▸ PASO 2: MATRICES
--------------------------------------------------------------------------------

**Vector $C$ (coeficientes lineales):**
  $$C = \begin{bmatrix} 0, 0, 0 \end{bmatrix}$$

**Matriz $D$ (coeficientes cuadráticos):**
  $$D = \begin{bmatrix} 0.08 & 0.01 & 0.015 \\\\ 0.01 & 0.04 & 0.005 \\\\ 0.015 & 0.005 & 0.06 \end{bmatrix}$$

**Matriz $A_{eq}$ (restricciones igualdad):**
  $$A_{eq} = \begin{bmatrix} 1 & 1 & 1 \end{bmatrix}$$

**Vector $b_{eq}$:**
  $$b_{eq} = \begin{bmatrix} 100 \end{bmatrix}$$

**Matriz $A_{ineq}$ (restricciones desigualdad):**
  $$A_{ineq} = \begin{bmatrix} -1/10 & -0.05 & -0.08 \\\\ -1 & 0 & 0 \\\\ 0 & 1 & 0 \\\\ 0 & 0 & -1 \\\\ 0 & 0 & 1 \\\\ 0 & -1 & -1 \end{bmatrix}$$

**Vector $b_{ineq}$:**
  $$b_{ineq} = \begin{bmatrix} -15/2, -20, 50, -10, 40, -45 \end{bmatrix}$$

▸ PASO 3: CONVEXIDAD
--------------------------------------------------------------------------------

**Eigenvalores de $D$:**
  - $\lambda_{1} = 0.090501$ (\geq 0)
  - $\lambda_{2} = 0.051978$ (\geq 0)
  - $\lambda_{3} = 0.03752$ (\geq 0)

✔ **El problema es CONVEXO**
  El método garantiza encontrar el óptimo global

▸ PASO 4: SISTEMA KKT
--------------------------------------------------------------------------------

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

▸ PASO 5: PROCESO DE OPTIMIZACION
--------------------------------------------------------------------------------

**Método:** Sequential Least Squares Programming (SLSQP)

✔ **Convergencia exitosa**
  - Total de iteraciones: 7

**Punto inicial:**
  $$x^{(0)} = \begin{bmatrix} 10, 10, 10 \end{bmatrix}$$

**Iteraciones del algoritmo:**

**Iteración 0:**
  - $x^{(0)} = (33.0833, 33.5833, 100/3)$
  - $f(x^{(0)}) = 132.9198$
  - $||\nabla f|| = 4.7554$

**Iteración 1:**
  - $x^{(1)} = (32.2643, 34.404, 33.3317)$
  - $f(x^{(1)}) = 131.6075$
  - $||\nabla f|| = 4.7186$

**Iteración 2:**
  - $x^{(2)} = (29.989, 36.6593, 33.3517)$
  - $f(x^{(2)}) = 128.3315$
  - $||\nabla f|| = 4.6198$

**Iteración 3:**
  - $x^{(3)} = (29.9496, 36.633, 33.4174)$
  - $f(x^{(3)}) = 128.3252$
  - $||\nabla f|| = 4.6194$

**Iteración 4:**
  - $x^{(4)} = (29.7627, 36.5085, 33.7288)$
  - $f(x^{(4)}) = 128.2999$
  - $||\nabla f|| = 4.6178$

**Iteración 5:**
  - $x^{(5)} = (29.2307, 36.1538, 34.6154)$
  - $f(x^{(5)}) = 128.2692$
  - $||\nabla f|| = 4.6137$

**Iteración 6:**
  - $x^{(6)} = (29.2307, 36.1538, 34.6154)$
  - $f(x^{(6)}) = 128.2692$
  - $||\nabla f|| = 4.6137$

**Solución óptima encontrada:**
  - $A^* = 29.2307$
  - $B^* = 36.1538$
  - $F^* = 34.6154$

**Valor objetivo óptimo:**
  $$f(x^*) = 128.2692$$

▸ PASO 6: VERIFICACION KKT
--------------------------------------------------------------------------------

**Verificación de condiciones KKT:**

**Gradiente en solución óptima:**
  $$\nabla f(x^*) = \begin{bmatrix} 3.2192, 1.9115, 2.6962 \end{bmatrix}$$

**Factibilidad primal:**
  - Residual igualdades: $0$
  - Violación desigualdades: $0$
  - No negatividad: ✔ Satisfecha

▸ PASO 7: SOLUCION OPTIMA
--------------------------------------------------------------------------------

**SOLUCIÓN ÓPTIMA:**

  - $A^* = 29.2307$
  - $B^* = 36.1538$
  - $F^* = 34.6154$

**Riesgo mínimo (varianza):**
  $$f(x^*) = 128.2692$$

================================================================================
PROCEDIMIENTO COMPLETADO
================================================================================