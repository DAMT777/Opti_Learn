PROGRAMACION CUADRATICA - METODO DE DOS FASES
================================================================================

▸ PASO 1: DEFINICION DEL PROBLEMA
--------------------------------------------------------------------------------

Función objetivo:
  $$A**2 + B**2$$

Variables: $A, B$
Número de variables: 2

Restricciones:
  - Igualdades: 1
  - Desigualdades: 0
  - No negatividad: $x \geq 0$

▸ PASO 2: MATRICES
--------------------------------------------------------------------------------

Vector $C$ (coeficientes lineales):
  $$C = \begin{bmatrix} 0, 0 \end{bmatrix}$$

Matriz $D$ (coeficientes cuadráticos):
  $$D = \begin{bmatrix} 2 & 0 \\ 0 & 2 \end{bmatrix}$$

Matriz $A$ (restricciones):
  $$A = \begin{bmatrix} 1 & 1 \end{bmatrix}$$

Vector $b$:
  $$b = \begin{bmatrix} 1 \end{bmatrix}$$

▸ PASO 3: CONVEXIDAD
--------------------------------------------------------------------------------

Eigenvalores de $D$:
  $\lambda_{1} = 2$ (\geq 0)
  $\lambda_{2} = 2$ (\geq 0)

✔ El problema es **CONVEXO**
  El método garantiza encontrar el óptimo global

▸ PASO 4: SISTEMA KKT
--------------------------------------------------------------------------------

**Condiciones de Karush-Kuhn-Tucker:**

1. **Estacionariedad**: $\nabla f(x) + A^T\lambda + \mu = 0$
2. **Factibilidad primal**: $Ax = b$, $x \geq 0$
3. **Factibilidad dual**: $\mu \geq 0$
4. **Complementariedad**: $\mu_i \cdot x_i = 0$ $\forall i$

**Variables del sistema:**
  - $x$ (decisión): 2
  - $\lambda$ (restricciones): 1
  - $\mu$ (no negatividad): 2

**Gradiente de $f(x)$:**
$$\nabla f(x) = \begin{bmatrix}
  2x_{1} \\
  2x_{2} \\
\end{bmatrix}$$

**Sistema de estacionariedad expandido:**
  $$2x_{1} + \lambda_{1} + \mu_{1} = 0$$
  $$2x_{2} + \lambda_{1} + \mu_{2} = 0$$


▸ PASO 5: FASE I
--------------------------------------------------------------------------------

**FASE I**: Búsqueda de solución factible
Objetivo: Minimizar $W = \sum_{i} R_i$

**Tabla inicial:**
```
Basica |   x1   |   x2   |   R1   |   RHS   
--------------------------------------------
R1     |   1    |   1    |   1    |    1    
--------------------------------------------
Z      |   -1   |   -1   |   0    |    -1   
```

**→ Iteración 1**
- Variable entrante: $x1$ (coeficiente más negativo)
- Variable saliente: $R1$ (ratio test mínimo = $1$)
- Elemento pivote: $1$

Tabla **antes** del pivote:
```
Basica |   x1   |   x2   |   R1   |   RHS   
--------------------------------------------
R1     |   1    |   1    |   1    |    1    
--------------------------------------------
Z      |   -1   |   -1   |   0    |    -1   
```

Tabla **después** del pivote:
```
Basica |   x1   |   x2   |   R1   |   RHS   
--------------------------------------------
x1     |   1    |   1    |   1    |    1    
--------------------------------------------
Z      |   0    |   0    |   1    |    0    
```

**Resultado Fase I:**
  - $W_{final} = 0$
  - ✔ Problema **FACTIBLE** → continuar con Fase II

▸ PASO 6: FASE II
--------------------------------------------------------------------------------

**FASE II**: Optimización de $f(x)$

**Tabla inicial Fase II:**
```
Basica |   x1   |   x2   | lambda1 |  mu1   |  mu2   |   RHS   
---------------------------------------------------------------
R1     |   1    |   1    |    0    |   0    |   0    |    1    
mu1    |   1    |   0    |    0    |   -1   |   0    |    0    
mu2    |   0    |   1    |    0    |   0    |   -1   |    0    
---------------------------------------------------------------
Z      |   0    |   0    |    0    |   0    |   0    |    0    
```

**Tabla final (óptima):**
```
Basica |   x1   |   x2   | lambda1 |  mu1   |  mu2   |   RHS   
---------------------------------------------------------------
R1     |   1    |   1    |    0    |   0    |   0    |    1    
mu1    |   1    |   0    |    0    |   -1   |   0    |    0    
mu2    |   0    |   1    |    0    |   0    |   -1   |    0    
---------------------------------------------------------------
Z      |   0    |   0    |    0    |   0    |   0    |    0    
```

**Solución óptima:**
  - $x_{1}^* = 0$
  - $x_{2}^* = 0$
  - $f(x^*) = 0$

▸ PASO 7: SOLUCION OPTIMA
--------------------------------------------------------------------------------

**SOLUCIÓN ÓPTIMA:**

  $A^* = 0$
  $B^* = 0$

Valor objetivo óptimo:
  $$f(x^*) = 0$$

================================================================================
PROCEDIMIENTO COMPLETADO
================================================================================