from __future__ import annotations

from typing import Dict, Any


def resolver_qp(*args, **kwargs) -> Dict[str, Any]:
    return {
        'method': 'qp',
        'status': 'not_implemented',
        'message': 'QP pendiente (OSQP/quadprog) en MVP',
    }


# Alias de compatibilidad
def solve_qp(*args, **kwargs) -> Dict[str, Any]:
    return resolver_qp(*args, **kwargs)
