Instalación del cliente Groq
============================

Para habilitar el módulo de IA con Groq:

1) Instala la librería de Python

   pip install groq

   (Opcional) añade a tu requirements:

   groq>=0.10.0

2) Configura la clave de API

   Opción A: usando archivo `.env` (recomendado en desarrollo)

   - Copia `opti_learn/.env.example` a `opti_learn/.env` y completa:

     GROQ_API_KEY=TU_CLAVE_AQUI

   Opción B: como variable de entorno del sistema (Windows PowerShell)

     setx GROQ_API_KEY "TU_CLAVE_AQUI"

   Luego cierra y vuelve a abrir la terminal si usas `setx`.

3) Variables opcionales:

   - GROQ_MODEL (por defecto: llama-3.1-8b-instant)
   - AI_TEMPERATURE (por defecto: 0.2)
   - AI_MAX_TOKENS (por defecto: 2048)
   - AI_PROMPT_PATH (ruta alternativa al prompt contextual)
