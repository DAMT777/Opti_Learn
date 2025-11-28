# 🌐 Visualización 3D del Método de Multiplicadores de Lagrange

## Descripción General

El módulo `visualizer_lagrange_3d.py` proporciona **visualizaciones tridimensionales** para problemas de optimización con restricciones de igualdad resueltos mediante el Método de Multiplicadores de Lagrange.

---

## 🎯 Características Principales

### ✅ Visualización Automática

- **Generación automática** para todos los problemas 2D (2 variables)
- **Doble visualización**: 2D (curvas de nivel) + 3D (superficie)
- **Integración perfecta** con el solver de Lagrange existente

### 🎨 Elementos Visuales en 3D

1. **Superficie de la Función Objetivo**
   - Renderizada con colormap viridis
   - 100×100 puntos de resolución
   - Transparencia alpha=0.7 para mejor visualización

2. **Curva de Restricción**
   - Color: Rojo intenso
   - Grosor: 3px
   - Proyectada sobre la superficie f(x,y)
   - Calculada mediante solver numérico (scipy.fsolve)

3. **Punto Óptimo**
   - Marcador: Esfera verde lima
   - Tamaño: 150 unidades
   - Borde: Verde oscuro
   - Con línea vertical descendente al plano base

4. **Proyección en el Plano XY**
   - Punto semitransparente en el plano base
   - Ayuda a ubicar la posición horizontal del óptimo

5. **Caja de Texto Pedagógica**
   - Explica la condición de tangencia
   - Fondo color trigo con transparencia
   - Ubicación: Esquina superior izquierda

### 📐 Configuración Técnica

```python
# Tamaño y resolución
figsize = (10, 8)  # pulgadas
dpi = 120
output_size ≈ 250-360 KB

# Vista de cámara 3D
elevation = 25°  # Ángulo vertical
azimuth = 45°    # Ángulo horizontal

# Colorbar
shrink = 0.6     # Factor de escala
aspect = 10      # Relación de aspecto
```

### 🔧 Aspectos Técnicos

**Backend de Matplotlib:**
```python
matplotlib.use('Agg')  # Sin GUI, ideal para servidor
```

**Cálculo de la Curva de Restricción:**
- Método: Solver numérico (scipy.optimize.fsolve)
- 200 puntos de muestreo
- Tolerancia: residual < 0.01
- Filtrado automático de puntos inválidos

**Rango de Visualización:**
- Centro: Punto óptimo (x*, y*)
- Margen: 1.5× max(|x*|, |y*|, 2.0)
- Adaptativo según la escala del problema

---

## 📊 Comparación 2D vs 3D

| Aspecto | Visualización 2D | Visualización 3D |
|---------|------------------|------------------|
| **Vista** | Curvas de nivel (plano) | Superficie completa |
| **Comprensión** | Tangencia en el plano | Altura sobre restricción |
| **Tamaño archivo** | ~170-200 KB | ~250-360 KB |
| **Ancho display** | 600px | 700px |
| **Uso pedagógico** | Condición geométrica | Perspectiva espacial |

---

## 🚀 Uso en el Código

### Importación

```python
from opti_app.core.visualizer_lagrange_3d import generate_lagrange_3d_plot
```

### Invocación Directa

```python
plot_path = generate_lagrange_3d_plot(
    objective="x**2 + y**2",
    variables=['x', 'y'],
    constraints=["x + y - 1"],
    optimal_point={'x': 0.5, 'y': 0.5},
    optimal_value=0.5,
    filename='mi_plot_3d.png'
)
```

### Integración Automática en Solver

El solver de Lagrange genera **automáticamente** ambas visualizaciones:

```python
from opti_app.core.solver_lagrange import solve_with_lagrange_method

result = solve_with_lagrange_method(
    objective_expression="x**2 + y**2",
    variable_names=['x', 'y'],
    equality_constraints=["x + y - 1"]
)

# result['explanation'] incluye AMBAS imágenes:
# - lagrange_2d_*.png (curvas de nivel)
# - lagrange_3d_*.png (superficie 3D)
```

---

## 📂 Estructura de Archivos

