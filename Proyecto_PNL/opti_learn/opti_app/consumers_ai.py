import json
import asyncio
import ast
import re
from typing import Any, Dict, List

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from .models import ChatSession, ChatMessage
from .core import analyzer, recommender_ai, solver_gradiente
from .ai import groq_service
import sympy as sp


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


METHOD_KEYWORDS = {
    'gradiente': 'gradient',
    'gradient': 'gradient',
    'gradual': 'gradient',
    'lagrange': 'lagrange',
    'lagrangiano': 'lagrange',
    'kkt': 'kkt',
    'karush': 'kkt',
    'cuadratic': 'qp',
    'quadratic': 'qp',
    'qp': 'qp',
    'cálculo': 'differential',
    'calculo': 'differential',
}


def _clean_expr(expr: str) -> str:
    expr = expr.strip()
    if len(expr) >= 2 and expr[0] in "\"'`" and expr[-1] == expr[0]:
        expr = expr[1:-1]
    return expr.strip().rstrip(';, .')


def _strip_to_math(expr: str) -> str:
    expr = expr.strip()
    for idx, ch in enumerate(expr):
        if ch.isalnum() or ch in "+-(":
            return expr[idx:].strip()
    return expr


def _parse_numeric_list(snippet: str) -> List[float] | None:
    snippet = snippet.strip()
    try:
        value = ast.literal_eval(snippet)
    except Exception:
        snippet = snippet.strip('[](){}')
        parts = [p.strip() for p in re.split(r'[;,]', snippet) if p.strip()]
        if not parts:
            return None
        try:
            value = [float(p) for p in parts]
        except Exception:
            return None
    if isinstance(value, (int, float)):
        return [float(value)]
    if isinstance(value, (list, tuple)):
        cleaned = []
        for item in value:
            try:
                cleaned.append(float(item))
            except Exception:
                return None
        return cleaned
    return None


def _parse_variables(snippet: str) -> List[str]:
    snippet = snippet.strip()
    if not snippet:
        return []
    if snippet.startswith('['):
        try:
            value = ast.literal_eval(snippet)
            if isinstance(value, (list, tuple)):
                return [str(v).strip() for v in value if str(v).strip()]
        except Exception:
            pass
    return [part.strip() for part in re.split(r'[,\s]+', snippet) if part.strip()]


def parse_payload_from_text(message: str) -> Dict[str, Any] | None:
    text = message or ''
    lowered = text.lower()
    detected_method = None
    for keyword, mapped in METHOD_KEYWORDS.items():
        if keyword in lowered:
            detected_method = mapped
            break
    # Solo soportamos gradiente en este flujo
    if detected_method and detected_method != 'gradient':
        return None

    expr = None
    inferred_vars = None
    expr_patterns = [
        r'(?:func(?:ión|ion|objective|objetivo)[^:]*:\s*)(?P<expr>"[^"]+"|\'[^\']+\'|`[^`]+`|[^\n,;]+)',
        r'f\s*\([^\)]*\)\s*=\s*(?P<expr>[^\n,;]+)',
    ]
    for pattern in expr_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            expr = _strip_to_math(_clean_expr(match.group('expr')))
            if expr:
                break
    if not expr:
        try:
            m = re.search(r'(?P<expr>.+?)\s*x0\s*[:=]', text, re.IGNORECASE)
            if m:
                expr_guess = _strip_to_math(_clean_expr(m.group('expr')))
                if expr_guess:
                    expr = expr_guess
                    try:
                        sym = sp.sympify(expr_guess, locals=analyzer.FUNCIONES_PERMITIDAS)
                        vars_auto = sorted([str(s) for s in sym.free_symbols])
                        if vars_auto:
                            inferred_vars = vars_auto
                    except Exception:
                        pass
        except Exception:
            pass
    if not expr:
        return None

    payload: Dict[str, Any] = {
        'objective_expr': expr,
        'constraints': [],
    }
    if inferred_vars:
        payload['variables'] = inferred_vars
    var_match = re.search(r'variables?\s*[:=]\s*(\[[^\]]+\]|[a-zA-Z_,\s]+)', text, re.IGNORECASE)
    if var_match:
        vars_list = _parse_variables(var_match.group(1))
        if vars_list:
            payload['variables'] = vars_list

    x0_match = re.search(r'x[_\s]?0\s*[:=]\s*(\[[^\]]+\]|\([^\)]+\)|\{[^\}]+\})', text, re.IGNORECASE)
    if x0_match:
        x0_values = _parse_numeric_list(x0_match.group(1))
        if x0_values is not None:
            payload['x0'] = x0_values

    tol_match = re.search(r'tol(?:erancia)?\s*[:=]\s*([0-9eE\.\-+]+)', text, re.IGNORECASE)
    if tol_match:
        try:
            payload['tol'] = float(tol_match.group(1))
        except Exception:
            pass

    max_iter_match = re.search(r'(?:max(?:imo)?\s*iter|iteraciones\s*max)\s*[:=]\s*(\d+)', text, re.IGNORECASE)
    if max_iter_match:
        try:
            payload['max_iter'] = int(max_iter_match.group(1))
        except Exception:
            pass

    payload['method'] = detected_method or 'gradient'
    # Fallback: intentar extraer x0 si no se obtuvo
    if 'x0' not in payload or payload.get('x0') is None:
        m = re.search(r'x[_\s]?0\s*[:=]\s*(\[[^\]]+\]|\([^\)]+\)|\{[^\}]+\})', text, re.IGNORECASE)
        if m:
            x0_values = _parse_numeric_list(m.group(1))
            if x0_values is not None:
                payload['x0'] = x0_values

    return payload


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
                    "Extrae un JSON con campos: objective_expr (SymPy), variables (lista), "
                    "constraints (lista opcional), x0 (lista opcional), tol (float), "
                    "max_iter (int), derivative_only (bool opcional). Responde solo JSON."
                ),
            },
            {"role": "user", "content": text},
        ]
        raw = groq_service.chat_completion(messages)
        return json.loads(raw) if raw else None
    except Exception:
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


