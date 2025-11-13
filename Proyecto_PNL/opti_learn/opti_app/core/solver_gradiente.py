from __future__ import annotations

from typing import Dict, List, Any, Optional
import numpy as np

from .analyzer import build_sympy_functions, construir_funciones_numericas_sympy


def resolver_descenso_gradiente(
    expresion_objetivo: str,
    nombres_variables: List[str],
    x_inicial: Optional[List[float]] = None,
    tolerancia: float = 1e-6,
    max_iteraciones: int = 200,
) -> Dict[str, Any]:
    f_num, grad_num = construir_funciones_numericas_sympy(expresion_objetivo, nombres_variables)
    n_dim = len(nombres_variables)
    x_vec = np.zeros(n_dim, dtype=float) if x_inicial is None else np.array(x_inicial, dtype=float).reshape(n_dim)

    def valor_funcion(xv: np.ndarray) -> float:
        return float(np.array(f_num(xv), dtype=float))

    def valor_gradiente(xv: np.ndarray) -> np.ndarray:
        return np.array(grad_num(xv), dtype=float).reshape(n_dim)

    iteraciones: List[Dict[str, Any]] = []
    c_armijo = 1e-4
    factor_reduccion = 0.5
    f_k = valor_funcion(x_vec)
    for k in range(max_iteraciones):
        grad_k = valor_gradiente(x_vec)
        norma_grad = float(np.linalg.norm(grad_k))
        if norma_grad < tolerancia:
            iteraciones.append({'k': k, 'x_k': x_vec.tolist(), 'f_k': f_k, 'grad_norm': norma_grad, 'step': 0.0, 'notes': 'Convergencia por gradiente'})
            break

        # Backtracking Armijo
        alpha = 1.0
        while True:
            x_nuevo = x_vec - alpha * grad_k
            f_nuevo = valor_funcion(x_nuevo)
            if f_nuevo <= f_k - c_armijo * alpha * norma_grad * norma_grad:
                break
            alpha *= factor_reduccion
            if alpha < 1e-12:
                break

        iteraciones.append({'k': k, 'x_k': x_vec.tolist(), 'f_k': f_k, 'grad_norm': norma_grad, 'step': float(alpha)})
        x_vec = x_nuevo
        f_k = f_nuevo

        if abs(iteraciones[-1]['f_k'] - f_k) < tolerancia * (1.0 + abs(f_k)):
            iteraciones.append({'k': k+1, 'x_k': x_vec.tolist(), 'f_k': f_k, 'grad_norm': float(np.linalg.norm(valor_gradiente(x_vec))), 'step': 0.0, 'notes': 'Convergencia por cambio relativo'})
            break

    resultado = {
        'method': 'gradient',
        'status': 'ok',
        'x_star': x_vec.tolist(),
        'f_star': f_k,
        'iterations': iteraciones,
    }
    return resultado


# Alias de compatibilidad
def solve(objective_expr: str, variables: List[str], x0: Optional[List[float]] = None,
          tol: float = 1e-6, max_iter: int = 200) -> Dict[str, Any]:
    return resolver_descenso_gradiente(
        expresion_objetivo=objective_expr,
        nombres_variables=variables,
        x_inicial=x0,
        tolerancia=tol,
        max_iteraciones=max_iter,
    )
