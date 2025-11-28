# 🎯 MÉTODO DE MULTIPLICADORES DE LAGRANGE

---

## PASO 1: PRESENTACIÓN DEL PROBLEMA

### ✔️ Función Objetivo

$$f(t, k) = - k^{2} + 8 k - t^{2} + 12 t$$

### ✔️ Restricciones (igualdades)

**Restricción 1:**
$$g_1(t, k) = k + 2 t - 18 = 0$$

### ✔️ Variables de Decisión

**Variables:** $t, k$

---

### 🔧 Vamos a unir la función objetivo con la restricción usando Lagrange

**Estrategia:** Transformar el problema restringido en uno sin restricciones
mediante la función Lagrangiana, que incorpora las restricciones usando
multiplicadores (λ).

## PASO 2: CONSTRUCCIÓN DE LA LAGRANGIANA

$$\mathcal{L}(t, k, \lambda) = - k^{2} + 8 k - \lambda \left(k + 2 t - 18\right) - t^{2} + 12 t$$

**Componentes:**

- **Función objetivo:** $f(t, k)$
- **Penalización restricción 1:** $-(\lambda \left(k + 2 t - 18\right))$

📌 **Explicación pedagógica:**

*La Lagrangiana mezcla la función objetivo con la restricción para
transformarlo en un problema sin restricciones. El multiplicador λ
ajusta automáticamente la importancia de cumplir cada restricción.*

## PASO 3: DERIVADAS PARCIALES (CONDICIÓN DE ESTACIONARIEDAD)

Para encontrar puntos críticos, igualamos a cero todas las derivadas parciales:

$$\frac{\partial \mathcal{L}}{\partial t} = - 2 \lambda - 2 t + 12 = 0$$

$$\frac{\partial \mathcal{L}}{\partial k} = - 2 k - \lambda + 8 = 0$$

$$\frac{\partial \mathcal{L}}{\partial lambda} = - k - 2 t + 18 = 0$$

💡 **Interpretación pedagógica:**

*Cada derivada es un sensor que indica dónde la función deja de cambiar.
Cuando todas las derivadas son cero, hemos encontrado un punto crítico*
*candidato a óptimo.*

## PASO 4: SISTEMA DE ECUACIONES

El sistema resultante es:

$$\begin{cases}
- 2 \lambda - 2 t + 12 = 0 \\
- 2 k - \lambda + 8 = 0 \\
- k - 2 t + 18 = 0 \\
\end{cases}$$

**Total de ecuaciones:** 3
**Total de incógnitas:** 3

## PASO 5: RESOLUCIÓN DEL SISTEMA

✅ **Se encontraron 1 solución(es)**

### Solución 1:

- $t^* = \frac{34}{5}$
- $k^* = \frac{22}{5}$
- $\lambda^* = - \frac{4}{5}$

📌 **Nota pedagógica:**

*El multiplicador λ nos indica cuánta presión ejerce la restricción
sobre la solución. Un λ grande significa que la restricción está*
*"apretando" mucho el óptimo.*

## PASO 6: ANÁLISIS DEL HESSIANO

Para determinar si el punto crítico es mínimo, máximo o punto silla,
analizamos el Hessiano de la función objetivo:

$$H_f = \left[\begin{matrix}-2 & 0\\0 & -2\end{matrix}\right]$$

**Valores propios (eigenvalues):**

- $\lambda_1 = -2.0000$
- $\lambda_2 = -2.0000$

**Clasificación:** Definida negativa → Máximo local

## PASO 7: CÁLCULO DEL VALOR ÓPTIMO

**Punto óptimo:** $(t^* = 6.8000, k^* = 4.4000)$

$$f(x^*) = 51.2000$$

✅ **Este es el valor máximo alcanzado**

**Multiplicadores de Lagrange:**

- $lambda = -0.8000$

## PASO 8: INTERPRETACIÓN PEDAGÓGICA

📘 **Conclusión:**

*La solución cumple la restricción, satisface el gradiente nulo y por tanto*
*representa un punto crítico candidato a óptimo.*

**Naturaleza del punto:** máximo

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
- ☑ **Naturaleza del punto:** Máximo local (H definida negativa)

### 🎯 Resultado Final

| Variable | Valor Óptimo |
|----------|--------------|
| t | 6.8000 |
| k | 4.4000 |
| lambda | -0.8000 |

**Valor óptimo:** f(x*) = 51.2000

---

## 📊 VISUALIZACIÓN GEOMÉTRICA DEL MÉTODO DE LAGRANGE

**Interpretación gráfica:**

El siguiente gráfico muestra:
- **Curvas de nivel** de la función objetivo f(x, y) en tonos de color
- **Restricción de igualdad** g(x, y) = 0 en rojo
- **Punto óptimo** marcado en verde donde ocurre la tangencia

<img src="/static/tmp/lagrange_6307.png" alt="Visualización de Lagrange" style="max-width: 100%; width: 600px; height: auto; display: block; margin: 20px auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />

💡 **Observación clave:** El punto óptimo se encuentra donde una curva de nivel
de la función objetivo es **tangente** a la restricción. Esta tangencia es la
condición geométrica que caracteriza al método de Lagrange.

---

### ✓ Procedimiento completado exitosamente
