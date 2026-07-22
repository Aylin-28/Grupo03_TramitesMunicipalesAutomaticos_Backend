from sqlalchemy.orm import Session

from app.integrations.ai.provider.gemini import gemini_client
from app.integrations.ai.provider.llama.llama_client import llama_client
from app.models.chat import Chat
from app.models.message import Message
from app.models.step import Step
from app.modules.ai.schemas import AskRequest, AskResponse

async def ask_strategy_llama(data: AskRequest, db: Session, user_id: int) -> AskResponse:
    try:

        chat_existente = db.query(Chat).filter(Chat.id == data.chat_id).first()

        if not chat_existente:
            chat_existente = Chat(id=data.chat_id, user_id=user_id, title=data.question[:20] + "...")
            db.add(chat_existente)
            db.commit()

        contexto_del_archivo = ""

        if data.file and data.file.filename:
            print(f"[Strategy Llama] Extrayendo texto en memoria de: {data.file.filename}")
            
            file_bytes = await data.file.read()
            mime_type = data.file.content_type
            
            texto_completo_del_archivo = gemini_client.textualizar(
                file_bytes=file_bytes,
                mime_type=mime_type
            )
            
            contexto_del_archivo = (
                f"\n\n[DOCUMENTO ADJUNTO APORTADO POR EL USUARIO ({data.file.filename})]\n"
                f"{texto_completo_del_archivo}\n"
                f"[FIN DEL DOCUMENTO ADJUNTO]"
            )

            # Guardar el documento en la base de datos (ChatContext)
            import uuid
            from app.models.chat_context import ChatContext
            
            doc_uuid = str(uuid.uuid4())
            chat_context_record = ChatContext(
                id=doc_uuid,
                chat_id=data.chat_id,
                filename=data.file.filename,
                extracted_text=texto_completo_del_archivo
            )
            db.add(chat_context_record)
            
            # Cambiar el estado del chat a 'action' (Acción Requerida) para que pase a la bandeja admin
            chat_existente.state = "action"


        mensajes_db = db.query(Message).filter(Message.chat_id == data.chat_id).order_by(Message.created_at.desc()).limit(3).all()

        mensajes_db.reverse()

        historial_previo = [{"role": m.role, "content": m.content} for m in mensajes_db]

        mensaje_con_contexto = f"{data.question}{contexto_del_archivo}"
        print("[Strategy Llama] Solicitando respuesta a llama_client...")

        resultado_json = llama_client.send_message(
            mensaje_actual=mensaje_con_contexto,
            historial_previo=historial_previo
        )

        respuesta_ia = resultado_json.get("answer", "Sin respuesta.")
        steps_ia = resultado_json.get("steps") if resultado_json.get("has_steps") else None

        nuevo_msg_user = Message(chat_id=data.chat_id, role="user", content=data.question)
        nuevo_msg_ia = Message(chat_id=data.chat_id, role="assistant", content=respuesta_ia)
        if steps_ia:
            for idx, paso_texto in enumerate(steps_ia):
                nuevo_paso = Step(priority=idx + 1, content=paso_texto)
                nuevo_msg_ia.steps.append(nuevo_paso)

        db.add_all([nuevo_msg_user, nuevo_msg_ia])
        db.commit()

        pasos_map = []
        if steps_ia:
            pasos_db = db.query(Step).filter(Step.message_id == nuevo_msg_ia.id).all()
            pasos_map = [{"id": p.id, "state": p.state, "priority": p.priority, "message": p.content} for p in pasos_db]
            
        return AskResponse(
            chat_id=data.chat_id,
            answer=respuesta_ia,
            steps=pasos_map
        )
    
    except Exception as e:
        db.rollback()
        print(f"[Strategy Llama - ERROR]: {e}")
        return AskResponse(
            chat_id=data.chat_id, 
            answer="Error con la estrategia de Llama o la DB", 
            steps=None
        )