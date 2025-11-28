from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    index, ParseProblemAPIView, ProblemViewSet, SolutionViewSet, 
    method_view, ai_chat, ai_prompt_health,
    solve_lagrange_manual, solve_differential_manual,
    solve_kkt_manual, solve_gradient_manual, solve_qp_manual
)


router = DefaultRouter()
router.register(r'problems', ProblemViewSet, basename='problem')
router.register(r'solutions', SolutionViewSet, basename='solution')


urlpatterns = [
    path('', index, name='index'),
    path('methods/<str:method_key>', method_view, name='method'),
    path('api/problems/parse', ParseProblemAPIView.as_view(), name='problems-parse'),
    path('api/ai/chat', ai_chat, name='ai-chat'),
    path('api/ai/prompt-health', ai_prompt_health, name='ai-prompt-health'),
    # Endpoints para formularios manuales (solución pedagógica paso a paso)
    path('api/methods/lagrange/solve', solve_lagrange_manual, name='solve-lagrange-manual'),
    path('api/methods/differential/solve', solve_differential_manual, name='solve-differential-manual'),
    path('api/methods/kkt/solve', solve_kkt_manual, name='solve-kkt-manual'),
    path('api/methods/gradient/solve', solve_gradient_manual, name='solve-gradient-manual'),
    path('api/methods/qp/solve', solve_qp_manual, name='solve-qp-manual'),
    path('api/', include(router.urls)),
]