```
opti_app/
├── core/
│   ├── visualizer_lagrange.py      # Visualizador 2D (curvas de nivel)
│   ├── visualizer_lagrange_3d.py   # Visualizador 3D (superficie) ✨ NUEVO
│   └── solver_lagrange.py          # Solver integrado
├── static/
│   └── tmp/
│       ├── lagrange_2d_*.png       # Imágenes 2D generadas
│       └── lagrange_3d_*.png       # Imágenes 3D generadas ✨ NUEVO
```

---

## 🧪 Tests Disponibles

### Test Completo de Visualización 3D
```bash
python test_lagrange_3d.py
```

**Incluye 3 casos de prueba:**
1. Problema básico: x² + y² con x + y = 1
2. Problema no lineal: x² + 4y² con x + 2y = 6
3. Problema del servidor: -t² - k² + 12t + 8k con 2t + k = 18

### Test Visual Rápido
```bash
python test_visual_3d.py
```

Genera un ejemplo único para inspección visual rápida.

---

## 🎓 Valor Pedagógico

### ¿Por qué Visualización 3D?

**Ventajas didácticas:**

1. **Intuición Espacial**: Los estudiantes ven la "colina" o "valle" de la función objetivo
2. **Restricción Visible**: La curva roja muestra el "camino permitido"
3. **Óptimo Claro**: El punto verde está en la "cima" o "valle" dentro del camino
4. **Perpendicular Visual**: Se puede apreciar que ∇f ⟂ restricción

**Complementariedad:**
- **2D**: Muestra la condición de tangencia (curva nivel ∥ restricción)
- **3D**: Muestra la altura óptima sobre la restricción

---

## 🔍 Ejemplo de Salida

### Problema del Servidor
```python
Minimizar: f(t,k) = -t² - k² + 12t + 8k
Sujeto a: 2t + k = 18
```

**Resultado:**
- Punto óptimo: (t*=6.8, k*=4.4)
- Valor óptimo: f*=51.2
- Naturaleza: **Máximo local**

**Visualizaciones generadas:**
1. `lagrange_2d_*.png` - Curvas de nivel mostrando tangencia
2. `lagrange_3d_*.png` - Superficie mostrando la "cima" del problema

---

## ⚙️ Configuración Avanzada

### Personalizar Vista 3D

```python
visualizer = LagrangeVisualizer3D(output_dir="mi_carpeta/")

# Modificar antes de create_3d_visualization():
# - Cambiar ángulo de cámara: ax.view_init(elev=30, azim=60)
# - Ajustar colormap: cmap=cm.coolwarm
# - Modificar resolución: num_points=150
```

### Troubleshooting

**Problema:** Curva de restricción no aparece

**Solución:** 
- La restricción puede ser muy compleja para resolver numéricamente
- El método usa scipy.fsolve con tolerancia flexible
- Si falla, la superficie se muestra sin la curva roja

**Problema:** Imágenes muy grandes

**Solución:**
- Reducir DPI: `plt.savefig(..., dpi=100)`
- Reducir tamaño: `figsize=(8, 6)`

---

## 📈 Rendimiento

| Métrica | Valor |
|---------|-------|
| Tiempo generación | ~0.5-1.5 segundos |
| Tamaño archivo | 250-360 KB |
| Resolución malla | 100×100 puntos |
| Puntos restricción | 200 evaluaciones |

---

## 🔮 Futuras Mejoras

- [ ] Animación rotativa de la superficie 3D
- [ ] Visualización de múltiples restricciones
- [ ] Vista interactiva (plotly) para exploración
- [ ] Gradientes visualizados como vectores 3D
- [ ] Plano tangente en el punto óptimo
- [ ] Curvas de nivel proyectadas en el plano base

---

## ✅ Conclusión

La visualización 3D es una **herramienta pedagógica poderosa** que complementa perfectamente la visualización 2D existente. Juntas, proporcionan:

- **Comprensión completa** del método de Lagrange
- **Validación visual** de la solución numérica
- **Intuición geométrica** sobre restricciones y gradientes
- **Experiencia de aprendizaje enriquecida**

🎯 **El solver de Lagrange ahora ofrece visualizaciones de clase mundial para la enseñanza de optimización restringida.**
