# ESPECIFICACIÓN TÉCNICA: SOLVER QP PEDAGÓGICO

## OBJETIVO
Implementar un solver de Programación Cuadrática que muestre el **procedimiento completo** del método de dos fases de forma **clara, estructurada y pedagógica**, sin sobre-decoración con emojis.

## PRINCIPIOS FUNDAMENTALES

### ❌ LO QUE NO ES "LÚDICO"
- Llenar de emojis cada línea
- Usar colores sin propósito técnico
- Decorar en vez de explicar
- Ocultar el proceso detrás de frases bonitas

### ✅ LO QUE SÍ ES "PEDAGÓGICO"
- Mostrar TODAS las iteraciones del algoritmo
- Explicar CADA decisión (variable entrante, saliente, pivote)
- Presentar tablas Simplex completas en cada paso
- Justificar técnicamente cada movimiento
- Trazabilidad total del procedimiento

## ESTRUCTURA REQUERIDA

### PASO 1: Presentación del Problema
```markdown
## PASO 1: PRESENTACION DEL PROBLEMA
--------------------------------------------------------------------------------

### Formulacion del Problema

**Funcion objetivo:**
```
minimize f(x) = ...
```

**Variables de decision:** x1, x2, ..., xn
**Numero de variables:** n

**Estructura de restricciones:**
- Restricciones de igualdad (Ax = b): m_eq
- Restricciones de desigualdad (Cx <= d): m_ineq
- Restricciones de no negatividad (x >= 0): aplicadas a todas las variables

**Forma estandar del problema:**
```
min f(X) = C*X + (1/2)X^T*D*X
s.a. A*X = b
     X >= 0
```
```

### PASO 2: Extracción de Matrices
```markdown
## PASO 2: EXTRACCION DE MATRICES
--------------------------------------------------------------------------------

### Matrices Extraidas del Problema

**Dimensiones de las matrices:**
- C (vector lineal): R^n
- D (matriz hessiana): R^n×n
- A (matriz de restricciones): R^m×n
- b (vector RHS): R^m

**Vector C (coeficientes lineales):**
```
C = [c1, c2, ..., cn]
```

**Matriz D (coeficientes cuadraticos - define curvatura):**
```
D = [d11  d12  ...  d1n]
    [d21  d22  ...  d2n]
    [...  ...  ...  ...]
    [dn1  dn2  ...  dnn]
```

**Matriz A (coeficientes de restricciones):**
```
A = [a11  a12  ...  a1n]
    [a21  a22  ...  a2n]
    [...  ...  ...  ...]
    [am1  am2  ...  amn]
```

**Vector b (terminos independientes):**
```
b = [b1, b2, ..., bm]
```
```

### PASO 3: Análisis de Convexidad
```markdown
## PASO 3: ANALISIS DE CONVEXIDAD
--------------------------------------------------------------------------------

### Analisis de Convexidad

**Metodo:** Descomposicion espectral de la matriz Hessiana D
**Objetivo:** Determinar si el problema es convexo

**Eigenvalores de D:**
  lambda_1 = xxx.xxxxxx (>= 0)
  lambda_2 = xxx.xxxxxx (>= 0)
  ...

**Clasificacion:** Definida positiva (convexa) / No convexa

**Implicacion:** Para problemas convexos, el metodo de dos fases
garantiza encontrar el optimo global. Las condiciones KKT son necesarias
y suficientes para optimalidad.
```

### PASO 4: Sistema KKT
```markdown
## PASO 4: SISTEMA KKT
--------------------------------------------------------------------------------

### Sistema de Optimalidad (KKT)

**Condiciones de Karush-Kuhn-Tucker:**

1. **Estacionariedad:**
   Grad(f(x)) + A^T*lambda + I*mu = 0
   (El gradiente de f se equilibra con las restricciones)

2. **Factibilidad primal:**
   A*x = b, x >= 0
   (El punto satisface todas las restricciones)

3. **Factibilidad dual:**
   mu >= 0
   (Los multiplicadores son no negativos)

4. **Complementariedad:**
   mu_i * x_i = 0 para todo i
   (Holgura complementaria: restriccion activa o multiplicador cero)

**Variables del sistema KKT:**
- Variables de decision (x): n
- Multiplicadores de restricciones (lambda): m
- Multiplicadores de no negatividad (mu): n
- **Total:** 2n + m variables en el sistema KKT
```

