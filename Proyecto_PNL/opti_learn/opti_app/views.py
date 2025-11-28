import time
import json
import uuid
from typing import Any, Dict

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.db.utils import OperationalError, ProgrammingError
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.decorators.csrf import ensure_csrf_cookie

from .models import Problem, Constraint, Solution, Iteration, ChatSession
from .serializers import (
    ProblemSerializer, SolutionSerializer, IterationSerializer, ParseRequestSerializer
)
from .core import analyzer
from .core import scope_guard
from .core import solver_gradiente, solver_cuadratico
from .core import recommender_ai
from .ai import groq_service


@ensure_csrf_cookie
def index(request):
    # Crear una sesión de chat por visita (simple MVP)
    chat_session_id = None
    try:
        session = ChatSession.objects.create(
            user=request.user if request.user.is_authenticated else None,
            problem=None,
            active=True,
        )
        chat_session_id = str(session.id)
    except (OperationalError, ProgrammingError):
        # BD sin migraciones: generar UUID efímero para permitir conexión WS sin persistencia.
        chat_session_id = str(uuid.uuid4())
    return render(request, 'index.html', {"chat_session_id": chat_session_id})


@api_view(["POST"])
def ai_chat(request):
    text = (request.data or {}).get('text', '')
    session_id = (request.data or {}).get('session_id')
    if not text:
        return Response({'detail': 'Texto vacío.'}, status=400)
    if not scope_guard.is_message_allowed(text):
        return Response({'type': 'assistant_message', 'text': scope_guard.scope_violation_reply()})

    # Construir historial básico si la BD está disponible
    history = []
    try:
        if session_id:
            session = ChatSession.objects.get(id=session_id)
            for m in session.messages.order_by('created_at'):
                if m.role in ('user','assistant','system'):
                    history.append({'role': m.role, 'content': m.content})
    except Exception:
        pass

    try:
        messages = groq_service.build_messages_from_session(history, text)
        assistant_text = groq_service.chat_completion(messages)
    except Exception as e:
        # Fallback local si Groq no está disponible
        assistant_text = (
            "No se pudo contactar al asistente IA. "
            "Verifica GROQ_API_KEY y el paquete 'groq'.\n\n"
            f"Detalle: {str(e)}"
        )
        try:
            payload = json.loads(text)
            if isinstance(payload, dict) and 'objective_expr' in payload:
                meta = analyzer.analyze_problem(payload)
                rec = recommender_ai.recommend(meta)
                assistant_text += (
                    "\n\nAnálisis preliminar: "
                    f"Variables: {meta.get('variables')} | "
                    f"Eq: {meta.get('has_equalities')} | Ineq: {meta.get('has_inequalities')} | "
                    f"Cuadrática: {meta.get('is_quadratic')} | Método sugerido: {rec.get('method')}"
                )
        except Exception:
            pass

    return Response({'type': 'assistant_message', 'text': assistant_text})


@api_view(["GET"])
def ai_prompt_health(request):
    """Devuelve información sobre el prompt del sistema usado por la IA."""
    conf = getattr(settings, "AI_ASSISTANT", {}) if hasattr(settings, "AI_ASSISTANT") else {}
    resolved = groq_service.resolve_prompt_path()
    path_str = str(resolved) if resolved else None
    exists = bool(resolved and resolved.is_file())
    head = None
    size = None
    try:
        if exists:
            txt = resolved.read_text(encoding="utf-8")
            head = txt[:400]
            size = len(txt)
    except Exception as e:  # pragma: no cover
        head = f"<error leyendo prompt: {e}>"
    data = {
        'configured_prompt_path': conf.get('prompt_path'),
        'resolved_prompt_path': path_str,
        'exists': exists,
        'size': size,
        'head': head,
        'model': conf.get('model'),
        'temperature': conf.get('temperature'),
        'max_tokens': conf.get('max_tokens'),
    }
    return Response(data)


