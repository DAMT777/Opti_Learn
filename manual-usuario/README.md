# Manual de Usuario - OptiLearn Web

Este es el manual de usuario para OptiLearn Web, desarrollado con Next.js y Nextra.

## Instalación

```bash
npm install
```

## Desarrollo

```bash
npm run dev
```

El manual estará disponible en `http://localhost:3000`

## Build para producción

```bash
npm run build
npm start
```

## Estructura

- `pages/` - Páginas del manual en formato MDX
- `theme.config.jsx` - Configuración del tema Nextra
- `next.config.js` - Configuración de Next.js

## Contenido

El manual incluye:
- Introducción al sistema
- Primeros pasos
- Guías de cada método de optimización
- Ejemplos prácticos
- Arquitectura del sistema
- Preguntas frecuentes

## Actualización

Para añadir nuevas páginas:
1. Crea un archivo `.mdx` en la carpeta `pages/`
2. Actualiza `_meta.json` si es necesario
3. Usa Markdown estándar con soporte para componentes React

## Tecnologías

- Next.js 14
- Nextra 2.13
- React 18
