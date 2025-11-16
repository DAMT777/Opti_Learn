from __future__ import annotations

from typing import Dict, List, Any, Optional
import numpy as np

from .analyzer import build_sympy_functions, construir_funciones_numericas_sympy


def _build_mesh(f_num, puntos: np.ndarray, resolution: int = 60):
    if puntos.size == 0:
        return None
    xs = puntos[:, 0]
    ys = puntos[:, 1]
    x_min, x_max = float(xs.min()), float(xs.max())
    y_min, y_max = float(ys.min()), float(ys.max())
    x_center = float((x_min + x_max) / 2.0)
    y_center = float((y_min + y_max) / 2.0)
    range_x = max(x_max - x_min, 1e-3)
    range_y = max(y_max - y_min, 1e-3)
    max_abs_x = float(np.max(np.abs(xs)))
    max_abs_y = float(np.max(np.abs(ys)))
    half_x = max(range_x * 0.75, max_abs_x + 5.0, 12.0)
    half_y = max(range_y * 0.75, max_abs_y + 5.0, 12.0)
    x_lin = np.linspace(x_center - half_x, x_center + half_x, resolution)
    y_lin = np.linspace(y_center - half_y, y_center + half_y, resolution)
    xv, yv = np.meshgrid(x_lin, y_lin)
    coords = np.stack([xv.ravel(), yv.ravel()], axis=-1)
    z_vals = []
    for coord in coords:
        try:
            z = float(np.array(f_num(coord), dtype=float))
        except Exception:
            z = float('nan')
        z_vals.append(z)
    zv = np.array(z_vals, dtype=float).reshape(xv.shape)
    return {
        'x': x_lin.tolist(),
        'y': y_lin.tolist(),
        'z': zv.tolist(),
    }


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

        alpha = 1.0
        while True:
            x_nuevo = x_vec - alpha * grad_k
            f_nuevo = valor_funcion(x_nuevo)
            if f_nuevo <= f_k - c_armijo * alpha * norma_grad * norma_grad:
                break
            alpha *= factor_reduccion
            if alpha < 1e-12:
                break

        iteraciones.append({
            'k': k,
            'x_k': x_vec.tolist(),
            'f_k': f_k,
            'grad_norm': norma_grad,
            'step': float(alpha),
            'alpha': float(alpha),
            'grad': valor_gradiente(x_vec).tolist(),
        })
        x_vec = x_nuevo
        f_k = f_nuevo

        if abs(iteraciones[-1]['f_k'] - f_k) < tolerancia * (1.0 + abs(f_k)):
            grad_fin = valor_gradiente(x_vec)
            iteraciones.append({
                'k': k+1,
                'x_k': x_vec.tolist(),
                'f_k': f_k,
                'grad_norm': float(np.linalg.norm(grad_fin)),
                'step': 0.0,
                'alpha': 0.0,
                'grad': grad_fin.tolist(),
                'notes': 'Convergencia por cambio relativo',
            })
            break

    trajectory = []
    fx_values = []
    points = []
    for it in iteraciones:
        xk = it.get('x_k') or []
        if len(xk) == n_dim:
            points.append(np.array(xk, dtype=float))
            trajectory.append({'x': float(xk[0]), 'y': float(xk[1]) if n_dim > 1 else float(xk[0]), 'f': float(it.get('f_k', 0.0))})
            fx_values.append(float(it.get('f_k', 0.0)))

    plot_data: Dict[str, Any] = {}
    if n_dim == 2 and len(points) >= 2:
        point_array = np.stack(points)
        mesh = _build_mesh(f_num, point_array)
        segments = []
        for i in range(len(point_array) - 1):
            segments.append({
                'x': [float(point_array[i, 0]), float(point_array[i + 1, 0])],
                'y': [float(point_array[i, 1]), float(point_array[i + 1, 1])],
            })
        fx_curve = {'iter': list(range(len(fx_values))), 'f': fx_values}
        plot_data = {
            'mesh': mesh,
            'trajectory': {
                'x': [float(p[0]) for p in point_array],
                'y': [float(p[1]) for p in point_array],
                'f': fx_values,
            },
            'segments': segments,
            'fx_curve': fx_curve,
        }

    resultado = {
        'method': 'gradient',
        'status': 'ok',
        'x_star': x_vec.tolist(),
        'f_star': f_k,
        'iterations': iteraciones,
        'plot_data': plot_data,
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