### PASO 5: Preparación del Método
```markdown
## PASO 5: PREPARACION METODO DOS FASES
--------------------------------------------------------------------------------

### Preparacion del Metodo de Dos Fases

**Fundamento teorico:**
Se requieren variables artificiales para inicializar el metodo Simplex
con una base factible inicial. En la Fase I, minimizamos W = suma(Ri)
donde Ri son las variables artificiales. Cuando W = 0, hemos encontrado
una solucion factible del sistema original.

**Estrategia del algoritmo:**
- **Fase I:** Minimizar W = suma de variables artificiales para encontrar factibilidad
- **Fase II:** Optimizar la funcion objetivo original desde base factible

**Variables del sistema Simplex:**
  - x (decision): n variables
  - lambda (restricciones): m variables
  - mu (no negatividad): n variables
  - R (artificiales): m_eq variables (solo para igualdades)
  - S (holguras): m_ineq variables (solo si hay desigualdades)
```

### PASO 6: FASE I - COMPLETA
```markdown
## PASO 6: FASE I - BUSQUEDA DE FACTIBILIDAD
--------------------------------------------------------------------------------

### FASE I: Busqueda de Solucion Factible

**Objetivo de Fase I:** Minimizar W = suma(Ri) para eliminar variables artificiales

**Iteraciones del algoritmo Simplex:**

**[ITERACION 0] - Configuracion Inicial**
- Tabla inicial de Fase I con variables artificiales en la base
- Base inicial: R1, R2, ..., Rm
- Funcion objetivo W: suma de artificiales

TABLA SIMPLEX (Iteracion 0):
```
Base  |  x1    x2   ...  xn  |  R1   R2  ...  Rm  | RHS
------|----------------------|--------------------|---------
R1    | a11   a12  ... a1n  |   1    0  ...   0  | b1
R2    | a21   a22  ... a2n  |   0    1  ...   0  | b2
...   | ...   ...  ... ...  |  ...  ...  ... ... | ...
Rm    | am1   am2  ... amn  |   0    0  ...   1  | bm
------|----------------------|--------------------|---------
W     | c1    c2   ... cn   |   0    0  ...   0  | 0
```

**[ITERACION 1] - Operacion de Pivote**
- Variable entrante: x_j (columna con coeficiente mas negativo en W)
- Variable saliente: R_i (ratio test: min{b_i/a_ij : a_ij > 0})
- Elemento pivote: a_ij
- Criterio de seleccion: Regla del minimo ratio
- Justificacion: La columna de x_j tiene el coeficiente mas negativo en la fila objetivo

TABLA SIMPLEX (Iteracion 1):
```
[Tabla despues del pivote - mostrar completa]
```

... [MOSTRAR TODAS LAS ITERACIONES] ...

**[ITERACION FINAL] - Optimo de Fase I**
- Valor final de W: 0.0000
- Todas las variables artificiales han salido de la base
- Conclusion: El problema es factible - se continua con Fase II

TABLA FINAL DE FASE I:
```
[Tabla final completa]
```

**RESULTADO DE FASE I:**
- Estado: Solucion factible encontrada
- Valor final de W: 0.0000
- Conclusion: Todas las variables artificiales eliminadas (W = 0)
- El problema es factible - se continua con Fase II

**Resumen de Fase I:**
- Numero de iteraciones: k
- Objetivo alcanzado: SI
```

