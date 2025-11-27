import json
import ast
import asyncio
import logging
import re
from typing import Any, Dict, List

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from .models import ChatSession, ChatMessage
from .core import (
    analyzer,
    message_parser,
    recommender_ai,
    scope_guard,
    solver_cuadratico,
    solver_gradiente,
    solver_kkt,
    solver_lagrange,
)
from .ai import groq_service
import sympy as sp

logger = logging.getLogger(__name__)

def _fmt_number(value: Any) -> str:
    try:
        if isinstance(value, (list, tuple)):
            return "[" + ", ".join(_fmt_number(v) for v in value) + "]"
        return f"{float(value):.8f}"
    except Exception:
        return str(value)


def _fmt_number_latex(value: Any) -> str:
    try:
        if isinstance(value, (list, tuple)):
            inner = ", ".join(_fmt_number_latex(v) for v in value)
            return r"\left[" + inner + r"\right]"
        return f"{float(value):.8f}"
    except Exception:
        return str(value)


def _symbolic_details(expr: str, variables: List[str]) -> Dict[str, Any]:
    details: Dict[str, Any] = {'latex_expr': expr.replace("*", r"\ast "), 'grad_components': []}
    try:
        local_symbols = {name: sp.Symbol(name, real=True) for name in variables}
        sym = sp.sympify(expr, locals=local_symbols)
        details['latex_expr'] = sp.latex(sym)
        details['grad_components'] = [sp.latex(sp.diff(sym, local_symbols[v])) for v in variables]
    except Exception:
        details['grad_components'] = [f"\\partial f / \\partial {v}" for v in variables]
    return details


def build_gradient_report(
    problema: Dict[str, Any],
    meta: Dict[str, Any],
    resultado: Dict[str, Any],
    recomendacion: Dict[str, Any],
    parametros: Dict[str, Any],
    symbolic: Dict[str, Any],
) -> str:
    variables = meta.get('variables') or problema.get('variables') or []
    latex_expr = symbolic.get('latex_expr')
    x0 = parametros.get('x0')
    tol = parametros.get('tol', 1e-6)
    max_iter = parametros.get('max_iter', 200)
    razon = recomendacion.get('rationale', 'Gradiente descendente aplica al no haber restricciones.')
    iteraciones = resultado.get('iterations', [])

    lines = []
    lines.append("## Problema")
    lines.append(f"- Función objetivo: $f({', '.join(variables)}) = {latex_expr}$")
    if x0 is not None:
        lines.append(f"- Punto inicial $x_0 = {_fmt_number_latex(x0)}$")
    lines.append("")
    lines.append("## Análisis")
    lines.append(f"- Variables detectadas: {variables}")
    lines.append(f"- Restricciones: eq={meta.get('has_equalities')} | ineq={meta.get('has_inequalities')}")
    lines.append(f"- Método recomendado: **{recomendacion.get('method')}** → {razon}")
    lines.append("")
    lines.append("## Procedimiento")
    grad_components = symbolic.get('grad_components') or []
    if grad_components:
        grad_str = ", ".join(grad_components)
        lines.append(f"- Gradiente simbólico preliminar: $\\nabla f(x) = [{grad_str}]$.")
    lines.append("1. Calcular el gradiente $\\nabla f(x)$ y evaluar su norma.")
    lines.append("2. Determinar $\\alpha_k$ mediante búsqueda de línea (Armijo) usando el gradiente actual.")
    lines.append("3. Actualizar $x_{k+1} = x_k - \\alpha_k \\nabla f(x_k)$.")
    lines.append(f"4. Repetir hasta que $\\|\\nabla f(x_k)\\| < {tol}$ o $k \\ge {max_iter}$.")
    lines.append("")

    if iteraciones:
        grad_components = symbolic.get('grad_components') or []
        if grad_components:
            grad_str = ", ".join(grad_components)
            lines.append(f"- Gradiente simbólico: $\\nabla f(x) = [{grad_str}]$.")
        lines.append("### Recordatorio: Gradiente y tamaño de paso")
        lines.append("- $\\nabla f(x) = [\\partial f / \\partial x_1, \\ldots, \\partial f / \\partial x_n]$.")
        lines.append("- Para cada iteración se muestra el vector gradiente completo y el valor de $\\alpha_k$.")
        lines.append("")
        lines.append("## Iteraciones (primeras 10)")
        lines.append('<table class="iteration-table">')
        lines.append("<thead><tr><th>$k$</th><th>$x_k$</th><th>$f(x_k)$</th><th>$\\|\\nabla f\\|$</th><th>$\\nabla f(x_k)$</th><th>$\\alpha_k$</th></tr></thead>")
        lines.append("<tbody>")
        for it in iteraciones[:10]:
            grad_display = it.get('grad')
            grad_latex = _fmt_number_latex(grad_display) if grad_display is not None else "-"
            alpha_val = _fmt_number_latex(it.get('alpha', it.get('step')))
            lines.append(
                "<tr>"
                f"<td>{it.get('k')}</td>"
                f"<td>$ {_fmt_number_latex(it.get('x_k'))} $</td>"
                f"<td>$ {_fmt_number_latex(it.get('f_k'))} $</td>"
                f"<td>$ {_fmt_number_latex(it.get('grad_norm'))} $</td>"
                f"<td>$ {grad_latex} $</td>"
                f"<td>$ {alpha_val} $</td>"
                "</tr>"
            )
        if len(iteraciones) > 10:
            lines.append(
                f"<tr><td colspan='6'>… (total {len(iteraciones)} iteraciones)</td></tr>"
            )
        lines.append("</tbody></table>")
        lines.append("")

    lines.append("## Resultado")
    lines.append(f"- Punto óptimo verificado: ${_fmt_number_latex(resultado.get('x_star'))}$")
    lines.append(f"- Valor mínimo: ${_fmt_number_latex(resultado.get('f_star'))}$")
    lines.append(f"- Iteraciones ejecutadas: {len(iteraciones)}")
    lines.append("")
    lines.append("## Interpretación")
    lines.append(
        "El gradiente descendente reduce consistentemente la norma $\\|\\nabla f(x_k)\\|$ hasta que se aproxima a cero; "
        "esto indica que el punto alcanzado satisface las condiciones de estacionariedad y es el mínimo global en este caso cuadrático. "
        "La secuencia de $\\alpha_k$ evidencia cómo la búsqueda de línea modera el descenso para evitar divergencias, "
        "y las últimas iteraciones muestran pasos muy pequeños, confirmando la convergencia."
    )
    return "\n".join(lines)


