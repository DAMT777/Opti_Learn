from __future__ import annotations

import ast
import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

import sympy as sp

from . import analyzer

OBJECTIVE_PATTERNS = [
    r'(?:func(?:i(?:\u00f3|o)n|tion)\s*(?:objetivo)?|objective|objetivo)\s*(?:[a-zA-Z]\s*\([^)]*\))?\s*(?:=|:)\s*(?P<expr>[^\n;]+)',
    r'(?:minimizar|minimize|maximizar|maximize)\s*(?P<expr>[^\n;]+)',
    r'[a-zA-Z]\s*\([^)]*\)\s*=\s*(?P<expr>[^\n;]+)',
]

CONSTRAINT_OPERATORS = {
    '<=': 'le',
    '>=': 'ge',
    '=': 'eq',
    '==': 'eq',
    '\u2264': 'le',
    '\u2265': 'ge',
}

DERIVATIVE_KEYWORDS = [
    'derivar',
    'derivada',
    'gradiente',
    'hessiano',
    'hessiana',
    'diferencial',
    'diferenciar',
    'calcular gradiente',
    'calcular hessiano',
]

OPTIMIZATION_KEYWORDS = [
    'minimizar',
    'maximizar',
    'optimizar',
    'restriccion',
    'restricciones',
    'sujeto a',
    'subject to',
]

METHOD_KEYWORDS = {
    'gradiente': 'gradient',
    'gradient': 'gradient',
    'lagrange': 'lagrange',
    'lagrangiano': 'lagrange',
    'kkt': 'kkt',
    'karush': 'kkt',
    'qp': 'qp',
    'cuadratic': 'qp',
    'quadratic': 'qp',
    'calculo': 'differential',
    'calculo diferencial': 'differential',
    'diferencial': 'differential',
}

_UNICODE_SYMBOLS = str.maketrans({
    '\u2212': '-',
    '\u2013': '-',
    '\u2014': '-',
    '\u00b7': '*',
    '\u00d7': '*',
    '\u00f7': '/',
})


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize('NFD', text or '')
    stripped = ''.join(ch for ch in normalized if unicodedata.category(ch) != 'Mn')
    return stripped.lower()


def _looks_like_math_token(token: str) -> bool:
    if not token:
        return False
    if re.fullmatch(r'[a-zA-Z](?:_[0-9]+)?', token):
        return True
    if re.search(r'[0-9+\-*/^(){}[\]]', token):
        return True
    return False


def _clean_expr(expr: str) -> str:
    expr = expr.strip()
    if len(expr) >= 2 and expr[0] in "\"'`" and expr[-1] == expr[0]:
        expr = expr[1:-1]
    return expr.strip().rstrip(';, .')


def _strip_to_math(expr: str) -> str:
    expr = expr.strip()
    for idx, ch in enumerate(expr):
        if ch.isalnum() or ch in "+-(":
            return expr[idx:].strip()
    return expr


def _parse_numeric_list(snippet: str) -> List[float] | None:
    snippet = snippet.strip()
    try:
        value = ast.literal_eval(snippet)
    except Exception:
        snippet = snippet.strip('[](){}')
        parts = [p.strip() for p in re.split(r'[;,]', snippet) if p.strip()]
        if not parts:
            return None
        try:
            value = [float(p) for p in parts]
        except Exception:
            return None
    if isinstance(value, (int, float)):
        return [float(value)]
    if isinstance(value, (list, tuple)):
        cleaned = []
        for item in value:
            try:
                cleaned.append(float(item))
            except Exception:
                return None
        return cleaned
    return None


def _parse_variables(snippet: str) -> List[str]:
    snippet = snippet.strip()
    if not snippet:
        return []
    if snippet.startswith('['):
        try:
            value = ast.literal_eval(snippet)
            if isinstance(value, (list, tuple)):
                return [str(v).strip() for v in value if str(v).strip()]
        except Exception:
            pass
    return [part.strip() for part in re.split(r'[,\s]+', snippet) if part.strip()]


def _infer_variables(expr: str) -> List[str]:
    try:
        expr_sym = sp.sympify(expr, locals=analyzer.FUNCIONES_PERMITIDAS)
        return sorted(str(sym) for sym in expr_sym.free_symbols)
    except Exception:
        return []


