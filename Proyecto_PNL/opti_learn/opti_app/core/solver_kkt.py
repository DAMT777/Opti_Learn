from __future__ import annotations

from typing import Dict, Any


def resolver_kkt(*args, **kwargs) -> Dict[str, Any]:
    return {
        'method': 'kkt',
        'status': 'not_implemented',
        'message': 'Solver KKT pendiente en MVP',
    }


# Alias de compatibilidad
def solve(*args, **kwargs) -> Dict[str, Any]:
    return resolver_kkt(*args, **kwargs)