def build_pre_solution_analysis(
    problema: Dict[str, Any],
    meta: Dict[str, Any],
    recomendacion: Dict[str, Any],
    parametros: Dict[str, Any],
    symbolic: Dict[str, Any],
) -> str:
    variables = meta.get('variables') or problema.get('variables') or []
    latex_expr = symbolic.get('latex_expr') or problema.get('objective_expr', '').replace("*", r"\ast ")
    lines = []
    lines.append("## Análisis previo")
    lines.append(f"- Se detectan {len(variables)} variables: {variables}.")
    lines.append(f"- Función candidata: $f({', '.join(variables)}) = {latex_expr}$.")
    lines.append(f"- Restricciones: eq={meta.get('has_equalities')} | ineq={meta.get('has_inequalities')} (no se resolverán restricciones en esta demostración).")
    grad_components = symbolic.get('grad_components') or []
    if grad_components:
        grad_str = ", ".join(grad_components)
        lines.append(f"- Gradiente simbólico: $\\nabla f(x) = [{grad_str}]$.")
    lines.append("")
    lines.append("### Decisión del método")
    lines.append(f"- Recomendación automática: **{recomendacion.get('method')}** → {recomendacion.get('rationale')}")
    lines.append("")
    lines.append("### Estrategia paso a paso")
    lines.append("1. Calcular el gradiente simbólico y numérico $\\nabla f(x)$.")
    lines.append("2. Evaluar la norma del gradiente para diagnosticar la dirección de descenso.")
    lines.append("3. Seleccionar tamaño de paso $\\alpha_k$ mediante Armijo (line search).")
    lines.append("4. Actualizar $x_{k+1} = x_k - \\alpha_k \\nabla f(x_k)$.")
    lines.append(f"5. Repetir hasta que $\\|\\nabla f(x_k)\\| < {parametros.get('tol', 1e-6)}$ o $k \\ge {parametros.get('max_iter', 200)}$.")
    lines.append("")
    lines.append("Con este análisis se procede a ejecutar el solver local…")
    return "\n".join(lines)


def _merge_payload(primary: Dict[str, Any] | None, fallback: Dict[str, Any] | None) -> Dict[str, Any] | None:
    if primary is None:
        return fallback
    if fallback is None:
        return primary

    def _needs_value(value):
        return value is None or value == '' or value == [] or value == {}

    keys = [
        'objective_expr',
        'variables',
        'constraints',
        'constraints_raw',
        'x0',
        'tol',
        'max_iter',
        'method',
        'method_hint',
        'derivative_only',
    ]
    for key in keys:
        if _needs_value(primary.get(key)) and not _needs_value(fallback.get(key)):
            primary[key] = fallback.get(key)
    return primary


def _coerce_numeric_list(values: Any, label: str) -> List[float]:
    if values is None:
        raise ValueError(f"El campo {label} es obligatorio.")
    if isinstance(values, (int, float)):
        return [float(values)]
    if not isinstance(values, (list, tuple)):
        raise ValueError(f"{label} debe ser una lista de números reales.")
    cleaned: List[float] = []
    for item in values:
        if item is None or (isinstance(item, str) and not item.strip()):
            raise ValueError(f"{label} contiene valores vacíos; proporcione todos los componentes numéricos.")
        try:
            cleaned.append(float(item))
        except Exception:
            raise ValueError(f"Cada componente de {label} debe ser numérico. Revisa: {item!r}")
    return cleaned


