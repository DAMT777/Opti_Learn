import json
from typing import Any, Dict

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from .models import ChatSession, ChatMessage
from .core import analyzer, recommender_ai, solver_gradiente


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
            reply_payload: Dict[str, Any] = {}
            explanation = "Mensaje recibido."
            try:
                payload = json.loads(text)
                if isinstance(payload, dict) and 'objective_expr' in payload:
                    problema = {
                        'objective_expr': payload.get('objective_expr'),
                        'variables': payload.get('variables'),
                        'constraints': payload.get('constraints') or payload.get('constraints_raw') or [],
                    }
                    meta = analyzer.analyze_problem(problema)
                    rec = recommender_ai.recommend(meta)
                    explanation = (
                        f"Variables: {meta.get('variables')} • "
                        f"Eq: {meta.get('has_equalities')} • "
                        f"Ineq: {meta.get('has_inequalities')} • "
                        f"Método sugerido: {rec.get('method')}."
                    )
                    reply_payload['analysis'] = {
                        'variables': meta.get('variables'),
                        'objective_expr': meta.get('objective_expr'),
                        'constraints': meta.get('constraints_normalized'),
                        'recommendation': rec,
                    }

                    can_run_gradient = not meta.get('has_equalities') and not meta.get('has_inequalities')
                    metodo_usuario = payload.get('method') or rec.get('method')
                    wants_gradient = metodo_usuario == 'gradient'
                    if wants_gradient:
                        if can_run_gradient:
                            try:
                                resultado = solver_gradiente.solve(
                                    objective_expr=problema['objective_expr'],
                                    variables=meta.get('variables') or [],
                                    x0=payload.get('x0'),
                                    tol=float(payload.get('tol', 1e-6)),
                                    max_iter=int(payload.get('max_iter', 200)),
                                )
                                f_star = resultado.get('f_star')
                                f_star_display = (
                                    f"{f_star:.6g}" if isinstance(f_star, (int, float)) else "N/D"
                                )
                                iter_count = len(resultado.get('iterations', []))
                                explanation += (
                                    f" Gradiente descendente alcanzó f*≈{f_star_display} "
                                    f"en {iter_count} iteraciones."
                                )
                                reply_payload['plot'] = {
                                    'type': 'trajectory',
                                    'method': 'gradient',
                                    'variables': meta.get('variables'),
                                    'iterations': resultado.get('iterations', []),
                                    'x_star': resultado.get('x_star'),
                                    'f_star': resultado.get('f_star'),
                                }
                            except Exception as solver_error:
                                explanation += f" El solver local falló: {solver_error}"
                        else:
                            explanation += " Por ahora solo resolvemos gradiente cuando no hay restricciones."
                    else:
                        explanation += " Actualmente solo se ejecuta el solver de gradiente sin restricciones."
            except Exception:
                pass

            reply: Dict[str, Any] = {'type': 'assistant_message', 'text': explanation}
            if reply_payload:
                reply['payload'] = reply_payload
            await self.save_message('assistant', reply['text'], payload=reply.get('payload'))
            await self.send_json(reply)
        else:
            await self.send_json({'type': 'status', 'stage': 'idle', 'detail': 'Mensaje no reconocido'})

    async def send_json(self, content):
        await self.send(text_data=json.dumps(content))

    @database_sync_to_async
    def ensure_session(self):
        ChatSession.objects.get_or_create(id=self.session_id)

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
