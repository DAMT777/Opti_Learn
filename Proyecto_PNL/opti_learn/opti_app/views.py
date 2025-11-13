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
    title = titles.get(method_key, method_key)
    return render(request, 'methods/form.html', { 'method_key': method_key, 'title': title })


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
                solucion.explanation_final = recomendacion.get('rationale', '')
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

        return Response(SolutionSerializer(solucion).data)


class SolutionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Solution.objects.all().order_by('-created_at')
    serializer_class = SolutionSerializer
