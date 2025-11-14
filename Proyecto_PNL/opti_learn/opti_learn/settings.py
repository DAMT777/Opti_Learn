import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

# Carga variables desde .env si existe (desarrollo / despliegues simples)
# override=True para priorizar el archivo .env sobre variables previas del sistema
# (útil si antes configuraste GROQ_API_KEY con setx y ahora quieres usar .env)
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv(BASE_DIR / ".env", override=True)
except Exception:
    # Si python-dotenv no está instalado, continúa sin romper
    pass

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-insecure-secret-key")
DEBUG = os.getenv("DEBUG", "1") == "1"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'channels',
    'opti_app',
]

MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'opti_learn.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],  # Usar plantillas por app
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'opti_learn.wsgi.application'
ASGI_APPLICATION = 'opti_learn.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ),
}

# Channels (in-memory por defecto para desarrollo)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    }
}

# Configuración del asistente IA (Groq)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # No hardcodear secretos
AI_ASSISTANT = {
    'provider': 'groq',
    # Modelos recomendados por Groq a 2025: usa env si está definido.
    'model': os.getenv('GROQ_MODEL', 'llama-3.1-8b-instant'),
    'fallback_models': [
        os.getenv('GROQ_FALLBACK_1', 'llama-3.1-70b-versatile'),
        os.getenv('GROQ_FALLBACK_2', 'mixtral-8x7b-32768'),
    ],
    'temperature': float(os.getenv('AI_TEMPERATURE', '0.2')),
    'max_tokens': int(os.getenv('AI_MAX_TOKENS', '2048')),
    'prompt_path': os.getenv(
        'AI_PROMPT_PATH',
        str((Path(__file__).resolve().parent.parent / 'opti_app' / 'ai' / 'prompt_contextual.txt').resolve())
    ),
}