def _validate_payload_for_method(method: str, payload: Dict[str, Any], meta: Dict[str, Any]) -> None:
    objective = payload.get('objective_expr')
    if not objective:
        raise ValueError(
            "No se pudo identificar la función objetivo. Escribe algo como f(x,y) = ... o 'minimizar ...' para continuar."
        )

    constraints = meta.get('constraints_normalized') or []
    if method == 'gradient':
        x0 = payload.get('x0')
        variables = meta.get('variables') or []
        if not variables:
            raise ValueError(
                "No se detectaron variables para construir el punto inicial. "
                "Especifica las variables o escribe la función objetivo en términos de x, y, etc."
            )
        if x0 is None:
            auto = [0.0 for _ in variables]
            payload.setdefault('_auto_notes', []).append(
                f"Se asumió x0 = {auto} como punto inicial (no se proporcionó en el enunciado)."
            )
            payload['x0'] = auto
            x0 = auto
        cleaned_x0 = _coerce_numeric_list(x0, 'x0')
        if variables and len(cleaned_x0) != len(variables):
            raise ValueError(
                f"La dimensión de x0 ({len(x0)}) no coincide con el número de variables detectadas ({len(variables)})."
            )
        payload['x0'] = cleaned_x0
    if method == 'lagrange':
        eqs = [c for c in constraints if c.get('kind') == 'eq']
        if not eqs:
            raise ValueError(
                "El método de Lagrange requiere al menos una restricción de igualdad g(x)=0. "
                "Describe las restricciones como g(x)=0 o expr = 0."
            )
    if method == 'kkt':
        ineqs = [c for c in constraints if c.get('kind') in ('le', 'ge')]
        if not ineqs:
            raise ValueError(
                "Para usar condiciones KKT debes incluir restricciones de desigualdad (≤ o ≥). "
                "Indica expresiones como h(x) <= 0."
            )


def _format_bullets(data: Any) -> str:
    if data is None:
        return ''
    if isinstance(data, dict):
        return "\n".join([f"- {k}: {v}" for k, v in data.items()])
    if isinstance(data, list):
        return "\n".join([f"- {item}" for item in data])
    return str(data)


def _extract_payload_with_ai(text: str) -> Dict[str, Any] | None:
    try:
        messages = [
            {
                "role": "system",
                "content": (
                    "Eres el asistente de OptiLearn. Recibes problemas de Programacion No Lineal en lenguaje natural. "
                    "Debes extraer informacion estructurada en JSON.\n\n"
                    "TAREAS:\n"
                    "1) Escribir la funcion objetivo en notacion SymPy (usa ** para potencias, * para productos).\n"
                    "2) Listar las variables. Si no se declaran, deducelas de la funcion.\n"
                    "3) Extraer TODAS las restricciones. Separa cotas dobles en DOS restricciones:\n"
                    "   - 'A >= 20' → {\"kind\": \"ge\", \"expr\": \"(A) - (20)\"}\n"
                    "   - '10 <= F <= 40' → DOS: {\"kind\": \"ge\", \"expr\": \"(F) - (10)\"} Y {\"kind\": \"le\", \"expr\": \"(F) - (40)\"}\n"
                    "   - 'A + B + F = 100' → {\"kind\": \"eq\", \"expr\": \"(A + B + F) - (100)\"}\n"
                    "4) Detectar el metodo aplicando ESTAS REGLAS EN ORDEN:\n"
                    "   REGLA 1: Menciona proceso iterativo → gradient\n"
                    "   REGLA 2: Restricciones NO LINEALES → kkt\n"
                    "   REGLA 3: Funcion CUADRATICA + restricciones LINEALES + MEZCLA (>=1 igualdad Y >=1 desigualdad) → qp\n"
                    "   REGLA 4: SOLO igualdades → lagrange\n"
                    "   REGLA 5: Hay desigualdades → kkt\n"
                    "   REGLA 6: Sin restricciones → gradient o differential\n"
                    "   CRITICO QP: Requiere al menos UNA igualdad Y al menos UNA desigualdad. Solo igualdades → lagrange. Solo desigualdades → kkt.\n\n"
                    "CAMPOS JSON:\n"
                    "- objective_expr: string\n"
                    "- variables: [lista de strings]\n"
                    "- constraints: [lista de {kind: eq|le|ge, expr: string}]\n"
                    "- x0, tol, max_iter: opcionales\n"
                    "- method: gradient|lagrange|kkt|qp|differential\n"
                    "- method_hint: mismo valor que method\n"
                    "- derivative_only: bool\n\n"
                    "Responde SOLO con el JSON, sin texto adicional."
                ),
            },
            {"role": "user", "content": text},
        ]
        raw = groq_service.chat_completion(messages)
        if not raw:
            logger.warning("AI extractor returned empty response")
            return None
        raw_clean = raw.strip()
        # Si la respuesta no contiene llaves o parece un bloque LaTeX, abortamos para no romper.
        if "\\begin" in raw_clean or "\\frac" in raw_clean:
            logger.debug("AI extractor detected LaTeX-like response, skipping JSON parse.")
            return None
        if "```" in raw_clean and "json" not in raw_clean.lower():
            logger.debug("AI extractor response fenced but not JSON, skipping.")
            return None
        logger.info("AI raw completion: %s", raw_clean[:500])
        logger.debug("AI extractor raw response (first 500 chars): %s", raw_clean[:500])
        # Intentar extraer el bloque JSON aunque venga envuelto en texto/markdown
        candidate = raw_clean
        fenced = re.search(r"```json(.*?)```", raw_clean, flags=re.IGNORECASE | re.S)
        if fenced:
            candidate = fenced.group(1)
        else:
            start = raw_clean.find("{")
            end = raw_clean.rfind("}")
            if start != -1 and end != -1 and end > start:
                candidate = raw_clean[start:end + 1]
        candidate = candidate.strip("` \n\t")
        if not candidate.startswith(("{", "[")):
            logger.debug("AI extractor candidate is not JSON-like, skipping: %s", candidate[:80])
            return None
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            # Fallback: permitir dicts con comillas simples o claves sin comillas
            try:
                data = ast.literal_eval(candidate)
            except Exception:
                # Intento simple: reemplazar comillas simples por dobles
                fixed = candidate.replace("'", '"')
                data = json.loads(fixed)
        logger.debug("AI extractor parsed JSON: %s", candidate[:500])
        if 'method' not in data or not data.get('method'):
            data['method'] = data.get('method_hint')
        return data
    except Exception:
        logger.exception("AI extractor failed to build payload")
        return None


