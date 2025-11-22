from __future__ import annotations

import re
import unicodedata
from typing import Iterable


# Palabras clave usadas para detectar si el mensaje habla de PNL.
_PNL_KEYWORDS = [
    'pnl',
    'programacion no lineal',
    'optimiza',
    'lagrange',
    'lagrangiano',
    'kkt',
    'karush',
    'gradiente',
    'gradient',
    'descenso',
    'armijo',
    'multiplicador',
    'hessiano',
    'restriccion',
    'restricciones',
    'funcion objetivo',
    'objetivo',
    'minimizar',
    'maximizar',
    'qp',
    'programacion cuadratica',
    'diferencial',
    'lagrangeano',
    'nabla',
    'x0',
    'objective_expr',
    'constraints',
    'variables',
]

_REGEX_PATTERNS = [
    r'f\s*\([^)]*\)\s*=\s*',
    r'\bmin(?:imizar)?\b',
    r'\bmax(?:imizar)?\b',
    r'\bnabla\b',
    r'\bgrad(?:iente|ient)?\b',
    r'\blagrange\b',
    r'\bkarush\b',
    r'\bkkt\b',
]

_GREETINGS = ['hola', 'buen dia', 'buenos dias', 'buenas', 'saludos']
_IDENTITY = [
    'quien te creo',
    'quien te hizo',
    'quien eres',
    'quienes son tus creadores',
    'quien te construyo',
]
_META = ['optilearn', 'universidad de los llanos', 'diego alejandro machado', 'juan carlos barrera', 'jesus gregorio delgado']
_SYMBOLS = '\u2207\u2264\u2265\u03bb\u03bc'
_SCOPE_MESSAGE = (
    'No podemos responder esa solicitud porque esta fuera del alcance de Programacion No Lineal (PNL) '
    'que cubre OptiLearn Web. Solo atendemos consultas sobre los metodos Gradiente, Lagrange, KKT, '
    'Calculo Diferencial y Programacion Cuadratica. Describe la funcion objetivo, las variables y las '
    'restricciones para poder ayudarte.'
)


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize('NFD', text)
    return ''.join(ch for ch in normalized if unicodedata.category(ch) != 'Mn')


def _normalize(text: str) -> str:
    cleaned = _strip_accents(text or '')
    cleaned = cleaned.lower()
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()


def _contains_any(text: str, keywords: Iterable[str]) -> bool:
    return any(kw in text for kw in keywords)


def _looks_like_pnl(raw: str, normalized: str) -> bool:
    if _contains_any(normalized, _PNL_KEYWORDS):
        return True
    for pattern in _REGEX_PATTERNS:
        if re.search(pattern, normalized):
            return True
    if any(symbol in raw for symbol in _SYMBOLS):
        return True
    if '{' in raw and _contains_any(normalized, ['objective_expr', 'constraints', 'variables', 'x0']):
        return True
    if '**' in raw or '^' in raw:
        return True
    return False


def classify_message(text: str) -> str:
    """Clasifica el texto segun el uso previsto por el asistente."""
    normalized = _normalize(text)
    raw = text or ''
    if not normalized:
        return 'empty'
    if _contains_any(normalized, _GREETINGS):
        return 'greeting'
    if _contains_any(normalized, _IDENTITY):
        return 'identity'
    if _contains_any(normalized, _META):
        return 'meta'
    if _looks_like_pnl(raw, normalized):
        return 'pnl'
    return 'out_of_scope'


def is_message_allowed(text: str) -> bool:
    """Devuelve True si el mensaje puede procesarse (PNL o categorias permitidas)."""
    return classify_message(text) != 'out_of_scope'


def scope_violation_reply() -> str:
    """Mensaje estandar cuando la consulta no es de PNL."""
    return _SCOPE_MESSAGE
