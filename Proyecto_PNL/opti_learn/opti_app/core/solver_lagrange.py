from __future__ import annotations

from typing import Dict, Any, List


def solve_with_lagrange_method(
    objective_expression: str,
    variable_names: List[str],
    equality_constraints: List[str],
) -> Dict[str, Any]:
    """Stub del método de Lagrange con nombres autodescriptivos.

    Parámetros
    - objective_expression: expresión SymPy de la función objetivo f(x)
    - variable_names: nombres de variables en orden, p. ej. ["x", "y"]
    - equality_constraints: lista de expresiones g_i(x)=0 escritas como strings

    Retorna
    - Dict con metadatos del método y estado not_implemented (MVP)
    """
    return {
        'method': 'lagrange',
        'status': 'not_implemented',
        'message': 'Solver de Lagrange pendiente en MVP',
        'received': {
            'objective_expression': objective_expression,
            'variable_names': variable_names,
            'equality_constraints': equality_constraints,
        },
    }


# Alias de compatibilidad hacia atrás.
def solve(objective_expr: str, variables: List[str], equalities: List[str]) -> Dict[str, Any]:
    return solve_with_lagrange_method(
        objective_expression=objective_expr,
        variable_names=variables,
        equality_constraints=equalities,
    )
