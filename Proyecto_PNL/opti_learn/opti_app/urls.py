from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import index, ParseProblemAPIView, ProblemViewSet, SolutionViewSet, method_view, ai_chat, ai_prompt_health


router = DefaultRouter()
router.register(r'problems', ProblemViewSet, basename='problem')
router.register(r'solutions', SolutionViewSet, basename='solution')


urlpatterns = [
    path('', index, name='index'),
    path('methods/<str:method_key>', method_view, name='method'),
    path('api/problems/parse', ParseProblemAPIView.as_view(), name='problems-parse'),
    path('api/ai/chat', ai_chat, name='ai-chat'),
    path('api/ai/prompt-health', ai_prompt_health, name='ai-prompt-health'),
    path('api/', include(router.urls)),
]
