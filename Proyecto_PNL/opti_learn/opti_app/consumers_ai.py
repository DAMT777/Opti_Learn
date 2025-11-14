import json
import asyncio
from typing import Any, Dict

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from .models import ChatSession, ChatMessage
from .core import analyzer, recommender_ai, solver_gradiente
from .ai import groq_service


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

            history = await self.get_history()
            messages = groq_service.build_messages_from_session(history, text)
            reply_payload: Dict[str, Any] = {}
            assistant_text = "Mensaje recibido."
            analysis_text = ""
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
                    assistant_text = (
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
                                assistant_text += (
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
                                assistant_text += f" El solver local falló: {solver_error}"
                        else:
                            assistant_text += " Por ahora solo resolvemos gradiente cuando no hay restricciones."
                    else:
                        assistant_text += " Actualmente solo se ejecuta el solver de gradiente sin restricciones."
                    if assistant_text != "Mensaje recibido.":
                        analysis_text = assistant_text
            except Exception:
                pass
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
                if reply_payload.get('analysis'):
                    assistant_text += (
                        "\n\nAnálisis preliminar: "
                        f"Variables: {reply_payload['analysis'].get('variables')} | "
                        f"Eq: {reply_payload['analysis'].get('recommendation', {}).get('variables')} | "
                        f"Ineq: {reply_payload['analysis'].get('recommendation', {}).get('method')}"
                )
            if analysis_text:
                assistant_text = f"{assistant_text}\n\n{analysis_text}"
            reply: Dict[str, Any] = {'type': 'assistant_message', 'text': assistant_text}
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
