# Guía de Capturas de Pantalla

Este documento describe qué capturas de pantalla necesitas agregar al manual.

## Ubicación de las imágenes

Todas las imágenes deben colocarse en la carpeta `public/images/` según su categoría.

## Capturas necesarias

### Screenshots (`/images/screenshots/`)

1. **interfaz-principal.png**
   - Captura de la pantalla principal de OptiLearn Web
   - Muestra: formulario de entrada, botones, áreas de resultado
   - Tamaño recomendado: 1200x800px

2. **ejemplo-gradiente.png**
   - Captura de un problema resuelto con Gradiente Descendente
   - Incluye: entrada del problema, tabla de iteraciones, gráfica
   - Debe mostrar la trayectoria de optimización

3. **ejemplo-lagrange.png**
   - Captura de un problema con Multiplicadores de Lagrange
   - Incluye: función objetivo, restricciones de igualdad, solución

4. **ejemplo-kkt.png**
   - Captura de un problema con Condiciones KKT
   - Incluye: restricciones no lineales, análisis de multiplicadores

5. **ejemplo-qp.png**
   - Captura de Programación Cuadrática
   - Incluye: análisis de convexidad, Fase I y II, solución

6. **ejemplo-diferencial.png**
   - Captura de análisis diferencial
   - Incluye: gradiente simbólico, Hessiana, clasificación de puntos

### Diagramas (`/images/diagramas/`)

1. **arquitectura.png**
   - Diagrama de arquitectura del sistema
   - Componentes: Frontend, Backend, IA, Base de datos
   - Puede ser creado con draw.io, Lucidchart, o similar

2. **flujo-datos.png**
   - Diagrama de flujo de datos entre componentes
   - Muestra el recorrido desde la entrada del usuario hasta la respuesta

3. **casos-uso.png** (opcional)
   - Diagrama de casos de uso UML
   - Actores: Usuario, Sistema IA, Administrador

4. **diagrama-secuencia.png** (opcional)
   - Diagrama de secuencia del proceso de solución
   - Interacciones entre módulos

### Resultados (`/images/resultados/`)

1. **tabla-iteraciones.png**
   - Captura de una tabla de iteraciones del gradiente
   - Muestra: k, x_k, f(x_k), ||∇f||, α_k

2. **grafica-convergencia.png**
   - Gráfica mostrando la convergencia del algoritmo
   - Puede incluir: trayectoria en 2D/3D, evolución de f(x)

3. **explicacion-ia.png**
   - Captura de la explicación pedagógica generada por la IA
   - Muestra el texto explicativo con viñetas

## Cómo tomar las capturas

1. **Ejecuta el servidor OptiLearn Web**:
   ```bash
   cd opti_learn
   daphne -b 127.0.0.1 -p 8000 opti_learn.asgi:application
   ```

2. **Abre el navegador** en `http://localhost:8000`

3. **Para cada método**:
   - Ingresa un problema de ejemplo
   - Espera la solución completa
   - Toma captura de pantalla (Windows: Win + Shift + S)
   - Guarda con el nombre correcto

4. **Edita las capturas** (opcional):
   - Recorta áreas innecesarias
   - Ajusta tamaño si es muy grande
   - Añade anotaciones si ayuda a la comprensión

## Herramientas recomendadas

- **Capturas**: Snipping Tool (Windows), Screenshot (Mac), Flameshot (Linux)
- **Edición**: Paint, GIMP, Photoshop
- **Diagramas**: Draw.io, Lucidchart, PlantUML, Mermaid

## Formato de archivos

- **Formato**: PNG (preferido) o JPG
- **Resolución**: 72-150 DPI
- **Tamaño**: Máximo 2MB por imagen
- **Dimensiones**: Entre 800-1600px de ancho

## Verificación

Después de agregar las imágenes, verifica que:
- ✅ Las rutas en los archivos `.mdx` son correctas
- ✅ Las imágenes se cargan correctamente en el manual
- ✅ El tamaño no afecta la velocidad de carga
- ✅ Las capturas son claras y legibles

## Comando para verificar

```bash
cd manual-usuario
npm run dev
```

Luego navega a `http://localhost:3000` y revisa cada página.
