from __future__ import annotations

from typing import Dict, Any, List

# Importar el solver numérico
try:
    from .solver_qp_numerical import solve_qp as solve_qp_numerical
    SOLVER_NUMERICO_DISPONIBLE = True
except ImportError:
    SOLVER_NUMERICO_DISPONIBLE = False
    solve_qp_numerical = None


def resolver_qp(
    objective_expr: str,
    variables: List[str],
    constraints: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """
    Resuelve un problema de Programación Cuadrática (QP) con explicación educativa paso a paso.
    
    Utiliza el solver completo que implementa el método de dos fases con condiciones KKT.
    """
    constraints = constraints or []
    
    # Usar el solver numérico si está disponible
    if SOLVER_NUMERICO_DISPONIBLE:
        try:
            return solve_qp_numerical(objective_expr, variables, constraints)
        except Exception as e:
            # Si el solver numérico falla, usar fallback educativo
            return _fallback_educational_qp(objective_expr, variables, constraints, error=str(e))
    else:
        return _fallback_educational_qp(objective_expr, variables, constraints)


def _fallback_educational_qp(
    objective_expr: str,
    variables: List[str],
    constraints: List[Dict[str, Any]],
    error: str = None
) -> Dict[str, Any]:
    """
    Versión educativa simplificada cuando el solver completo no está disponible o falla.
    """
    import sympy as sp
    
    try:
        sym_vars = [sp.Symbol(v, real=True) for v in variables]
        expr = sp.sympify(objective_expr, locals={v.name: v for v in sym_vars})
        grad = [sp.diff(expr, v) for v in sym_vars]
        hess = sp.hessian(expr, sym_vars)
        is_quadratic = expr.is_polynomial() and sp.degree(expr) == 2
        
        # Verificar convexidad
        try:
            eigenvals = list(hess.eigenvals().keys())
            is_convex = all(float(v) >= -1e-9 for v in eigenvals)
        except:
            is_convex = False
            
    except Exception as exc:
        return {
            'method': 'qp',
            'status': 'error',
            'message': f'No se pudo analizar el QP: {exc}',
            'explanation': 'Error al parsear la función objetivo.',
        }

    pasos_educativos = [
        "1. **Identificar la forma estándar QP:** Escribir como min/max f(X) = C·X + X^T·D·X sujeto a A·X ≤ b, X ≥ 0",
        "2. **Extraer matrices:** Identificar matriz cuadrática D, vector lineal C, matriz de restricciones A y vector b",
        "3. **Verificar convexidad:** Calcular eigenvalores de D (positivos para minimización, negativos para maximización)",
        "4. **Construir sistema KKT:** Formular condiciones de Karush-Kuhn-Tucker",
        "5. **Fase I (factibilidad):** Agregar variables artificiales y usar Simplex para encontrar solución factible",
        "6. **Fase II (optimización):** Eliminar artificiales y optimizar función objetivo original",
        "7. **Verificar optimalidad:** Comprobar que se cumplen todas las condiciones KKT",
        "8. **Interpretar solución:** Evaluar X* en la función objetivo para obtener z*"
    ]
    
    restr_desc = "; ".join([f"{c.get('kind','ineq')}: {c.get('expr')}" for c in constraints]) or "Sin restricciones declaradas."
    
    explicacion_partes = [
        "# PROGRAMACIÓN CUADRÁTICA (QP) - Guía Educativa\n",
        f"## Problema Planteado\n",
        f"- **Variables:** {', '.join(variables) if variables else 'no especificadas'}\n",
        f"- **Función objetivo:** {objective_expr}\n",
        f"- **Restricciones:** {restr_desc}\n",
        f"\n## Análisis Matemático\n",
        f"- **Gradiente:** ∇f = {grad}\n",
        f"- **Hessiano (matriz D):**\n```\n{hess}\n```\n",
        f"- **Es cuadrática:** {'Sí' if is_quadratic else 'No'}\n",
        f"- **Es convexa:** {'Sí' if is_convex else 'No'}\n",
        f"\n## Procedimiento de Solución (Método de Dos Fases)\n",
    ]
    
    for paso in pasos_educativos:
        explicacion_partes.append(f"{paso}\n")
    
    explicacion_partes.extend([
        "\n## Notas Importantes\n",
        "- Para problemas QP convexos, el método garantiza encontrar el óptimo global\n",
        "- Las condiciones KKT son necesarias y suficientes para optimalidad\n",
        "- El método de dos fases es robusto y aplicable a cualquier problema QP\n",
        "\n## Estado del Solver\n"
    ])
    
    if error:
        explicacion_partes.append(f"⚠️ **Nota:** El solver numérico encontró un error: {error}\n")
        explicacion_partes.append("Se muestra la guía educativa para resolver manualmente.\n")
    else:
        explicacion_partes.append("📚 **Nota:** Mostrando guía educativa del método.\n")
    
    return {
        'method': 'qp',
        'status': 'educational_guide',
        'message': 'Guía educativa del método QP generada.',
        'explanation': "".join(explicacion_partes),
        'steps': pasos_educativos,
        'x_star': None,
        'f_star': None,
    }


# Alias de compatibilidad
def solve_qp(*args, **kwargs) -> Dict[str, Any]:
    return resolver_qp(*args, **kwargs)
