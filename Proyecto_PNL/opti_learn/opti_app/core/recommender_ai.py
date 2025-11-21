from __future__ import annotations

from typing import Dict, Any


def recomendar_metodo(metadatos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Selección de método según la guía:
    - Objetivo cuadrático + restricciones lineales -> QP
    - Solo igualdades -> Lagrange
    - Desigualdades (con o sin igualdades) -> KKT
    - Sin restricciones -> Gradiente
    - Si el usuario solo pide derivar/analizar -> Cálculo diferencial
    """
    hay_igualdades = bool(metadatos.get('has_equalities'))
    hay_desigualdades = bool(metadatos.get('has_inequalities'))
    es_cuadratico = bool(metadatos.get('is_quadratic'))
    derivative_only = bool(metadatos.get('derivative_only'))

    if derivative_only:
        return {
            'method': 'differential',
            'rationale': 'Solo requiere derivadas/gradiente/Hessiano: aplicar cálculo diferencial.',
        }

    if es_cuadratico and (hay_igualdades or hay_desigualdades):
        return {
            'method': 'qp',
            'rationale': 'Función objetivo cuadrática con restricciones (asumidas lineales): usar Programación Cuadrática (QP).',
        }
    if hay_desigualdades:
        return {
            'method': 'kkt',
            'rationale': 'Hay restricciones de desigualdad (y posibles igualdades): aplicar condiciones KKT.',
        }
    if hay_igualdades:
        return {
            'method': 'lagrange',
            'rationale': 'Solo restricciones de igualdad: método de Lagrange.',
        }
    return {
        'method': 'gradient',
        'rationale': 'Problema sin restricciones: gradiente/descenso por gradiente.',
    }


# Alias de compatibilidad
def recommend(meta: Dict[str, Any]) -> Dict[str, Any]:
    return recomendar_metodo(meta)
