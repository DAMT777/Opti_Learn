# 🎯 MÉTODO DE MULTIPLICADORES DE LAGRANGE

---

## PASO 1: PRESENTACIÓN DEL PROBLEMA

### ✔️ Función Objetivo

$$f(x, y) = x^{2} + y^{2}$$

### ✔️ Restricciones (igualdades)

**Restricción 1:**
$$g_1(x, y) = x + y - 1 = 0$$

### ✔️ Variables de Decisión

**Variables:** $x, y$

---

### 🔧 Vamos a unir la función objetivo con la restricción usando Lagrange

**Estrategia:** Transformar el problema restringido en uno sin restricciones
mediante la función Lagrangiana, que incorpora las restricciones usando
multiplicadores (λ).

## PASO 2: CONSTRUCCIÓN DE LA LAGRANGIANA

$$\mathcal{L}(x, y, \lambda) = - \lambda \left(x + y - 1\right) + x^{2} + y^{2}$$

**Componentes:**

- **Función objetivo:** $f(x, y)$
- **Penalización restricción 1:** $-(\lambda \left(x + y - 1\right))$

📌 **Explicación pedagógica:**

*La Lagrangiana mezcla la función objetivo con la restricción para
transformarlo en un problema sin restricciones. El multiplicador λ
ajusta automáticamente la importancia de cumplir cada restricción.*

## PASO 3: DERIVADAS PARCIALES (CONDICIÓN DE ESTACIONARIEDAD)

Para encontrar puntos críticos, igualamos a cero todas las derivadas parciales:

$$\frac{\partial \mathcal{L}}{\partial x} = - \lambda + 2 x = 0$$

$$\frac{\partial \mathcal{L}}{\partial y} = - \lambda + 2 y = 0$$

$$\frac{\partial \mathcal{L}}{\partial lambda} = - x - y + 1 = 0$$

💡 **Interpretación pedagógica:**

*Cada derivada es un sensor que indica dónde la función deja de cambiar.
Cuando todas las derivadas son cero, hemos encontrado un punto crítico*
*candidato a óptimo.*

## PASO 4: SISTEMA DE ECUACIONES

El sistema resultante es:

$$\begin{cases}
- \lambda + 2 x = 0 \\
- \lambda + 2 y = 0 \\
- x - y + 1 = 0 \\
\end{cases}$$

**Total de ecuaciones:** 3
**Total de incógnitas:** 3

## PASO 5: RESOLUCIÓN DEL SISTEMA

✅ **Se encontraron 1 solución(es)**

### Solución 1:

- $x^* = \frac{1}{2}$
- $y^* = \frac{1}{2}$
- $\lambda^* = 1$

📌 **Nota pedagógica:**

*El multiplicador λ nos indica cuánta presión ejerce la restricción
sobre la solución. Un λ grande significa que la restricción está*
*"apretando" mucho el óptimo.*

## PASO 6: ANÁLISIS DEL HESSIANO

Para determinar si el punto crítico es mínimo, máximo o punto silla,
analizamos el Hessiano de la función objetivo:

$$H_f = \left[\begin{matrix}2 & 0\\0 & 2\end{matrix}\right]$$

**Valores propios (eigenvalues):**

- $\lambda_1 = 2.0000$
- $\lambda_2 = 2.0000$

**Clasificación:** Definida positiva → Mínimo local

## PASO 7: CÁLCULO DEL VALOR ÓPTIMO

**Punto óptimo:** $(x^* = 0.5000, y^* = 0.5000)$

$$f(x^*) = 0.5000$$

✅ **Este es el valor mínimo alcanzado**

**Multiplicadores de Lagrange:**

- $lambda = 1.0000$

## PASO 8: INTERPRETACIÓN PEDAGÓGICA

📘 **Conclusión:**

*La solución cumple la restricción, satisface el gradiente nulo y por tanto*
*representa un punto crítico candidato a óptimo.*

**Naturaleza del punto:** mínimo

**¿Qué significa el multiplicador λ?**

- Representa la **sensibilidad** del valor óptimo respecto a cambios en la restricción
- Si λ es grande: la restricción está "apretando" mucho la solución
- Si λ es pequeño: la restricción tiene poco impacto en el óptimo

**¿Por qué esta solución respeta la igualdad?**

- La derivada ∂L/∂λ = 0 **fuerza** que se cumpla g(x) = 0
- Es decir, el método de Lagrange garantiza automáticamente la factibilidad

## PASO 9: RESUMEN FINAL

### 📋 Checklist de Validación

- ☑ **Estacionariedad:** ∇L = 0 verificado
- ☑ **Cumplimiento de restricción:** g(x) = 0 verificado
- ☑ **Naturaleza del punto:** Mínimo local (H definida positiva)

### 🎯 Resultado Final

| Variable | Valor Óptimo |
|----------|--------------|
| x | 0.5000 |
| y | 0.5000 |
| lambda | 1.0000 |

**Valor óptimo:** f(x*) = 0.5000

---

## 📊 VISUALIZACIÓN GEOMÉTRICA DEL MÉTODO DE LAGRANGE

**Interpretación gráfica:**

El siguiente gráfico muestra:
- **Curvas de nivel** de la función objetivo f(x, y) en tonos de color
- **Restricción de igualdad** g(x, y) = 0 en rojo
- **Punto óptimo** marcado en verde donde ocurre la tangencia

<img src="/static/tmp/lagrange_7748.png" alt="Visualización de Lagrange" style="max-width: 100%; width: 600px; height: auto; display: block; margin: 20px auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />

💡 **Observación clave:** El punto óptimo se encuentra donde una curva de nivel
de la función objetivo es **tangente** a la restricción. Esta tangencia es la
condición geométrica que caracteriza al método de Lagrange.

---

### ✓ Procedimiento completado exitosamente