def _narrate_with_ai(payload: Dict[str, Any], meta: Dict[str, Any], resultado: Dict[str, Any], recom: Dict[str, Any]) -> str | None:
    try:
        variables = meta.get('variables') or []
        restrictions = meta.get('constraints_normalized') or []
        iter_count = len(resultado.get('iterations', []))
        solver_method = resultado.get('method') or recom.get('method')
        messages = [
            {
                "role": "system",
                "content": (
                    "Eres un tutor amable. Explica en español, en 6-10 viñetas, el procedimiento seguido "
                    "para resolver el problema de optimización. Incluye función, restricciones, método, "
                    "paso a paso y resultado. No uses JSON."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Función objetivo: {payload.get('objective_expr')}\n"
                    f"Variables: {variables}\n"
                    f"Restricciones: {restrictions}\n"
                    f"Método usado: {solver_method}\n"
                    f"Punto inicial x0: {payload.get('x0')}\n"
                    f"Tolerancia: {payload.get('tol', 1e-6)}, iteraciones máx: {payload.get('max_iter', 200)}\n"
                    f"Iteraciones ejecutadas: {iter_count}\n"
                    f"x* = {resultado.get('x_star')}, f* = {resultado.get('f_star')}\n"
                    "Redacta viñetas didácticas (procedimiento y resultado)."
                ),
            },
        ]
        return groq_service.chat_completion(messages)
    except Exception:
        return None



def solve_gradient_payload(
    payload: Dict[str, Any],
    problema: Dict[str, Any],
    meta: Dict[str, Any],
    recomendacion: Dict[str, Any],
    method_note: str | None = None,
) -> tuple[str, Dict[str, Any]]:
    tol_val = payload.get('tol')
    if tol_val in (None, ''):
        tol_val = 1e-6
    max_iter_val = payload.get('max_iter')
    if max_iter_val in (None, ''):
        max_iter_val = 200
    parametros = {
        'x0': payload.get('x0'),
        'tol': float(tol_val),
        'max_iter': int(max_iter_val),
    }
    symbolic = _symbolic_details(problema.get('objective_expr', ''), meta.get('variables') or [])
    if meta.get('has_equalities') or meta.get('has_inequalities'):
        raise ValueError('Actualmente solo se resuelven problemas sin restricciones para gradiente.')

    resultado = solver_gradiente.solve(
        objective_expr=problema['objective_expr'],
        variables=meta.get('variables') or [],
        x0=parametros['x0'],
        tol=parametros['tol'],
        max_iter=parametros['max_iter'],
    )
    plot_info = resultado.get('plot_data') or {}
    reply_payload: Dict[str, Any] = {
        'analysis': {
            'variables': meta.get('variables'),
            'objective_expr': meta.get('objective_expr'),
            'constraints': meta.get('constraints_normalized'),
            'recommendation': recomendacion,
        },
        'plot': {
            'type': 'trajectory',
            'method': 'gradient',
            'variables': meta.get('variables'),
            'iterations': resultado.get('iterations', []),
            'x_star': resultado.get('x_star'),
            'f_star': resultado.get('f_star'),
            'plot_data': plot_info,
        },
        'solver': {
            'method': resultado.get('method'),
            'status': resultado.get('status'),
            'x_star': resultado.get('x_star'),
            'f_star': resultado.get('f_star'),
            'iterations_count': len(resultado.get('iterations', [])),
        },
    }
    pre_analysis = build_pre_solution_analysis(problema, meta, recomendacion, parametros, symbolic)
    report = build_gradient_report(problema, meta, resultado, recomendacion, parametros, symbolic)

    ai_narrative = _narrate_with_ai(payload, meta, resultado, recomendacion)
    if ai_narrative and not ai_narrative.strip().startswith(("{", "[")):
        combined = f"{ai_narrative}\n\n---\n\n{pre_analysis}\n\n---\n\n{report}"
    else:
        traj = resultado.get('iterations', [])
        resumen = [
            "### Sintesis educativa",
            f"- Metodo: {resultado.get('method', 'gradiente')}",
            f"- Restricciones: eq={meta.get('has_equalities')} | ineq={meta.get('has_inequalities')}",
            f"- Iteraciones ejecutadas: {len(traj)}",
            f"- x* ~= {resultado.get('x_star')}",
            f"- f(x*) ~= {resultado.get('f_star')}",
            "- Recordatorio formal: en cada iteracion se parte de x_k, se calcula grad f(x_k) y se aplica retroceso Armijo (alpha inicial 1, c=1e-4, alpha=0.5*alpha mientras falle la desigualdad). Con el alpha aceptado se actualiza x_{k+1} = x_k - alpha_k * grad f(x_k) hasta que ||grad f|| es pequena.",
        ]
        combined = f"{pre_analysis}\n\n---\n\n{report}\n\n" + "\n".join(resumen)
    if method_note:
        combined = f"**Nota de seleccion:** {method_note}\n\n{combined}"
    return combined, reply_payload



