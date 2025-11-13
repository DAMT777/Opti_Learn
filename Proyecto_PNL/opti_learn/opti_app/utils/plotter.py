from __future__ import annotations

from typing import List, Dict, Any, Optional

try:
    import plotly.graph_objects as go
except Exception:  # pragma: no cover - dependencia opcional
    go = None


def contorno_con_trayectoria(nombre_funcion: str, variables: List[str], iteraciones: List[Dict[str, Any]]):
    if go is None:
        return None
    if len(variables) != 2:
        return None
    xs = [it['x_k'][0] for it in iteraciones]
    ys = [it['x_k'][1] for it in iteraciones]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=ys, mode='lines+markers', name='Trayectoria'))
    fig.update_layout(title=f"Trayectoria — {nombre_funcion}")
    return fig


# Alias de compatibilidad
def contour_with_path(func_name: str, vars: List[str], iterations: List[Dict[str, Any]]):
    return contorno_con_trayectoria(func_name, vars, iterations)
