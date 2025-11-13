import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from .models import ChatSession, ChatMessage
from .core import analyzer, recommender_ai


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs'].get('session_id')
        self.group_name = f"chat_{self.session_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        # Garantizar que la sesión existe
        await self.ensure_session()
        await self.accept()
        await self.send_json({
            'type': 'status',
            'stage': 'connected',
            'detail': 'Conexión establecida'
        })

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
            # Sugerencia mínima: si viene un JSON con objective_expr, intenta analizar
            explanation = "Mensaje recibido."
            try:
                payload = json.loads(text)
                if isinstance(payload, dict) and 'objective_expr' in payload:
                    meta = analyzer.analyze_problem(payload)
                    rec = recommender_ai.recommend(meta)
                    explanation = (
                        f"Variables: {meta.get('variables')} • "
                        f"Eq: {meta.get('has_equalities')} • Ineq: {meta.get('has_inequalities')} • "
                        f"Cuadrática: {meta.get('is_quadratic')} → Método sugerido: {rec.get('method')}"
                    )
            except Exception:
                pass

            reply = {'type': 'assistant_message', 'text': explanation}
            await self.save_message('assistant', reply['text'])
            await self.send_json(reply)
        else:
            await self.send_json({'type': 'status', 'stage': 'idle', 'detail': 'Mensaje no reconocido'})

    async def send_json(self, content):
        await self.send(text_data=json.dumps(content))

    @database_sync_to_async
    def ensure_session(self):
        ChatSession.objects.get_or_create(id=self.session_id)

    @database_sync_to_async
    def save_message(self, role: str, text: str):
        try:
            session = ChatSession.objects.get(id=self.session_id)
            ChatMessage.objects.create(session=session, role=role, content=text)
        except Exception:
            pass