# Métodos: vistas simples por cada técnica
@ensure_csrf_cookie
def method_view(request, method_key: str):
    titles = {
        'differential': 'Cálculo Diferencial (sin restricciones)',
        'lagrange': 'Método de Lagrange (igualdades)',
        'kkt': 'Condiciones KKT (desigualdades)',
        'gradient': 'Gradiente Descendente',
        'qp': 'Programación Cuadrática',
    }
    template_map = {
        'gradient': 'methods/gradient.html',
        'lagrange': 'methods/lagrange.html',
        'kkt': 'methods/kkt.html',
        'qp': 'methods/qp.html',
        'differential': 'methods/differential.html',
    }
    template_name = template_map.get(method_key, 'methods/gradient.html')
    context = {
        'method_key': method_key,
        'title': titles.get(method_key, method_key),
    }
    return render(request, template_name, context)


def _build_gradient_explanation(meta: Dict[str, Any], resultado: Dict[str, Any], tol: float, max_iter: int, x0=None) -> str:
    """
    Genera una explicación en tono educativo a partir del resultado del solver.
    Intenta usar el modelo IA si está disponible; si falla, devuelve un texto local.
    """
    vars_ = meta.get('variables') or []
    vars_str = ", ".join(vars_) if vars_ else "desconocidas"
    x_star = resultado.get('x_star')
    f_star = resultado.get('f_star')
    iters = resultado.get('iterations') or []
    k_final = iters[-1]['k'] if iters else 0
    objective = meta.get('objective_expr', '')
    alpha_series = [float(it.get('alpha')) for it in iters if isinstance(it.get('alpha'), (int, float))]

    def _line_search_summary(iteraciones):
        resumen = []
        for it in iteraciones[:4]:
            trace = it.get('line_search') or []
            if not trace:
                continue
            accepted = trace[-1]
            reductions = sum(1 for entry in trace if not entry.get('accepted'))
            resumen.append({
                'k': it.get('k'),
                'alpha': float(accepted.get('alpha', 0.0)),
                'reductions': reductions,
                'reason': accepted.get('reason', 'armijo'),
            })
        return resumen

    alpha_traces = _line_search_summary(iters)

    base_lines = []
    base_lines.append("Explicacion educativa (Gradiente Descendente)")
    base_lines.append(f"- Problema: minimizar f({vars_str}) = {objective}")
    base_lines.append(f"- Punto inicial: x0 = {x0 if x0 is not None else 'no especificado'}")
    base_lines.append(f"- Criterio de paro: ||grad f|| < {tol} o k >= {max_iter}")
    base_lines.append("")
    base_lines.append("Paso a paso:")
    base_lines.append("1) Calcular f(x_k) y el gradiente actual.")
    base_lines.append("2) Calcular alpha_k mediante retroceso Armijo:")
    base_lines.append("   - Iniciar alpha = 1, constante c = 1e-4 y factor rho = 0.5.")
    base_lines.append("   - Mientras f(x_k - alpha * grad) > f(x_k) - c * alpha * ||grad||^2 se reemplaza alpha = rho * alpha.")
    base_lines.append("   - El alpha aceptado es el ultimo que satisface la condicion de Armijo.")
    base_lines.append("3) Actualizar x_{k+1} = x_k - alpha_k * grad f(x_k).")
    base_lines.append("4) Repetir hasta cumplir el criterio de paro.")
    base_lines.append("")
    base_lines.append("Resultado del solver:")
    base_lines.append(f"- Iteraciones ejecutadas: {k_final + 1}")
    base_lines.append(f"- Punto optimo estimado: x* ~= {x_star}")
    base_lines.append(f"- Valor minimo: f(x*) ~= {f_star}")

    def _build_line_section():
        if alpha_traces:
            lines = ["", "Tamano de paso calculado (retroceso Armijo):"]
            for trace in alpha_traces:
                status = "criterio Armijo" if trace['reason'] == 'armijo' else "alpha minimo forzado"
                lines.append(
                    f"- Iteracion {trace['k']}: alpha_k ~= {trace['alpha']:.5g} "
                    f"(reducciones: {trace['reductions']}, {status})."
                )
            return "\n".join(lines)
        if alpha_series:
            values = ", ".join(f"{a:.5g}" for a in alpha_series[:6])
            if len(alpha_series) > 6:
                values += '...'
            return "\n\nTamano de paso aproximado por iteracion: " + values
        return ""
    line_section = _build_line_section()
    base_text = "\n".join(base_lines) + line_section

    # Intentar generar una version con el modelo IA si esta disponible
    try:
        alpha_summary_text = ""
        if alpha_traces:
            alpha_summary_text = "\nResumen Armijo: " + "; ".join(
                f"k={info['k']} -> alpha~={info['alpha']:.5g} (reducciones {info['reductions']})"
                for info in alpha_traces
            )
        elif alpha_series:
            alpha_summary_text = "\nTamanos de paso aproximados: " + ", ".join(
                f"{a:.5g}" for a in alpha_series[:6]
            )
        messages = [
            {
                "role": "system",
                "content": (
                    "Eres un tutor amable y pedagogico. Explica el gradiente descendente en 6-8 vinetas, "
                    "incluyendo el algoritmo de retroceso Armijo: alpha inicial 1, desigualdad de Armijo y reducciones por rho=0.5. "
                    "No digas 'se eligio'; describe el calculo paso a paso."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Funcion: f({vars_str}) = {objective}\n"
                    f"Punto inicial: {x0}\n"
                    f"Tolerancia: {tol}, Iteraciones max: {max_iter}\n"
                    f"Iteraciones ejecutadas: {k_final + 1}\n"
                    f"Resultado: x* = {x_star}, f* = {f_star}\n"
                    "Los tamanos de paso alpha_k se obtuvieron con busqueda de linea Armijo cada iteracion."
                    f"{alpha_summary_text}\n"
                    "Redacta el procedimiento sin JSON, solo texto."
                ),
            },
        ]
        ai_text = groq_service.chat_completion(messages)
        if ai_text:
            return ai_text.strip() + line_section
    except Exception:
        pass
    return base_text