def solve_qp_payload(
    payload: Dict[str, Any],
    problema: Dict[str, Any],
    meta: Dict[str, Any],
    recomendacion: Dict[str, Any],
    method_note: str | None = None,
) -> tuple[str, Dict[str, Any]]:
    """Resuelve problema QP y formatea la salida para visualización web."""
    resultado = solver_cuadratico.solve_qp(
        objective_expr=problema['objective_expr'],
        variables=meta.get('variables') or [],
        constraints=problema.get('constraints') or [],
    )
    
    variables = meta.get('variables') or []
    constraints_desc = meta.get('constraints_normalized') or problema.get('constraints') or []
    
    # Construir respuesta formateada - solo incluir la explicación del solver
    lines = []
    
    # Añadir la explicación completa del solver
    explicacion = (resultado.get('explanation') or '').strip()
    if explicacion:
        lines.append(explicacion)
    else:
        # Fallback si no hay explicación
        lines.append('#### Procedimiento sugerido para QP')
        lines.append('1. Reescribir f(x) como 0.5 x^T H x + c^T x para identificar H y c.')
        lines.append('2. Verificar convexidad revisando que H sea semidefinida positiva.')
        lines.append('3. Formular las restricciones lineales (igualdades y desigualdades) adicionando holguras/artificiales.')
        lines.append('4. Construir L(x, lambda, mu) y las condiciones KKT.')
        lines.append('5. Trabajar en dos fases (factibilidad y optimalidad) hasta localizar x*.')

    reply_payload: Dict[str, Any] = {
        'analysis': {
            'variables': variables,
            'objective_expr': meta.get('objective_expr'),
            'constraints': constraints_desc,
            'recommendation': recomendacion,
        },
        'plot': {'type': 'none', 'reason': 'qp_educational'},
        'solver': {
            'method': resultado.get('method', 'qp'),
            'status': resultado.get('status'),
            'message': resultado.get('message'),
            'x_star': resultado.get('x_star'),
            'f_star': resultado.get('f_star'),
            'steps': resultado.get('steps', []),
        },
    }
    return "\n".join(lines), reply_payload


def solve_lagrange_payload(
    payload: Dict[str, Any],
    problema: Dict[str, Any],
    meta: Dict[str, Any],
    recomendacion: Dict[str, Any],
    method_note: str | None = None,
) -> tuple[str, Dict[str, Any]]:
    equalities = [c.get('expr') for c in (problema.get('constraints') or []) if c.get('kind') == 'eq']
    resultado = solver_lagrange.solve(
        objective_expr=problema['objective_expr'],
        variables=meta.get('variables') or [],
        equalities=equalities,
    )
    lines = []
    lines.append('### Multiplicadores de Lagrange activados')
    lines.append(f"- f(x) = {problema.get('objective_expr')}")
    lines.append(f"- Igualdades detectadas ({len(equalities)}): {equalities or 'sin registrar'}")
    lines.append(f"- Argumento de recomendacion: {recomendacion.get('rationale')}")
    if method_note:
        lines.append(f"- Nota adicional: {method_note}")
    lines.append('')
    lines.append('#### Procedimiento guiado')
    lines.append('1. Formar L(x, lambda) = f(x) + sum(lambda_i * g_i(x)).')
    lines.append('2. Calcular derivadas parciales respecto a cada variable y cada lambda_i.')
    lines.append('3. Resolver el sistema estacionario {grad_x L = 0, g_i(x) = 0}.')
    lines.append('4. Evaluar f en los candidatos y usar el Hessiano restringido para clasificar.')
    lines.append('5. Interpretar los lambda_i como sensibilidad de cada restriccion.')
    lines.append('')
    lines.append('El MVP actual entrega esta guia y recuerda que el solver exacto esta en desarrollo.')

    reply_payload: Dict[str, Any] = {
        'analysis': {
            'variables': meta.get('variables'),
            'objective_expr': meta.get('objective_expr'),
            'constraints': equalities,
            'recommendation': recomendacion,
        },
        'plot': {'type': 'none', 'reason': 'lagrange_not_implemented'},
        'solver': {
            'method': resultado.get('method', 'lagrange'),
            'status': resultado.get('status', 'not_implemented'),
            'message': resultado.get('message'),
        },
    }
    return "\n".join(lines), reply_payload