def solve_gradient_payload(payload: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
    problema = {
        'objective_expr': payload.get('objective_expr'),
        'variables': payload.get('variables'),
        'constraints': payload.get('constraints') or payload.get('constraints_raw') or [],
    }
    meta = analyzer.analyze_problem(problema)
    recomendacion = recommender_ai.recommend(meta)
    parametros = {
        'x0': payload.get('x0'),
        'tol': float(payload.get('tol', 1e-6)),
        'max_iter': int(payload.get('max_iter', 200)),
    }
    symbolic = _symbolic_details(problema.get('objective_expr', ''), meta.get('variables') or [])
    metodo_solicitado = payload.get('method') or recomendacion.get('method')
    if metodo_solicitado != 'gradient':
        raise ValueError(f"Método {metodo_solicitado} no implementado en esta vista.")
    if meta.get('has_equalities') or meta.get('has_inequalities'):
        raise ValueError("Actualmente solo se resuelven problemas sin restricciones para gradiente.")

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
    # Si la IA devuelve JSON u objeto vacío, descartar y usar fallback.
    if ai_narrative and not ai_narrative.strip().startswith(("{", "[")):
        combined = f"{ai_narrative}\n\n---\n\n{pre_analysis}\n\n---\n\n{report}"
    else:
        traj = resultado.get('iterations', [])
        resumen = [
            "### Síntesis educativa",
            f"- Método: {resultado.get('method', 'gradiente')}",
            f"- Restricciones: eq={meta.get('has_equalities')} | ineq={meta.get('has_inequalities')}",
            f"- Iteraciones ejecutadas: {len(traj)}",
            f"- x* ≈ {resultado.get('x_star')}",
            f"- f(x*) ≈ {resultado.get('f_star')}",
            "- Recordatorio formal: en cada iteracion se parte de x_k, se calcula grad f(x_k) y se aplica retroceso Armijo (alpha inicial 1, c=1e-4, alpha=0.5*alpha mientras falle la desigualdad). Con el alpha aceptado se actualiza x_{k+1} = x_k - alpha_k * grad f(x_k) hasta que ||grad f|| es pequena.",
        ]
        combined = f"{pre_analysis}\n\n---\n\n{report}\n\n" + "\n".join(resumen)
    return combined, reply_payload


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

            structured_payload: Dict[str, Any] | None = None
            # Intentar JSON directo
            try:
                candidate = json.loads(text)
                if isinstance(candidate, dict) and 'objective_expr' in candidate:
                    structured_payload = candidate
            except Exception:
                structured_payload = None
            # Intentar parseo heurístico
            if not structured_payload:
                structured_payload = parse_payload_from_text(text)
            # Intentar extracción con IA
            if not structured_payload:
                structured_payload = _extract_payload_with_ai(text)

            if structured_payload:
                try:
                    assistant_text, reply_payload = solve_gradient_payload(structured_payload)
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