class ParseProblemAPIView(APIView):
    def post(self, request):
        serializer = ParseRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos_entrada = serializer.validated_data
        try:
            resultado = analyzer.analyze_problem(datos_entrada)
            return Response(resultado)
        except Exception as e:
            return Response({
                'code': 'parse_error',
                'message': str(e)
            }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)


class ProblemViewSet(viewsets.ModelViewSet):
    queryset = Problem.objects.all().order_by('-created_at')
    serializer_class = ProblemSerializer

    def perform_create(self, serializer):
        instance = serializer.save(owner=self.request.user if self.request.user.is_authenticated else None)
        # Persistir constraints normalizadas opcionalmente
        constraints = (serializer.validated_data.get('constraints_raw') or [])
        has_eq = any(c.get('kind') == 'eq' for c in constraints)
        has_ineq = any(c.get('kind') in ('le', 'ge') for c in constraints)
        instance.has_equalities = has_eq
        instance.has_inequalities = has_ineq
        # Detectar si es cuadrática
        try:
            meta = analyzer.analyze_problem(serializer.validated_data)
            instance.is_quadratic = bool(meta.get('is_quadratic', False))
            instance.variables = meta.get('variables', instance.variables)
            instance.save()
        except Exception:
            pass

    @action(detail=True, methods=['get'])
    def iterations(self, request, pk=None):
        problema = self.get_object()
        sol_id = request.query_params.get('solution_id')
        if sol_id:
            solucion = get_object_or_404(Solution, id=sol_id, problem=problema)
        else:
            solucion = problema.solutions.order_by('-created_at').first()
        if not solucion:
            return Response({'detail': 'No hay soluciones para este problema.'}, status=404)
        data = IterationSerializer(solucion.iterations.order_by('k'), many=True).data
        return Response(data)

    @action(detail=True, methods=['post'])
    def solve(self, request, pk=None):
        problema = self.get_object()
        parametros = request.data or {}
        inicio = time.perf_counter()
        try:
            metadatos = analyzer.analyze_problem({
                'objective_expr': problema.objective_expr,
                'variables': problema.variables,
                'constraints': problema.constraints_raw,
            })
        except Exception as e:
            return Response({'code': 'analyze_error', 'message': str(e)}, status=422)

        recomendacion = recommender_ai.recommend(metadatos)
        metodo = parametros.get('method') or recomendacion['method']
        tolerancia = float(parametros.get('tol', 1e-6))
        max_iteraciones = int(parametros.get('max_iter', 200))

        solucion = Solution(problem=problema, method=metodo, tolerance=tolerancia)
        solucion.save()

        resultado = None
        try:
            if metodo == 'gradient':
                resultado = solver_gradiente.solve(
                    objective_expr=problema.objective_expr,
                    variables=metadatos['variables'],
                    x0=parametros.get('x0'),
                    tol=tolerancia,
                    max_iter=max_iteraciones,
                )
                solucion.x_star = resultado['x_star']
                solucion.f_star = resultado['f_star']
                solucion.iterations_count = len(resultado['iterations'])
                solucion.status = resultado.get('status', 'ok')
                solucion.explanation_final = _build_gradient_explanation(
                    metadatos, resultado, tolerancia, max_iteraciones, parametros.get('x0')
                )
                solucion.runtime_ms = int((time.perf_counter() - inicio) * 1000)
                solucion.save()
                # Guardar iteraciones
                iteraciones_obj = []
                for it in resultado['iterations']:
                    iteraciones_obj.append(Iteration(
                        solution=solucion,
                        k=it['k'], x_k=it['x_k'], f_k=it.get('f_k'),
                        grad_norm=it.get('grad_norm'), step=it.get('step'),
                        line_search=it.get('line_search', []),
                        notes=it.get('notes', '')
                    ))
                Iteration.objects.bulk_create(iteraciones_obj)
            elif metodo == 'qp':
                resultado = solver_cuadratico.solve_qp(
                    objective_expr=problema.objective_expr,
                    variables=metadatos['variables'],
                    constraints=problema.constraints_raw,
                )
                solucion.x_star = resultado.get('x_star')
                solucion.f_star = resultado.get('f_star')
                solucion.iterations_count = len(resultado.get('iterations', []))
                solucion.status = resultado.get('status', 'educational_only')
                solucion.explanation_final = resultado.get('explanation', resultado.get('message', ''))
                solucion.runtime_ms = int((time.perf_counter() - inicio) * 1000)
                solucion.save()
            else:
                solucion.status = 'not_implemented'
                solucion.explanation_final = (
                    f"Método {metodo} aún no implementado en el MVP. "
                    f"Recomendación: {recomendacion.get('rationale', '')}"
                )
                solucion.runtime_ms = int((time.perf_counter() - inicio) * 1000)
                solucion.save()
        except Exception as e:
            solucion.status = 'error'
            solucion.explanation_final = f"Error al resolver: {e}"
            solucion.runtime_ms = int((time.perf_counter() - inicio) * 1000)
            solucion.save()
            return Response(SolutionSerializer(solucion).data, status=500)

        response_data = SolutionSerializer(solucion).data
        if resultado and resultado.get('plot_data'):
            response_data['plot_data'] = resultado['plot_data']
        # Asegurar texto plano en explanation_final (sin JSON crudo)
        expl = response_data.get('explanation_final')
        if isinstance(expl, (dict, list)):
            # Formatear dict/list a viñetas simples
            if isinstance(expl, dict):
                bullets = [f"- {k}: {v}" for k, v in expl.items()]
            else:
                bullets = [f"- {item}" for item in expl]
            response_data['explanation_final'] = "\n".join(bullets)
        elif expl is None:
            response_data['explanation_final'] = "Interpretación no disponible."
        else:
            response_data['explanation_final'] = str(expl)
        return Response(response_data)


class SolutionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Solution.objects.all().order_by('-created_at')
    serializer_class = SolutionSerializer


# ==============================================================================
# ENDPOINTS DIRECTOS PARA FORMULARIOS MANUALES (SIN PERSISTENCIA EN BD)
# ==============================================================================

@api_view(["POST"])
def solve_lagrange_manual(request):
    """
    Endpoint para resolver problemas de Lagrange desde formulario manual.
    Recibe: objective_expr, variables, constraints (JSON)
    Retorna: explanation (Markdown con LaTeX + imágenes), metadata
    """
    from .core.solver_lagrange import solve_with_lagrange_method
    
    try:
        data = request.data
        objective_expr = data.get('objective_expr', '').strip()
        variables = data.get('variables', [])
        constraints_raw = data.get('constraints', [])
        
        if not objective_expr:
            return Response({'error': 'Función objetivo requerida'}, status=400)
        if not variables:
            return Response({'error': 'Variables requeridas'}, status=400)
        if not constraints_raw:
            return Response({'error': 'Restricciones requeridas'}, status=400)
        
        # Normalizar restricciones a lista de strings
        constraints = []
        for c in constraints_raw:
            if isinstance(c, str):
                # Formato antiguo: string directo
                constraints.append(c.strip())
            elif isinstance(c, dict):
                # Formato nuevo: {expr: "...", kind: "eq"}
                expr = c.get('expr', c.get('expression', '')).strip()
                if expr:
                    constraints.append(expr)
            else:
                continue
        
        if not constraints:
            return Response({'error': 'No se encontraron restricciones válidas'}, status=400)
        
        # Llamar al solver pedagógico
        result = solve_with_lagrange_method(
            objective_expression=objective_expr,
            variable_names=variables,
            equality_constraints=constraints
        )
        
        return Response({
            'success': True,
            'explanation': result.get('explanation', ''),
            'metadata': {
                'x_star': result.get('x_star'),
                'f_star': result.get('f_star'),
                'lambda_star': result.get('lambda_star'),
                'critical_points': result.get('critical_points', []),
                'plot_2d_path': result.get('plot_2d_path'),
                'plot_3d_path': result.get('plot_3d_path'),
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Error al resolver: {str(e)}'
        }, status=500)


@api_view(["POST"])
def solve_differential_manual(request):
    """
    Endpoint para resolver problemas de cálculo diferencial desde formulario manual.
    Recibe: objective_expr, variables
    Retorna: explanation (Markdown con LaTeX + imágenes), metadata
    """
    from .core.solver_differential import solve_with_differential_method
    
    try:
        data = request.data
        objective_expr = data.get('objective_expr', '').strip()
        variables = data.get('variables', [])
        
        if not objective_expr:
            return Response({'error': 'Función objetivo requerida'}, status=400)
        if not variables:
            return Response({'error': 'Variables requeridas'}, status=400)
        
        # Llamar al solver pedagógico
        result = solve_with_differential_method(
            objective_expression=objective_expr,
            variable_names=variables
        )
        
        return Response({
            'success': True,
            'explanation': result.get('explanation', ''),
            'metadata': {
                'critical_points': result.get('critical_points', []),
                'optimal_point': result.get('optimal_point'),
                'optimal_value': result.get('optimal_value'),
                'nature': result.get('nature'),
                'plot_2d_path': result.get('plot_2d_path'),
                'plot_3d_path': result.get('plot_3d_path'),
            }
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Error al resolver: {str(e)}'
        }, status=500)


@api_view(["POST"])
def solve_kkt_manual(request):
    """
    Endpoint para resolver problemas con condiciones KKT desde formulario manual.
    Recibe: objective_expr, variables, constraints (JSON con kind: eq/ineq/le/ge)
    Retorna: explanation (Markdown con LaTeX), metadata
    """
    from .core.solver_kkt import KKTSolver
    
    try:
        data = request.data
        objective_expr = data.get('objective_expr', '').strip()
        variables = data.get('variables', [])
        constraints = data.get('constraints', [])
        # Soportar ambos nombres para maximización
        is_maximization = data.get('maximize', data.get('is_maximization', False))
        
        if not objective_expr:
            return Response({'error': 'Función objetivo requerida'}, status=400)
        if not variables:
            return Response({'error': 'Variables requeridas'}, status=400)
        
        # Preparar restricciones para el solver KKT
        kkt_constraints = []
        for c in constraints:
            expr = c.get('expr', c.get('expression', ''))
            kind = c.get('kind', 'ineq')
            rhs = c.get('rhs', 0)
            
            # Normalizar expresiones con operadores de comparación
            if '>=' in expr:
                parts = expr.split('>=')
                expr = f"({parts[0].strip()}) - ({parts[1].strip()})"
                kind = 'ge'
            elif '<=' in expr:
                parts = expr.split('<=')
                expr = f"({parts[0].strip()}) - ({parts[1].strip()})"
                kind = 'le'
            elif '=' in expr and kind == 'eq':
                parts = expr.split('=')
                if len(parts) == 2:
                    expr = f"({parts[0].strip()}) - ({parts[1].strip()})"
            
            kkt_constraints.append({
                'expression': expr,
                'kind': kind,
                'rhs': rhs
            })
        
        # Llamar al solver KKT pedagógico
        solver = KKTSolver(
            objective_expr=objective_expr,
            variables=variables,
            constraints=kkt_constraints,
            is_maximization=is_maximization
        )
        result = solver.solve()
        
        return Response({
            'success': result.get('status') == 'success',
            'explanation': result.get('explanation', ''),
            'metadata': {
                'x_star': result.get('solution'),
                'f_star': result.get('optimal_value'),
                'candidates': result.get('candidates', []),
                'is_maximization': is_maximization,
            }
        })
        
    except Exception as e:
        import traceback
        return Response({
            'success': False,
            'error': f'Error al resolver: {str(e)}',
            'traceback': traceback.format_exc()
        }, status=500)


@api_view(["POST"])
def solve_gradient_manual(request):
    """
    Endpoint para resolver problemas con Gradiente Descendente desde formulario manual.
    Recibe: objective_expr, variables, x0 (opcional), tol (opcional), max_iter (opcional)
    Retorna: explanation (Markdown con LaTeX + gráficas), metadata
    """
    from .core.solver_gradiente import resolver_descenso_gradiente
    
    try:
        data = request.data
        objective_expr = data.get('objective_expr', '').strip()
        variables = data.get('variables', [])
        x0 = data.get('x0', None)
        tol = float(data.get('tol', 1e-6))
        max_iter = int(data.get('max_iter', 200))
        
        if not objective_expr:
            return Response({'error': 'Función objetivo requerida'}, status=400)
        if not variables:
            return Response({'error': 'Variables requeridas'}, status=400)
        
        # Llamar al solver de Gradiente
        result = resolver_descenso_gradiente(
            expresion_objetivo=objective_expr,
            nombres_variables=variables,
            x_inicial=x0,
            tolerancia=tol,
            max_iteraciones=max_iter
        )
        
        # Generar explicación pedagógica
        explanation = _generate_gradient_explanation(
            objective_expr, variables, result, x0, tol, max_iter
        )
        
        return Response({
            'success': result.get('status') == 'ok',
            'explanation': explanation,
            'metadata': {
                'x_star': result.get('x_star'),
                'f_star': result.get('f_star'),
                'iterations': result.get('iterations', []),
                'iterations_count': len(result.get('iterations', [])),
                'plot_data': result.get('plot_data'),
            }
        })
        
    except Exception as e:
        import traceback
        return Response({
            'success': False,
            'error': f'Error al resolver: {str(e)}',
            'traceback': traceback.format_exc()
        }, status=500)


def _generate_gradient_explanation(objective_expr, variables, result, x0, tol, max_iter):
    """Genera explicación pedagógica paso a paso para Gradiente Descendente."""
    import sympy as sp
    
    lines = []
    
    # Título
    lines.append("# 📉 MÉTODO DE GRADIENTE DESCENDENTE")
    lines.append("")
    lines.append("**Optimización iterativa siguiendo la dirección de máximo descenso**")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # PASO 1: Presentación
    lines.append("## PASO 1: PRESENTACIÓN DEL PROBLEMA")
    lines.append("")
    vars_str = ', '.join(variables)
    lines.append(f"**Función objetivo a minimizar:**")
    lines.append("")
    lines.append(f"$$f({vars_str}) = {objective_expr}$$")
    lines.append("")
    lines.append(f"**Variables:** ${vars_str}$")
    lines.append("")
    
    x0_str = str(x0) if x0 else "origen (ceros)"
    lines.append(f"**Punto inicial:** $x_0 = {x0_str}$")
    lines.append(f"**Tolerancia:** $\\epsilon = {tol}$")
    lines.append(f"**Iteraciones máximas:** {max_iter}")
    lines.append("")
    
    # PASO 2: El método
    lines.append("## PASO 2: EL ALGORITMO")
    lines.append("")
    lines.append("El Gradiente Descendente sigue estos pasos en cada iteración $k$:")
    lines.append("")
    lines.append("1. **Calcular el gradiente** $\\nabla f(x_k)$ en el punto actual")
    lines.append("2. **Verificar convergencia**: Si $\\|\\nabla f(x_k)\\| < \\epsilon$, terminar")
    lines.append("3. **Búsqueda de línea**: Encontrar el paso óptimo $\\alpha_k$")
    lines.append("4. **Actualizar posición**: $x_{k+1} = x_k - \\alpha_k \\nabla f(x_k)$")
    lines.append("5. **Repetir** hasta convergencia o agotar iteraciones")
    lines.append("")
    
    lines.append("### 🔍 Búsqueda de Línea (Golden Section)")
    lines.append("")
    lines.append("Para encontrar el paso óptimo $\\alpha_k$, resolvemos:")
    lines.append("")
    lines.append("$$\\alpha_k = \\arg\\min_{\\alpha > 0} f(x_k - \\alpha \\nabla f(x_k))$$")
    lines.append("")
    lines.append("Usamos el método de **sección dorada** que divide el intervalo")
    lines.append("en proporción áurea $\\phi = \\frac{1+\\sqrt{5}}{2}$ para encontrar el mínimo.")
    lines.append("")
    
    # PASO 3: Ejecución
    iterations = result.get('iterations', [])
    lines.append("## PASO 3: EJECUCIÓN DEL ALGORITMO")
    lines.append("")
    lines.append(f"**Total de iteraciones ejecutadas:** {len(iterations)}")
    lines.append("")
    
    # Mostrar algunas iteraciones clave
    lines.append("### Tabla de Iteraciones")
    lines.append("")
    lines.append("| k | $x_k$ | $f(x_k)$ | $\\|\\nabla f\\|$ | $\\alpha_k$ |")
    lines.append("|---|-------|----------|-----------------|-------------|")
    
    iters_to_show = min(8, len(iterations))
    for i in range(iters_to_show):
        it = iterations[i]
        x_k = it.get('x_k', [])
        x_k_str = ', '.join([f"{v:.4f}" for v in x_k]) if x_k else '-'
        f_k = it.get('f_k', 0)
        grad_norm = it.get('grad_norm', 0)
        alpha = it.get('alpha', 0)
        lines.append(f"| {it.get('k', i)} | ({x_k_str}) | {f_k:.6f} | {grad_norm:.6f} | {alpha:.6f} |")
    
    if len(iterations) > iters_to_show:
        lines.append(f"| ... | ... | ... | ... | ... |")
        # Mostrar última iteración
        last_it = iterations[-1]
        x_k = last_it.get('x_k', [])
        x_k_str = ', '.join([f"{v:.4f}" for v in x_k]) if x_k else '-'
        lines.append(f"| {last_it.get('k', len(iterations)-1)} | ({x_k_str}) | {last_it.get('f_k', 0):.6f} | {last_it.get('grad_norm', 0):.6f} | {last_it.get('alpha', 0):.6f} |")
    
    lines.append("")
    
    # PASO 4: Resultado
    lines.append("## PASO 4: RESULTADO FINAL")
    lines.append("")
    
    x_star = result.get('x_star', [])
    f_star = result.get('f_star', 0)
    
    lines.append("### 🎯 Punto Óptimo Encontrado")
    lines.append("")
    
    if x_star:
        for i, (var, val) in enumerate(zip(variables, x_star)):
            lines.append(f"$$${var}^* = {val:.6f}$$")
    
    lines.append("")
    lines.append("### 📊 Valor Mínimo")
    lines.append("")
    lines.append(f"$$f(x^*) = {f_star:.6f}$$")
    lines.append("")
    
    # PASO 5: Interpretación
    lines.append("## PASO 5: INTERPRETACIÓN PEDAGÓGICA")
    lines.append("")
    lines.append("### ¿Qué hicimos?")
    lines.append("")
    lines.append("1. **Partimos de un punto inicial** y calculamos el gradiente")
    lines.append("2. **El gradiente indica la dirección de máximo crecimiento**, así que vamos en sentido opuesto (descenso)")
    lines.append("3. **Optimizamos el tamaño del paso** para avanzar lo máximo posible en cada iteración")
    lines.append("4. **Repetimos hasta que el gradiente sea casi cero** (punto crítico)")
    lines.append("")
    
    lines.append("### 💡 Intuición Geométrica")
    lines.append("")
    lines.append("Imagina una bola rodando por una superficie. La bola siempre rueda en la dirección")
    lines.append("de mayor pendiente hacia abajo. El gradiente descendente imita este comportamiento,")
    lines.append("pero optimizando el tamaño de cada \"paso\" para converger más rápido.")
    lines.append("")
    
    # Notas sobre convergencia
    final_grad = iterations[-1].get('grad_norm', 0) if iterations else 0
    if final_grad < tol:
        lines.append("✅ **El algoritmo convergió exitosamente** (gradiente menor que la tolerancia)")
    else:
        lines.append("⚠️ **El algoritmo terminó por límite de iteraciones** (puede requerir más pasos)")
    lines.append("")
    
    lines.append("---")
    lines.append("")
    lines.append("### ✓ Procedimiento completado")
    lines.append("")
    
    return "\n".join(lines)


@api_view(["POST"])
def solve_qp_manual(request):
    """
    Endpoint para resolver problemas de Programación Cuadrática desde formulario manual.
    Recibe: objective_expr, variables, constraints (JSON)
    Retorna: explanation (Markdown con LaTeX), metadata
    """
    from .core.solver_cuadratico import resolver_qp
    
    try:
        data = request.data
        objective_expr = data.get('objective_expr', '').strip()
        variables = data.get('variables', [])
        constraints = data.get('constraints', [])
        
        if not objective_expr:
            return Response({'error': 'Función objetivo requerida'}, status=400)
        if not variables:
            return Response({'error': 'Variables requeridas'}, status=400)
        
        # Preparar restricciones
        qp_constraints = []
        for c in constraints:
            expr = c.get('expr', c.get('expression', ''))
            kind = c.get('kind', 'ineq')
            
            # Normalizar expresiones
            if '>=' in expr:
                parts = expr.split('>=')
                expr = f"({parts[0].strip()}) - ({parts[1].strip()})"
                kind = 'ge'
            elif '<=' in expr:
                parts = expr.split('<=')
                expr = f"({parts[0].strip()}) - ({parts[1].strip()})"
                kind = 'le'
            elif '=' in expr and kind == 'eq':
                parts = expr.split('=')
                if len(parts) == 2:
                    expr = f"({parts[0].strip()}) - ({parts[1].strip()})"
            
            qp_constraints.append({
                'expr': expr,
                'kind': kind
            })
        
        # Llamar al solver QP
        result = resolver_qp(
            objective_expr=objective_expr,
            variables=variables,
            constraints=qp_constraints
        )
        
        return Response({
            'success': result.get('status') in ['success', 'educational_guide', 'optimal'],
            'explanation': result.get('explanation', ''),
            'metadata': {
                'x_star': result.get('x_star'),
                'f_star': result.get('f_star'),
                'status': result.get('status'),
                'steps': result.get('steps', []),
            }
        })
        
    except Exception as e:
        import traceback
        return Response({
            'success': False,
            'error': f'Error al resolver: {str(e)}',
            'traceback': traceback.format_exc()
        }, status=500)