def solve_kkt_payload(
    payload: Dict[str, Any],
    problema: Dict[str, Any],
    meta: Dict[str, Any],
    recomendacion: Dict[str, Any],
    method_note: str | None = None,
) -> tuple[str, Dict[str, Any]]:
    """Resuelve problemas usando condiciones KKT."""
    
    # Preparar constraints en formato correcto
    constraints = []
    for c in problema.get('constraints', []):
        constraints.append({
            'expression': c.get('expr', ''),
            'rhs': c.get('rhs', 0),
            'kind': c.get('kind', 'ineq')
        })
    
    # Detectar si es maximización
    is_max = problema.get('is_maximization', False)
    
    # Invocar solver KKT
    resultado = solver_kkt.solve(
        objective_expr=problema.get('objective_expr'),
        variables=meta.get('variables'),
        constraints=constraints,
        is_maximization=is_max
    )
    
    lines = []
    
    # Si hay nota del método, agregarla
    if method_note:
        lines.append(method_note)
        lines.append('')
    
    # Agregar explicación del solver
    if resultado.get('status') == 'success':
        explanation = resultado.get('explanation', '')
        if explanation:
            lines.append(explanation)
        else:
            lines.append('✅ Solución KKT encontrada')
            lines.append('')
            sol = resultado.get('solution', {})
            for var, val in sol.items():
                lines.append(f"- {var} = {val:.6f}")
            lines.append('')
            lines.append(f"Valor óptimo: {resultado.get('optimal_value', 'N/A')}")
    else:
        lines.append(f"❌ Error en solver KKT: {resultado.get('message', 'Unknown error')}")
        if 'traceback' in resultado:
            lines.append('')
            lines.append('```')
            lines.append(resultado['traceback'])
            lines.append('```')

    reply_payload: Dict[str, Any] = {
        'analysis': {
            'variables': meta.get('variables'),
            'objective_expr': meta.get('objective_expr'),
            'constraints': constraints,
            'recommendation': recomendacion,
        },
        'plot': {'type': 'none', 'reason': 'kkt_analytical'},
        'solver': {
            'method': resultado.get('method', 'kkt'),
            'status': resultado.get('status', 'error'),
            'solution': resultado.get('solution', {}),
            'optimal_value': resultado.get('optimal_value'),
            'candidates': resultado.get('candidates', []),
        },
    }
    return "\n".join(lines), reply_payload


def solve_differential_payload(
    payload: Dict[str, Any],
    problema: Dict[str, Any],
    meta: Dict[str, Any],
    recomendacion: Dict[str, Any],
    method_note: str | None = None,
) -> tuple[str, Dict[str, Any]]:
    variables = meta.get('variables') or problema.get('variables') or []
    if not variables:
        raise ValueError('No se detectaron variables para derivar.')
    try:
        sym_vars = [sp.Symbol(v, real=True) for v in variables]
        expr_sym = sp.sympify(problema['objective_expr'], locals={v.name: v for v in sym_vars})
        grad = [sp.diff(expr_sym, v) for v in sym_vars]
        hess = sp.hessian(expr_sym, sym_vars)
    except Exception as exc:
        raise ValueError(f'No se pudo derivar la funcion objetivo: {exc}') from exc

    grad_strings = [str(g) for g in grad]
    hess_strings = [[str(entry) for entry in row] for row in (hess.tolist() if hasattr(hess, 'tolist') else [[hess]])]
    lines = []
    lines.append('### Laboratorio de calculo diferencial')
    lines.append(f"- f({', '.join(variables)}) = {problema.get('objective_expr')}")
    lines.append(f'- Gradiente simbolico: {grad_strings}')
    lines.append(f'- Hessiano: {hess_strings}')
    if method_note:
        lines.append(f"- Nota: {method_note}")
    else:
        lines.append(f"- Motivo: {recomendacion.get('rationale')}")
    lines.append('')
    lines.append('#### Procedimiento sugerido')
    lines.append('1. Calcular gradiente y Hessiano simbolicos (como arriba).')
    lines.append('2. Evaluar gradiente en los puntos de interes para verificar estacionaridad.')
    lines.append('3. Revisar definitud del Hessiano para clasificar el punto.')
    lines.append('4. Utilizar la informacion para alimentar metodos numericos si es necesario.')

    reply_payload: Dict[str, Any] = {
        'analysis': {
            'variables': variables,
            'objective_expr': meta.get('objective_expr'),
            'constraints': meta.get('constraints_normalized'),
            'recommendation': recomendacion,
        },
        'plot': {'type': 'none', 'reason': 'symbolic_only'},
        'solver': {
            'method': 'differential',
            'status': 'analysis_only',
            'gradient': grad_strings,
            'hessian': hess_strings,
        },
    }
    return "\n".join(lines), reply_payload


