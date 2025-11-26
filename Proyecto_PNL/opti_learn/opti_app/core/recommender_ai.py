from __future__ import annotations

from typing import Dict, Any


def recomendar_metodo(metadatos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Selecciona el metodo segun reglas formales:
    Prioridad segun arbol de decision:
    1) QP solo si: objetivo estrictamente cuadratico + TODAS las restricciones lineales + al menos una restriccion.
    2) Si hay desigualdades y no aplica QP -> KKT.
    3) Si hay solo igualdades (sin desigualdades) -> Lagrange.
    4) Sin restricciones:
       - Funcion simple/pocos vars -> Calculo diferencial.
       - Funcion compleja/multiples vars -> Gradiente.
    Si nada aplica, devuelve method=None.
    """
    iterativo = bool(metadatos.get('iterative_process'))
    hay_igualdades = bool(metadatos.get('has_equalities'))
    hay_desigualdades = bool(metadatos.get('has_inequalities'))
    es_cuadratico = bool(metadatos.get('is_quadratic'))
    restricciones_lineales = bool(metadatos.get('constraints_are_linear'))
    hay_restricciones = bool(metadatos.get('has_constraints') or hay_igualdades or hay_desigualdades)
    derivative_only = bool(metadatos.get('derivative_only'))

    # 0) QP clasico con restricciones lineales (requiere al menos una restriccion)
    if es_cuadratico and restricciones_lineales and hay_restricciones:
        return {
            'method': 'qp',
            'rationale': 'Objetivo estrictamente cuadratico con restricciones lineales y al menos una restriccion: Programacion Cuadratica.',
        }
    # 1) Desigualdades (no QP) -> KKT
    if hay_desigualdades:
        return {
            'method': 'kkt',
            'rationale': 'Hay restricciones de desigualdad (y posibles igualdades): condiciones KKT.',
        }
    # 3) Solo igualdades -> Lagrange
    if hay_igualdades:
        return {
            'method': 'lagrange',
            'rationale': 'Solo restricciones de igualdad: metodo de Lagrange.',
        }
    # 4) Sin restricciones
    if not hay_restricciones:
        if derivative_only:
            return {
                'method': 'differential',
                'rationale': 'Sin restricciones y la tarea es analitica (puntos criticos/estabilidad): calculo diferencial.',
            }
        # Sin restricciones no se clasifica como QP; elegir entre gradiente/diferencial segun complejidad.
        if iterativo:
            return {
                'method': 'gradient',
                'rationale': 'Sin restricciones y se menciona proceso iterativo: gradiente.',
            }
        return {
            'method': 'gradient',
            'rationale': 'Sin restricciones y enfoque numerico general: descenso por gradiente.',
        }
    # 5) No aplica ninguna regla
    return {
        'method': None,
        'rationale': 'No es posible determinar el metodo con la informacion disponible.',
    }


# Alias de compatibilidad
def recommend(meta: Dict[str, Any]) -> Dict[str, Any]:
    return recomendar_metodo(meta)