### PASO 7: FASE II - COMPLETA
```markdown
## PASO 7: FASE II - OPTIMIZACION
--------------------------------------------------------------------------------

### FASE II: Optimizacion de la Funcion Objetivo

**Objetivo de Fase II:** Minimizar f(x) = C*x + (1/2)x^T*D*x

**Iteraciones de optimizacion:**

**[ITERACION 0] - Inicio de Fase II**
- Tabla inicial de Fase II (factible, sin artificiales)
- Funcion objetivo: f(x) original

TABLA SIMPLEX (Iteracion 0 - Fase II):
```
[Tabla completa]
```

**[ITERACION 1] - Mejora del Objetivo**
- Variable entrante: x_k
- Variable saliente: mu_j
- Elemento pivote: a_jk
- Justificacion: Coeficiente mas negativo en fila objetivo
- Reduccion de objetivo: delta_f

TABLA SIMPLEX (Iteracion 1 - Fase II):
```
[Tabla completa despues del pivote]
```

... [MOSTRAR TODAS LAS ITERACIONES] ...

**[ITERACION FINAL] - Optimo Alcanzado**
- Condicion de optimalidad: Todos los costos reducidos >= 0
- No existen mejoras posibles

TABLA OPTIMA FINAL:
```
Base  |  x1    x2   ...  xn  |  mu1  mu2  ... mun | RHS
------|----------------------|--------------------|---------
...   | ...   ...  ... ...  |  ...  ...  ... ... | ...
------|----------------------|--------------------|---------
f(x)  | c1'   c2'  ... cn'  | mu1'  mu2' ... mun'| f_opt
```

**RESULTADO DE FASE II:**
- Estado: Optimo encontrado
- Condicion de optimalidad: Todos los costos reducidos >= 0
- No existen mejoras posibles

**Solucion obtenida:**
  x_1 = xxx.xxxxxx
  x_2 = xxx.xxxxxx
  ...

**Valor optimo:**
  f(x*) = xxx.xxxxxx

**Resumen de Fase II:**
- Numero de iteraciones: k
- Solucion optima: SI
```

### PASO 8: Verificación KKT
```markdown
## PASO 8: VERIFICACION KKT
--------------------------------------------------------------------------------

### Verificacion de Condiciones KKT

**1. Estacionariedad:** Verificada
   Grad(f(x*)) + A^T*lambda* + I*mu* = 0

**2. Factibilidad primal:** Verificada
   A*x* = b, x* >= 0

**3. Factibilidad dual:** Verificada
   mu* >= 0

**4. Complementariedad:** Verificada
   mu_i * x_i = 0 para todo i

**Conclusion:** Todas las condiciones KKT satisfechas - punto optimo validado
```

### PASO 9: Solución e Interpretación
```markdown
## PASO 9: SOLUCION E INTERPRETACION
--------------------------------------------------------------------------------

### Solucion Final

**Solucion optima:**
  x1* = xxx.xxxxxx
  x2* = xxx.xxxxxx
  ...
  xn* = xxx.xxxxxx

**Valor objetivo optimo:** f(x*) = xxx.xxxxxx

**Significado:** El valor optimo de la funcion objetivo es xxx.xxxxxx

**Interpretacion:** Este es el mejor valor posible que satisface todas
las restricciones del problema. En el contexto del problema original,
esto significa [interpretacion contextual segun el problema].
```

## NOTAS TÉCNICAS FINALES
```markdown
================================================================================
## NOTAS TECNICAS DEL PROCEDIMIENTO
================================================================================

### Fundamentos Teoricos:

**1. Metodo de Dos Fases**
   - Fase I busca factibilidad mediante minimizacion de artificiales
   - Fase II optimiza la funcion original desde una base factible
   - Garantiza encontrar el optimo si el problema es factible y acotado

**2. Condiciones KKT**
   - Necesarias para optimalidad en cualquier problema con restricciones
   - Suficientes para optimalidad global en problemas convexos
   - Generalizan las condiciones de Lagrange

**3. Convexidad**
   - Determinada por eigenvalores de la matriz Hessiana D
   - Garantiza que cualquier optimo local es global
   - Fundamental para la validez teorica del metodo

### Aplicaciones Practicas:

- Optimizacion de carteras financieras (minimizacion de riesgo)
- Planificacion de produccion (minimizacion de costos)
- Machine Learning (entrenamiento de modelos)
- Control optimo (minimizacion de error)

================================================================================
PROCEDIMIENTO COMPLETADO
================================================================================
```

