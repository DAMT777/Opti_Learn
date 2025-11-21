from __future__ import annotations

from typing import Dict, Any, List
import sympy as sp


def _is_positive_semidefinite(matrix: sp.Matrix) -> bool:
    try:
        return all(v >= -1e-9 for v in matrix.eigenvals().keys())
    except Exception:
        return False


def resolver_qp(
    objective_expr: str,
    variables: List[str],
    constraints: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """
    Procedimiento educativo para un QP (sin solver numérico en el MVP).
    Devuelve un texto paso a paso basado en la estructura del problema.
    """
    constraints = constraints or []
    try:
        sym_vars = [sp.Symbol(v, real=True) for v in variables]
        expr = sp.sympify(objective_expr, locals={v.name: v for v in sym_vars})
        grad = [sp.diff(expr, v) for v in sym_vars]
        hess = sp.hessian(expr, sym_vars)
        is_quadratic = expr.is_polynomial() and expr.total_degree() == 2
        is_convex = _is_positive_semidefinite(hess)
    except Exception as exc:  # pragma: no cover - tolerancia a errores de parseo
        return {
            'method': 'qp',
            'status': 'error',
            'message': f'No se pudo analizar el QP: {exc}',
            'iterations': [],
            'plot_data': {},
            'explanation': 'No se pudo generar la interpretación educativa.',
        }

    pasos = [
        "Identificar la función objetivo cuadrática: escribirla como 0.5 xᵀ H x + cᵀ x.",
        "Verificar convexidad (H semidefinida positiva si se minimiza).",
        "Formular restricciones lineales y no negatividad.",
        "Construir Lagrangiana y condiciones KKT (estacionariedad, primal factible, dual factible, complementariedad).",
        "Montar tabla (fase 1) con variables originales, holguras y artificiales hasta eliminar artificiales.",
        "Con la base factible, reemplazar el objetivo real y continuar iteraciones (fase 2) hasta optimalidad.",
        "Leer solución óptima x* y evaluar f(x*).",
    ]
    restr_desc = "; ".join([f"{c.get('kind','ineq')}: {c.get('expr')}" for c in constraints]) or "Sin restricciones declaradas."
    explicacion = "\n".join([
        "Programa cuadrático (descripción educativa):",
        f"- Variables: {', '.join(variables) if variables else 'no especificadas'}.",
        f"- Objetivo: {objective_expr}.",
        f"- Gradiente: {grad}.",
        f"- Hessiano: {hess.tolist() if hasattr(hess, 'tolist') else hess}.",
        f"- Es cuadrática: {is_quadratic}. Convexa (mínimo asegurado si sí): {is_convex}.",
        f"- Restricciones: {restr_desc}",
        "",
        "Procedimiento sugerido (2 fases):",
        *[f"{i+1}) {p}" for i, p in enumerate(pasos)],
        "",
        "Nota: este MVP no resuelve numéricamente el QP; se muestra la guía para el alumno.",
    ])

    return {
        'method': 'qp',
        'status': 'educational_only',
        'message': 'Procedimiento educativo generado. Solver numérico no incluido en el MVP.',
        'iterations': [],
        'plot_data': {},
        'explanation': explicacion,
        'x_star': None,
        'f_star': None,
    }


# Alias de compatibilidad
def solve_qp(*args, **kwargs) -> Dict[str, Any]:
    return resolver_qp(*args, **kwargs)
