from __future__ import annotations

from typing import Dict, Any


def recomendar_metodo(m: Dict[str, Any]) -> Dict[str, Any]:
    """
    Selecciona el metodo segun reglas formales y orden explicitado en el arbol de decision.
    """
    iterativo = bool(m.get('iterative_process'))
    eq = bool(m.get('has_equalities'))
    ineq = bool(m.get('has_inequalities'))
    cuadratico = bool(m.get('is_quadratic'))
    lineal = bool(m.get('constraints_are_linear'))
    deriv = bool(m.get('derivative_only'))
    method_hint = (m.get('method_hint') or '').strip()
    restricciones = bool(m.get('has_constraints') or eq or ineq)

    # 0. Iterativo → Gradiente
    if iterativo:
        return {'method': 'gradient', 'rationale': 'Proceso iterativo explicito.'}

    # 0b. Hint explicito (gradiente ya cubierto). Respeta KKT, Lagrange, differential, qp.
    if method_hint in {'kkt', 'lagrange', 'differential', 'gradient', 'qp'}:
        return {'method': method_hint, 'rationale': f'Metodo indicado por el enunciado/IA: {method_hint}.'}

    # 1. Desigualdades no lineales → KKT
    if ineq and not lineal:
        return {'method': 'kkt', 'rationale': 'Existen desigualdades no lineales: condiciones KKT.'}

    # 2. Igualdades → Lagrange
    if eq:
        return {'method': 'lagrange', 'rationale': 'Restricciones de igualdad sin desigualdad.'}

    # 3. Sin restricciones
    if not restricciones:
        if deriv:
            return {'method': 'differential', 'rationale': 'Puntos criticos / derivadas detectadas.'}
        return {'method': 'gradient', 'rationale': 'Sin restricciones y no derivadas → Gradiente.'}

    # 4. QP solo aqui (cuadratico + restricciones lineales, incluye desigualdades lineales)
    if cuadratico and lineal and restricciones:
        return {'method': 'qp', 'rationale': 'Objetivo cuadratico + restricciones lineales.'}

    # 5. Desigualdades restantes → KKT
    if ineq:
        return {'method': 'kkt', 'rationale': 'Existen desigualdades: condiciones KKT.'}

    return {'method': None, 'rationale': 'No se pudo clasificar.'}


# Alias de compatibilidad
def recommend(meta: Dict[str, Any]) -> Dict[str, Any]:
    return recomendar_metodo(meta)