## REGLAS DE IMPLEMENTACIÓN

### ✅ DEBE HACER:
1. Mostrar TODAS las tablas Simplex completas
2. Explicar CADA pivote con justificación
3. Mostrar iteración 0, 1, 2, ..., hasta óptimo
4. Usar formato técnico limpio y estructurado
5. Dimensiones de matrices siempre visibles
6. Ratio test explicado en cada pivote
7. Variables base/no base identificadas
8. Valor objetivo en cada iteración

### ❌ NO DEBE HACER:
1. Omitir iteraciones ("... después de varias iteraciones ...")
2. Saltar tablas
3. Dar resultados sin justificación
4. Sobre-decorar con emojis innecesarios
5. Ocultar el proceso detrás de frases vagas
6. Resumir en lugar de mostrar
7. Usar decoración en lugar de explicación técnica

## CRITERIO DE ACEPTACIÓN

Una implementación es CORRECTA si:
- [ ] Muestra cada tabla Simplex completa
- [ ] Explica cada pivote (entrante, saliente, elemento pivote)
- [ ] Justifica cada decisión del algoritmo
- [ ] No omite ninguna iteración
- [ ] Formato claro y técnicamente correcto
- [ ] Variables λ y μ correctamente contadas
- [ ] Holguras S solo si hay desigualdades
- [ ] Artificiales R solo si hay igualdades
- [ ] Trazabilidad total del procedimiento

## EJEMPLO DE ITERACIÓN CORRECTA

```markdown
**[ITERACION 3] - Operacion de Pivote**

**Tabla actual:**
```
Base  |  x1     x2     x3   |  mu1    mu2    mu3  | RHS
------|---------------------|---------------------|----------
mu1   | 2.000  1.000  0.000 | 1.000   0.000  0.000| 4.000
x2    | 0.500  1.000  0.000 | 0.000   1.000  0.000| 2.000
x3    | 0.000  0.000  1.000 | 0.000   0.000  1.000| 1.000
------|---------------------|---------------------|----------
f(x)  |-3.000  0.000  0.000 | 0.000   0.000  0.000| -6.000
```

**Analisis para siguiente pivote:**
- Coeficientes en fila objetivo: [-3.000, 0.000, 0.000, 0.000, 0.000, 0.000]
- Columna mas negativa: x1 (coeficiente -3.000)
- **Variable entrante:** x1

**Ratio test:**
- Fila mu1: 4.000 / 2.000 = 2.000 ← MINIMO
- Fila x2: 2.000 / 0.500 = 4.000
- Fila x3: no aplica (coeficiente = 0)

- **Variable saliente:** mu1
- **Elemento pivote:** 2.000
- **Justificacion:** Se elige x1 porque tiene el coeficiente mas negativo (-3.000).
  Se elige mu1 porque tiene el minimo ratio (2.000).

**Operacion de pivote:**
- Dividir fila mu1 entre 2.000
- Eliminar x1 en las demas filas

**Tabla despues del pivote:**
```
Base  |  x1     x2     x3   |  mu1    mu2    mu3  | RHS
------|---------------------|---------------------|----------
x1    | 1.000  0.500  0.000 | 0.500   0.000  0.000| 2.000
x2    | 0.000  0.750  0.000 |-0.250   1.000  0.000| 1.000
x3    | 0.000  0.000  1.000 | 0.000   0.000  1.000| 1.000
------|---------------------|---------------------|----------
f(x)  | 0.000  1.500  0.000 | 1.500   0.000  0.000| 0.000
```

**Resultado de iteracion:**
- Nuevo valor objetivo: 0.000
- Reduccion: -6.000 → 0.000 (mejora de 6.000)
- Continuar con siguiente iteracion
```

Este nivel de detalle es OBLIGATORIO para cada iteración.

---

**NOTA FINAL:** El carácter pedagógico NO viene de los emojis, sino de la 
CLARIDAD, COMPLETITUD y TRAZABILIDAD del procedimiento mostrado.
