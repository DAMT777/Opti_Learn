from django.urls import re_path
from .consumers_ai import ChatConsumer

# Ruta WebSocket: /ws/chat/<uuid>/
websocket_urlpatterns = [
    re_path(r'^ws/chat/(?P<session_id>[0-9a-fA-F-]+)/$', ChatConsumer.as_asgi()),
]