def solve_structured_problem(payload: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
    if not payload.get('objective_expr'):
        raise ValueError(
            "No se pudo identificar la función objetivo. Incluye expresiones como f(x,y) = ... o 'minimizar ...' para comenzar."
        )
    constraints = payload.get('constraints')
    if constraints is None:
        constraints = payload.get('constraints_raw') or []
    problema = {
        'objective_expr': payload.get('objective_expr'),
        'variables': payload.get('variables'),
        'constraints': constraints,
    }
    meta = analyzer.analyze_problem(problema)
    meta_with_flags = dict(meta)
    if payload.get('derivative_only') or (payload.get('method') == 'differential') or (payload.get('method_hint') == 'differential'):
        meta_with_flags['derivative_only'] = True
    if payload.get('iterative_process'):
        meta_with_flags['iterative_process'] = True
    # Propagar pista de metodo si viene en el payload (IA/usuario)
    if payload.get('method'):
        meta_with_flags['method_hint'] = payload.get('method')
    elif payload.get('method_hint'):
        meta_with_flags['method_hint'] = payload.get('method_hint')

    # Fusionar hints textuales con los flags del analizador
    hints = payload.get('_constraint_hints') or {}
    has_eq = bool(meta_with_flags.get('has_equalities') or hints.get('has_equalities_hint'))
    has_ineq = bool(meta_with_flags.get('has_inequalities') or hints.get('has_inequalities_hint'))
    meta_with_flags['has_equalities'] = has_eq
    meta_with_flags['has_inequalities'] = has_ineq
    meta_with_flags['has_constraints'] = bool(meta.get('has_constraints') or has_eq or has_ineq)

    recomendacion = recommender_ai.recommend(meta_with_flags)

    method = recomendacion.get('method')
    method_note = recomendacion.get('rationale')
    if not method:
        raise ValueError('No es posible determinar el metodo con la informacion disponible.')
    forced = payload.get('method')
    if forced and forced != method:
        method_note = (
            f"{method_note} (Se solicito {forced}, pero las reglas seleccionan {method})."
        )
    elif forced and forced == method:
        method_note = f"{method_note} (Coincide con el método indicado)."
    elif payload.get('method_hint') and payload.get('method_hint') != method:
        method_note = f"{method_note} (La pista mencionaba {payload.get('method_hint')}, se usará {method})."
    
    # Información de debug solo para logs, no para el usuario
    # (Eliminado del output visible)

    _validate_payload_for_method(method, payload, meta)
    auto_notes = payload.pop('_auto_notes', [])
    if auto_notes:
        notes_text = " ".join(auto_notes)
        method_note = f"{method_note} {notes_text}".strip() if method_note else notes_text

    if method == 'gradient':
        return solve_gradient_payload(payload, problema, meta, recomendacion, method_note)
    if method == 'qp':
        return solve_qp_payload(payload, problema, meta, recomendacion, method_note)
    if method == 'lagrange':
        return solve_lagrange_payload(payload, problema, meta, recomendacion, method_note)
    if method == 'kkt':
        return solve_kkt_payload(payload, problema, meta, recomendacion, method_note)
    if method == 'differential':
        return solve_differential_payload(payload, problema, meta, recomendacion, method_note)
    raise ValueError(f'Metodo {method} no soportado en el asistente.')


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs'].get('session_id')
        self.group_name = f"chat_{self.session_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        try:
            await self.ensure_session()
        except Exception:
            pass
        await self.accept()
        await self.send_json({'type': 'status', 'stage': 'connected', 'detail': 'Conexión establecida'})

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data or '{}')
        except Exception:
            data = {}

        msg_type = data.get('type')
        if msg_type == 'user_message':
            text = data.get('text', '')
            await self.save_message('user', text)

            message_kind = scope_guard.classify_message(text)
            if message_kind in ('greeting', 'identity', 'meta', 'empty'):
                ai_reply = await self._respond_smalltalk(text, message_kind)
                await self.save_message('assistant', ai_reply)
                await self.send_json({'type': 'assistant_message', 'text': ai_reply})
                return
            if message_kind == 'out_of_scope':
                reminder = scope_guard.scope_violation_reply()
                await self.save_message('assistant', reminder)
                await self.send_json({'type': 'assistant_message', 'text': reminder})
                return

            structured_payload: Dict[str, Any] | None = None
            heuristic_candidate: Dict[str, Any] | None = None
            parse_source = "none"  # Para debugging
            
            # Intentar JSON directo
            try:
                candidate = json.loads(text)
                if isinstance(candidate, dict) and 'objective_expr' in candidate:
                    structured_payload = candidate
                    parse_source = "json_directo"
            except Exception:
                structured_payload = None
            
            if not structured_payload:
                ai_payload = _extract_payload_with_ai(text)
                logger.info("AI payload raw: %s", ai_payload)
                if ai_payload:
                    structured_payload = ai_payload
                    parse_source = "ai_extractor"
                    logger.info(f"[DEBUG] Usando AI Extractor - Restricciones: {len(ai_payload.get('constraints', []))}, Metodo: {ai_payload.get('method')}")
            
            if structured_payload:
                heuristic_candidate = message_parser.parse_structured_payload(text, allow_partial=True)
                logger.info("Heuristic payload: %s", heuristic_candidate)
                structured_payload = _merge_payload(structured_payload, heuristic_candidate)
                logger.info("Merged payload to solver: %s", structured_payload)
            # Si el usuario menciona explicitamente KKT, forzar el metodo a KKT
            try:
                if 'kkt' in (text or '').lower():
                    structured_payload.setdefault('method', 'kkt')
                    structured_payload.setdefault('method_hint', 'kkt')
            except Exception:
                pass
            if not structured_payload:
                if heuristic_candidate is None:
                    heuristic_candidate = message_parser.parse_structured_payload(text)
                structured_payload = heuristic_candidate
                if structured_payload:
                    parse_source = "heuristic_parser"
                    logger.warning(f"[DEBUG] AI Extractor falló, usando parser heurístico - Restricciones: {len(structured_payload.get('constraints', []))}")

            if structured_payload:
                logger.debug("Structured payload before solver: %s", json.dumps(structured_payload, ensure_ascii=False))
                
                try:
                    assistant_text, reply_payload = solve_structured_problem(structured_payload)
                    # No agregar notas de debug al texto visible del usuario
                except Exception as exc:
                    assistant_text = (
                        "No se pudo resolver el problema con el solver local. "
                        f"Detalle: {exc}\n\n"
                        "Sugerencia: verifica dimensiones de x0 y variables, y usa funciones soportadas (sin/sin(), cos/cos())."
                    )
                    reply_payload = {'error': str(exc)}
                reply = {'type': 'assistant_message', 'text': assistant_text, 'payload': reply_payload}
                await self.save_message('assistant', assistant_text, payload=reply_payload)
                await self.send_json(reply)
                return

            history = await self.get_history()
            messages = groq_service.build_messages_from_session(history, text)
            try:
                assistant_text = await asyncio.to_thread(
                    groq_service.chat_completion,
                    messages,
                )
            except Exception as e:
                assistant_text = (
                    "No se pudo contactar al asistente IA. "
                    "Verifica GROQ_API_KEY y la instalación del paquete 'groq'.\n\n"
                    f"Detalle: {str(e)}"
                )
            reply: Dict[str, Any] = {'type': 'assistant_message', 'text': assistant_text}
            await self.save_message('assistant', assistant_text)
            await self.send_json(reply)
        else:
            await self.send_json({'type': 'status', 'stage': 'idle', 'detail': 'Mensaje no reconocido'})

    async def send_json(self, content):
        await self.send(text_data=json.dumps(content))

    async def _respond_smalltalk(self, user_text: str, kind: str) -> str:
        """
        Usa Groq con el prompt contextual para responder saludos/preguntas basicas.
        Si falla la llamada a la IA, recurre al texto base local.
        """
        try:
            prompt = (
                "Eres el asistente educativo de OptiLearn Web. Responde en una o dos frases, en espanol, "
                "con tono cercano. No devuelvas JSON ni tablas. No pidas la funcion objetivo a menos que el "
                "usuario lo solicite. Si es saludo, saluda y ofrece ayuda breve. "
                "Si preguntan quien te creo, responde: 'Fui creado para OptiLearn Web por estudiantes de la Universidad de los Llanos: "
                "Diego Alejandro Machado Tovar, Juan Carlos Barrera Guevara y Jesus Gregorio Delgado.' "
                "Si preguntan como estas, responde de forma humana y dispuesta a ayudar. "
                f"Mensaje del usuario: {user_text}"
            )
            ai_reply = await asyncio.to_thread(
                groq_service.chat_completion,
                [{"role": "user", "content": prompt}],
                None,
                0.6,
                180,
            )
            if ai_reply and ai_reply.strip():
                return ai_reply.strip()
        except Exception:
            pass
        # Fallback determinista
        return scope_guard.smalltalk_reply(kind)

    @database_sync_to_async
    def ensure_session(self):
        try:
            ChatSession.objects.get_or_create(id=self.session_id)
        except Exception:
            pass

    @database_sync_to_async
    def save_message(self, role: str, text: str, payload: Dict[str, Any] | None = None):
        try:
            session = ChatSession.objects.get(id=self.session_id)
            ChatMessage.objects.create(
                session=session,
                role=role,
                content=text,
                payload=payload or {},
            )
        except Exception:
            pass

    @database_sync_to_async
    def get_history(self):
        try:
            session = ChatSession.objects.get(id=self.session_id)
            qs = session.messages.order_by('created_at')
            out = []
            for m in qs:
                if m.role in ('user', 'assistant', 'system'):
                    out.append({"role": m.role, "content": m.content})
            return out
        except Exception:
            return []
