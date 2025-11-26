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
    lineales = bool(m.get('constraints_are_linear'))
    restricciones = bool(m.get('has_constraints') or eq or ineq)
    derivadas = bool(m.get('derivative_only'))

    # 0) Si el problema indica explícitamente que el método es iterativo → Gradiente
    if iterativo:
        return {
            'method': 'gradient',
            'rationale': 'El enunciado describe un procedimiento iterativo → Gradiente.',
        }

    # 1) QP: cuadratica + restricciones lineales + al menos una restriccion
    if cuadratico and lineales and restricciones:
        return {
            'method': 'qp',
            'rationale': 'Funcion cuadratica + restricciones lineales: Programacion Cuadratica.',
        }

    # 2) Si hay desigualdades → KKT
    if ineq:
        return {
            'method': 'kkt',
            'rationale': 'Existen desigualdades: se usan condiciones KKT.',
        }

    # 3) Solo igualdades → Lagrange
    if eq:
        return {
            'method': 'lagrange',
            'rationale': 'Solo restricciones de igualdad: metodo de Lagrange.',
        }

    # 4) Sin restricciones
    if not restricciones:
        if derivadas:
            return {
                'method': 'differential',
                'rationale': 'Sin restricciones y el problema pide puntos criticos: Calculo diferencial.',
            }
        return {
            'method': 'gradient',
            'rationale': 'Sin restricciones y sin indicacion de derivadas: descenso por gradiente.',
        }

    return {'method': None, 'rationale': 'No se pudo clasificar.'}


# Alias de compatibilidad
def recommend(meta: Dict[str, Any]) -> Dict[str, Any]:
    return recomendar_metodo(meta)
