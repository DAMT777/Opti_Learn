from __future__ import annotations

from typing import Dict, List, Any, Optional
import math
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


def _build_curve_1d(f_num, puntos: np.ndarray, resolution: int = 200):
    xs = puntos[:, 0]
    x_min, x_max = float(xs.min()), float(xs.max())
    x_center = float((x_min + x_max) / 2.0)
    range_x = max(x_max - x_min, 1e-3)
    max_abs_x = float(np.max(np.abs(xs))) if xs.size else 0.0
    half = max(range_x * 0.75, max_abs_x + 3.0, 6.0)
    x_lin = np.linspace(x_center - half, x_center + half, resolution)
    y_vals = []
    for xv in x_lin:
        try:
            y_vals.append(float(np.array(f_num([xv]), dtype=float)))
        except Exception:
            y_vals.append(float('nan'))
    return {'x': x_lin.tolist(), 'f': y_vals}


def _argmin_step_along_gradient(valor_funcion, x_vec, grad_vec, alpha_ini=1.0, tol=1e-6):
    """
    Aproxima alpha_k = argmin_{alpha>0} f(x_k - alpha * grad f(x_k))
    usando b�squeda dorada sobre una direcci�n de descenso.
    """
    norma = float(np.linalg.norm(grad_vec))
    if norma < 1e-12:
        fk = valor_funcion(x_vec)
        return 0.0, fk, [{'alpha': 0.0, 'f_value': fk, 'reason': 'zero_gradient', 'accepted': True}]

    def phi(alpha: float) -> float:
        if alpha <= 0:
            return valor_funcion(x_vec)
        return valor_funcion(x_vec - alpha * grad_vec)

    phi0 = phi(0.0)
    alpha_right = alpha_ini
    phi_right = phi(alpha_right)
    shrink_steps = 0
    while phi_right >= phi0 and alpha_right > 1e-12 and shrink_steps < 20:
        alpha_right *= 0.5
        phi_right = phi(alpha_right)
        shrink_steps += 1

    if phi_right >= phi0:
        return 0.0, phi0, [{'alpha': 0.0, 'f_value': phi0, 'reason': 'no_descent', 'accepted': True}]

    alpha_high = alpha_right * 2.0
    phi_high = phi(alpha_high)
    expand_steps = 0
    while phi_high < phi_right and alpha_high < 50.0 and expand_steps < 20:
        alpha_right = alpha_high
        phi_right = phi_high
        alpha_high *= 2.0
        phi_high = phi(alpha_high)
        expand_steps += 1

    left = 0.0
    right = min(alpha_high, 50.0)
    golden = (math.sqrt(5) - 1.0) / 2.0
    c = right - golden * (right - left)
    d = left + golden * (right - left)
    fc = phi(c)
    fd = phi(d)
    trace: List[Dict[str, Any]] = []
    for _ in range(60):
        if abs(right - left) < tol:
            break
        if fc < fd:
            right = d
            d = c
            fd = fc
            c = right - golden * (right - left)
            fc = phi(c)
        else:
            left = c
            c = d
            fc = fd
            d = left + golden * (right - left)
            fd = phi(d)
        mid = (left + right) / 2.0
        trace.append({'alpha': float(mid), 'f_value': float(phi(mid)), 'accepted': False})

    alpha_opt = (left + right) / 2.0
    f_opt = phi(alpha_opt)
    trace.append({'alpha': float(alpha_opt), 'f_value': float(f_opt), 'reason': 'argmin', 'accepted': True})
    return float(alpha_opt), float(f_opt), trace


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
    f_k = valor_funcion(x_vec)
    for k in range(max_iteraciones):
        grad_k = valor_gradiente(x_vec)
        norma_grad = float(np.linalg.norm(grad_k))
        if norma_grad < tolerancia:
            iteraciones.append({
                'k': k,
                'x_k': x_vec.tolist(),
                'f_k': f_k,
                'grad_norm': norma_grad,
                'step': 0.0,
                'alpha': 0.0,
                'grad': grad_k.tolist(),
                'line_search': [],
                'notes': 'Convergencia por gradiente',
            })
            break

        alpha_opt, f_nuevo, line_search_trace = _argmin_step_along_gradient(
            valor_funcion, x_vec, grad_k, alpha_ini=1.0, tol=tolerancia
        )
        x_nuevo = x_vec - alpha_opt * grad_k

        iteraciones.append({
            'k': k,
            'x_k': x_vec.tolist(),
            'f_k': f_k,
            'grad_norm': norma_grad,
            'step': float(alpha_opt),
            'alpha': float(alpha_opt),
            'grad': grad_k.tolist(),
            'line_search': line_search_trace,
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
                'line_search': [],
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

    plot_data: Dict[str, Any] = {'dimension': n_dim, 'allow_plots': n_dim <= 2}
    point_array = np.stack(points) if points else np.empty((0, n_dim))
    fx_curve = {'iter': list(range(len(fx_values))), 'f': fx_values}
    if n_dim == 1 and point_array.size > 0:
        curve = _build_curve_1d(f_num, point_array)
        plot_data = {
            'dimension': n_dim,
            'allow_plots': True,
            'func_1d': curve,
            'trajectory': {
                'x': [float(p[0]) for p in point_array],
                'f': fx_values,
            },
            'fx_curve': fx_curve,
        }
    elif n_dim == 2 and len(points) >= 1:
        mesh = _build_mesh(f_num, point_array if len(points) >= 2 else np.vstack([point_array, point_array]))
        segments = []
        for i in range(len(point_array) - 1):
            segments.append({
                'x': [float(point_array[i, 0]), float(point_array[i + 1, 0])],
                'y': [float(point_array[i, 1]), float(point_array[i + 1, 1])],
            })
        plot_data = {
            'dimension': n_dim,
            'allow_plots': True,
            'mesh': mesh,
            'trajectory': {
                'x': [float(p[0]) for p in point_array],
                'y': [float(p[1]) for p in point_array],
                'f': fx_values,
            },
            'segments': segments,
            'fx_curve': fx_curve,
        }
    else:
        plot_data['reason'] = 'high_dimension'

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