def _extract_objective(text: str) -> Tuple[Optional[str], Optional[Tuple[int, int]]]:
    for pattern in OBJECTIVE_PATTERNS:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            expr = _strip_to_math(_clean_expr(match.group('expr')))
            if expr:
                return expr, match.span('expr')
    return None, None


def _find_assignment_expr(text: str) -> Optional[str]:
    """
    Busca patrones del tipo C(x,y)=... dentro de un texto largo y devuelve la parte
    derecha de la asignación ya limpiada.
    """
    pattern = re.compile(r'([A-Za-z]\s*\([^)]*\)\s*=\s*[^.\n]+)')
    m = pattern.search(text)
    if not m:
        return None
    snippet = m.group(1)
    # Tomar solo lo que hay después del signo '='
    if '=' in snippet:
        snippet = snippet.split('=', 1)[1]
    expr = _strip_to_math(_clean_expr(snippet))
    return expr or None


def _slice_before_markers(text: str) -> str:
    normalized = _normalize_text(text)
    markers = [
        'x0',
        'punto inicial',
        'variables',
        'restriccion',
        'restricciones',
        'sujeto a',
        'subject to',
        'tol',
        'tolerancia',
        'iteraciones',
    ]
    positions = [normalized.find(marker) for marker in markers if marker in normalized]
    if not positions:
        return text
    cut = min(pos for pos in positions if pos >= 0)
    return text[:cut]


def _fallback_expr_from_context(text: str) -> Optional[str]:
    segment = _slice_before_markers(text)
    tokens = segment.strip().split()
    if not tokens:
        return None
    expr_tokens: List[str] = []
    for token in reversed(tokens):
        cleaned = token.strip(",.;")
        if _looks_like_math_token(cleaned):
            expr_tokens.append(cleaned)
            continue
        if expr_tokens:
            break
    expr_tokens.reverse()
    if not expr_tokens:
        return None
    candidate = " ".join(expr_tokens)
    candidate = _strip_to_math(_clean_expr(candidate))
    candidate = _massage_expression(candidate)
    if not candidate:
        return None
    try:
        sp.sympify(candidate, locals=analyzer.FUNCIONES_PERMITIDAS)
    except Exception:
        # Si sympify falla, devolvemos igualmente el candidato para merging posterior.
        pass
    return candidate


def _overlaps(span_a: Tuple[int, int], span_b: Tuple[int, int]) -> bool:
    return span_a[0] < span_b[1] and span_b[0] < span_a[1]


def _normalize_constraint(lhs: str, op: str, rhs: str) -> Dict[str, Any]:
    kind = CONSTRAINT_OPERATORS.get(op)
    expr = f"({lhs.strip()}) - ({rhs.strip()})"
    return {
        'kind': kind,
        'expr': expr,
        'raw': f"{lhs.strip()} {op} {rhs.strip()}",
    }


def _extract_constraints(text: str, objective_span: Optional[Tuple[int, int]]) -> List[Dict[str, Any]]:
    pattern = re.compile(r'(?P<lhs>[^<>=\n]+?)\s*(?P<op><=|>=|\u2264|\u2265|==|=)\s*(?P<rhs>[^\n;]+)')
    constraints: List[Dict[str, Any]] = []
    for match in pattern.finditer(text):
        span = match.span()
        if objective_span and _overlaps(span, objective_span):
            continue
        op = match.group('op')
        if op not in CONSTRAINT_OPERATORS:
            continue
        lhs = match.group('lhs')
        rhs = match.group('rhs')
        if not lhs or not rhs:
            continue
        normalized = _normalize_constraint(lhs, op, rhs)
        if normalized['kind']:
            constraints.append(normalized)
    return constraints


def _detect_method_hint(text: str) -> Optional[str]:
    normalized = _normalize_text(text)
    for keyword, method in METHOD_KEYWORDS.items():
        if keyword in normalized:
            return method
    return None


def _detect_derivative_only(text: str) -> bool:
    normalized = _normalize_text(text)
    has_derivative = any(keyword in normalized for keyword in DERIVATIVE_KEYWORDS)
    has_optimization = any(keyword in normalized for keyword in OPTIMIZATION_KEYWORDS)
    return has_derivative and not has_optimization


