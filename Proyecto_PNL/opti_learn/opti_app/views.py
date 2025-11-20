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
from .core import solver_gradiente
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

    base_lines = []
    base_lines.append("Explicación educativa (Gradiente Descendente)")
    base_lines.append(f"- Problema: minimizar f({vars_str}) = {objective}")
    base_lines.append(f"- Punto inicial: x0 = {x0 if x0 is not None else 'no especificado'}")
    base_lines.append(f"- Criterio de paro: ||∇f|| < {tol} o k ≥ {max_iter}")
    base_lines.append("")
    base_lines.append("Paso a paso:")
    base_lines.append("1) Calcular f(x) y el gradiente en el punto actual.")
    base_lines.append("2) Elegir α_k por búsqueda de línea (Armijo).")
    base_lines.append("3) Actualizar x_{k+1} = x_k - α_k · ∇f(x_k).")
    base_lines.append("4) Repetir hasta cumplir el criterio de paro.")
    base_lines.append("")
    base_lines.append("Resultado del solver:")
    base_lines.append(f"- Iteraciones ejecutadas: {k_final + 1}")
    base_lines.append(f"- Punto óptimo estimado: x* ≈ {x_star}")
    base_lines.append(f"- Valor mínimo: f(x*) ≈ {f_star}")
    base_text = "\n".join(base_lines)

    # Intentar generar una versión con el modelo IA si está disponible
    try:
        messages = [
            {
                "role": "system",
                "content": (
                    "Eres un tutor amable y pedagógico. Explica en español el procedimiento del gradiente "
                    "descendente de forma breve (6-8 viñetas máximo), enfatizando qué se calculó y por qué."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Función: f({vars_str}) = {objective}\n"
                    f"Punto inicial: {x0}\n"
                    f"Tolerancia: {tol}, Iteraciones máx: {max_iter}\n"
                    f"Iteraciones ejecutadas: {k_final + 1}\n"
                    f"Resultado: x* = {x_star}, f* = {f_star}\n"
                    "Redacta el procedimiento pedagógico sin usar JSON, solo texto con viñetas."
                ),
            },
        ]
        ai_text = groq_service.chat_completion(messages)
        if ai_text:
            return ai_text
    except Exception:
        pass

    return base_text

    lines = []
    lines.append("Procedimiento paso a paso (Gradiente Descendente):")
    lines.append(f"- Variables: {vars_str}. Tolerancia: {tol}. Iteraciones max: {max_iter}.")
    if x0:
        lines.append(f"- Punto inicial: x0 = {x0}.")
    lines.append("- 1) Calcular f(x) y su gradiente en el punto actual.")
    lines.append("- 2) Elegir alpha_k por busqueda de linea (Armijo).")
    lines.append("- 3) Actualizar x_{k+1} = x_k - alpha_k * grad f(x_k).")
    lines.append("- 4) Repetir hasta que ||grad f|| < tolerancia o se alcance el maximo de iteraciones.")
    lines.append("")
    lines.append("Resultado:")
    lines.append(f"- Iteraciones ejecutadas: {k_final + 1}")
    lines.append(f"- Punto optimo estimado: x* = {x_star}")
    lines.append(f"- Valor minimo: f(x*) = {f_star}")
    return "\n".join(lines)


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
                        notes=it.get('notes', '')
                    ))
                Iteration.objects.bulk_create(iteraciones_obj)
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
