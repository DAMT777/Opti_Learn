from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

from django.conf import settings


def _get_api_key() -> Optional[str]:
    # Prioriza variable de entorno y limpia espacios/comillas accidentales.
    raw = os.getenv("GROQ_API_KEY") or getattr(settings, "GROQ_API_KEY", None)
    if raw is None:
        return None
    key = str(raw).strip().strip('"').strip("'")
    return key or None


def resolve_prompt_path() -> Optional[Path]:
    """Devuelve la ruta resuelta del prompt (aunque no exista) o None si no hay configuración."""
    conf = getattr(settings, "AI_ASSISTANT", {}) or {}
    raw_path = conf.get("prompt_path")
    if not raw_path:
        return None
    p = Path(str(raw_path))
    if not p.is_absolute():
        try:
            base_dir = Path(getattr(settings, "BASE_DIR", "."))
            p = (base_dir / p).resolve()
        except Exception:
            pass
    return p


def load_system_prompt() -> str:
    p = resolve_prompt_path()
    try:
        if p and p.is_file():
            return p.read_text(encoding="utf-8")
    except Exception:
        pass
    # Fallback conciso si no existe el archivo.
    return (
        "Eres un asistente educativo de optimización no lineal. "
        "Responde con Markdown claro usando secciones (## Problema, ## Análisis, ## Método Recomendado, ## Paso a Paso, ## Resultado, ## Interpretación). "
        "Incluye fórmulas LaTeX cuando ayuden y un bloque JSON final con campos {metodo, razon, pasos, resultado, explicacion}."
    )


def _get_client():
    key = _get_api_key()
    if not key:
        return None
    try:
        from groq import Groq  # import local para no romper si no está instalado
    except Exception:  # pragma: no cover
        return None
    return Groq(api_key=key)


def chat_completion(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> str:
    client = _get_client()
    if client is None:
        raise RuntimeError(
            "GROQ_API_KEY no configurada o paquete 'groq' no instalado."
        )

    conf = getattr(settings, "AI_ASSISTANT", {}) or {}
    primary = model or conf.get("model") or "llama-3.1-8b-instant"
    fallbacks = list(conf.get("fallback_models", [])) or [
        "llama-3.1-8b-instant",
        "llama-3.1-70b-versatile",
        "mixtral-8x7b-32768",
    ]
    # Garantiza que el primario está al frente sin duplicarse
    models_to_try = [m for m in [primary] + fallbacks if m]
    seen = set()
    models_to_try = [m for m in models_to_try if not (m in seen or seen.add(m))]

    temperature = temperature if temperature is not None else float(conf.get("temperature", 0.2))
    max_tokens = max_tokens or int(conf.get("max_tokens", 2048))

    sys_prompt = load_system_prompt()
    chat_messages = [{"role": "system", "content": sys_prompt}] + list(messages)

    last_err: Optional[Exception] = None
    for mdl in models_to_try:
        try:
            response = client.chat.completions.create(
                model=mdl,
                messages=chat_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content  # type: ignore[no-any-return]
        except Exception as e:  # pragma: no cover
            # Si es un error por modelo dado-de-baja, prueba el siguiente
            msg = str(e).lower()
            if any(k in msg for k in ["decommissioned", "model_not_found", "unknown model", "not supported"]):
                last_err = e
                continue
            # Otros errores: propaga
            raise
    # Si no funcionó ningún fallback, lanza el último error
    raise RuntimeError(f"No se pudo usar los modelos {models_to_try}: {last_err}")


def build_messages_from_session(session_messages: List[Dict[str, str]], user_text: str) -> List[Dict[str, str]]:
    # Recorta historial si fuese muy largo; aquí mantenemos últimas ~10 interacciones.
    history = session_messages[-20:] if len(session_messages) > 20 else session_messages
    return history + [{"role": "user", "content": user_text}]