def parse_structured_payload(text: str, allow_partial: bool = False) -> Dict[str, Any] | None:
    if not text or not text.strip():
        return None

    text = text.translate(_UNICODE_SYMBOLS)
    expr, span = _extract_objective(text)
    if not expr:
        expr = _find_assignment_expr(text)
        span = None
    if not expr:
        expr = _fallback_expr_from_context(text)
        span = None
    if expr:
        expr = _massage_expression(_trim_expr_noise(expr))

    payload: Dict[str, Any] = {'objective_expr': expr, 'constraints': []}
    if expr is None and not allow_partial:
        return None

    var_match = re.search(r'variables?\s*[:=]\s*(\[[^\]]+\]|[a-zA-Z_,\s]+)', text, re.IGNORECASE)
    variables: List[str] = []
    if var_match:
        variables = _parse_variables(var_match.group(1))
    if not variables:
        variables = _infer_variables(expr)
    if variables:
        payload['variables'] = variables

    constraints = _extract_constraints(text, span)
    if constraints:
        payload['constraints'] = [{'kind': c['kind'], 'expr': c['expr']} for c in constraints]
        payload['constraints_raw'] = constraints

    x0_patterns = [
        r'x[_\s]?0\s*[:=]\s*(\[[^\]]+\]|\([^\)]+\)|\{[^\}]+\})',
        r'punto\s+inicial\s*[:=]\s*(\[[^\]]+\]|\([^\)]+\)|\{[^\}]+\})',
    ]
    for pattern in x0_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            x0_values = _parse_numeric_list(match.group(1))
            if x0_values is not None:
                payload['x0'] = x0_values
                break

    tol_match = re.search(r'tol(?:erancia)?\s*[:=]\s*([0-9eE\.\-+]+)', text, re.IGNORECASE)
    if tol_match:
        try:
            payload['tol'] = float(tol_match.group(1))
        except Exception:
            pass

    max_iter_match = re.search(r'(?:max(?:imo)?\s*iter|iteraciones\s*max)\s*[:=]\s*(\d+)', text, re.IGNORECASE)
    if max_iter_match:
        try:
            payload['max_iter'] = int(max_iter_match.group(1))
        except Exception:
            pass

    method_hint = _detect_method_hint(text)
    if method_hint:
        payload['method_hint'] = method_hint

    payload['derivative_only'] = _detect_derivative_only(text)

    if allow_partial:
        has_any = any(
            key in payload and payload[key] not in (None, [], '', {})
            for key in ['objective_expr', 'variables', 'constraints', 'x0', 'tol', 'max_iter', 'method_hint']
        )
        return payload if has_any else None

    return payload if expr else None


def _trim_expr_noise(expr: str) -> str:
    if not expr:
        return expr
    lower = expr.lower()
    markers = [
        ' donde',
        '\ndonde',
        ' sujeto',
        ' subject',
        ' en este',
        'en este',
        ' objetivo',
        ' objective',
        ' restriccion',
        ' restricción',
    ]
    indices = [lower.find(marker) for marker in markers if lower.find(marker) != -1]
    if indices:
        cut = min(pos for pos in indices if pos >= 0)
        expr = expr[:cut]
    if '=' in expr:
        first = expr.find('=')
        second = expr.find('=', first + 1)
        if second != -1:
            expr = expr[:second]
    return expr.strip()


def _massage_expression(expr: str) -> str:
    if not expr:
        return expr
    expr = expr.translate(_UNICODE_SYMBOLS)
    expr = expr.replace('^', '**')
    # Convertir (x-3) 2 -> (x-3)**2 antes de insertar productos implícitos
    expr = re.sub(r'\(([^)]*)\)\s*(\d+)', r'(\1)**\2', expr)
    # Eliminar posibles repeticiones del nombre de la función al final (p. ej., "C(x,y)")
    expr = re.sub(r'\b[A-Z]\s*\([^)]*\)\s*$', '', expr)
    # Insertar multiplicación implícita donde aplique
    expr = re.sub(r'(?<=\d)\s*\(', '*(', expr)  # 7(y+2) -> 7*(y+2)
    expr = re.sub(r'(?<=\d)(?=[A-Za-z])', '*', expr)  # 5x -> 5*x
    expr = re.sub(r'(?<=\))\s+(?=\d)', ' * ', expr)
    return expr