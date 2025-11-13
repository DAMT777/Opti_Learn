from __future__ import annotations

from typing import Dict, Any


def recomendar_metodo(metadatos: Dict[str, Any]) -> Dict[str, Any]:
    hay_igualdades = bool(metadatos.get('has_equalities'))
    hay_desigualdades = bool(metadatos.get('has_inequalities'))
    es_cuadratico = bool(metadatos.get('is_quadratic'))

    if not hay_igualdades and not hay_desigualdades:
        metodo = 'gradient'
        justificacion = 'Problema sin restricciones: aplicar gradiente descendente (o análisis diferencial).'
    elif hay_igualdades and not hay_desigualdades:
        metodo = 'lagrange'
        justificacion = 'Restricciones de igualdad detectadas: aplicar método de Lagrange.'
    elif hay_desigualdades:
        if es_cuadratico:
            metodo = 'qp'
            justificacion = 'Estructura cuadrática con desigualdades: formular y resolver QP.'
        else:
            metodo = 'kkt'
            justificacion = 'Desigualdades generales: aplicar condiciones KKT.'
    else:
        metodo = 'gradient'
        justificacion = 'Heurística por defecto: gradiente.'

    return {'method': metodo, 'rationale': justificacion}


# Alias de compatibilidad
def recommend(meta: Dict[str, Any]) -> Dict[str, Any]:
    return recomendar_metodo(meta)
