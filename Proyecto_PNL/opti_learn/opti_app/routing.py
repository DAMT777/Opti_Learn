from django.urls import path
from .consumers_ai import ChatConsumer


websocket_urlpatterns = [
    path('ws/chat/<uuid:session_id>/', ChatConsumer.as_asgi()),
]
