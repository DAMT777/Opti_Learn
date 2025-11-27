from __future__ import annotations

from typing import Dict, Any


def recomendar_metodo(m: Dict[str, Any]) -> Dict[str, Any]:
    """
    Selecciona el metodo segun reglas formales y orden explicitado en el arbol de decision.
    
    ORDEN DE REGLAS (v3.2.0):
    1. Proceso iterativo → GRADIENT
    2. Restricciones no lineales → KKT
    3. Función cuadrática + restricciones lineales + MEZCLA de igualdades Y desigualdades → QP
    4. SOLO igualdades (sin desigualdades) → LAGRANGE
    5. Desigualdades → KKT
    6. Sin restricciones → DIFFERENTIAL o GRADIENT
    """
    iterativo = bool(m.get('iterative_process'))
    eq = bool(m.get('has_equalities'))
    ineq = bool(m.get('has_inequalities'))
    cuadratico = bool(m.get('is_quadratic'))
    lineal = bool(m.get('constraints_are_linear'))
    deriv = bool(m.get('derivative_only'))
    method_hint = (m.get('method_hint') or '').strip()
    restricciones = bool(m.get('has_constraints') or eq or ineq)

    # REGLA 1: Iterativo → Gradiente
    if iterativo:
        return {'method': 'gradient', 'rationale': 'Proceso iterativo explicito (paso α, iteraciones).'}

    # REGLA 2: Restricciones no lineales → KKT
    if restricciones and not lineal:
        return {'method': 'kkt', 'rationale': 'Restricciones no lineales detectadas (cuadrados, productos de variables, raices).'}

    # REGLA 3: QP (cuadrática + lineal + MEZCLA de igualdades Y desigualdades)
    if cuadratico and lineal and eq and ineq:
        return {'method': 'qp', 'rationale': 'Funcion objetivo cuadratica con restricciones lineales, combinando igualdades y desigualdades (Programacion Cuadratica).'}

    # REGLA 4: SOLO igualdades (sin desigualdades) → Lagrange
    if eq and not ineq:
        return {'method': 'lagrange', 'rationale': 'Solo restricciones de igualdad (sin desigualdades), aplicar multiplicadores de Lagrange.'}

    # REGLA 5: Desigualdades → KKT
    if ineq:
        return {'method': 'kkt', 'rationale': 'Restricciones con desigualdades detectadas, requiere condiciones KKT.'}

    # REGLA 6: Sin restricciones
    if not restricciones:
        if deriv:
            return {'method': 'differential', 'rationale': 'Sin restricciones, buscar puntos criticos mediante derivadas.'}
        return {'method': 'gradient', 'rationale': 'Sin restricciones, optimizacion mediante gradiente descendente.'}

    # Fallback
    return {'method': 'gradient', 'rationale': 'Caso por defecto: metodo del gradiente.'}


# Alias de compatibilidad
def recommend(meta: Dict[str, Any]) -> Dict[str, Any]:
    return recomendar_metodo(meta)
