from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.chat_context import ChatContext
from app.models.chat import Chat
from app.models.user import User

def get_observed_documents(db: Session):
    try:
        # Hacemos un join de ChatContext con Chat y User
        results = (
            db.query(ChatContext, Chat, User)
            .join(Chat, ChatContext.chat_id == Chat.id)
            .join(User, Chat.user_id == User.id)
            .order_by(ChatContext.created_at.desc())
            .all()
        )
        
        docs = []
        for context, chat, user in results:
            docs.append({
                "id": context.id,
                "chat_id": context.chat_id,
                "filename": context.filename,
                "extracted_text": context.extracted_text,
                "created_at": context.created_at,
                "chat_title": chat.title,
                "chat_state": chat.state,
                "user_name": user.full_name,
                "user_email": user.email
            })
        return docs
    finally:
        db.close()

def update_document_text(db: Session, document_id: str, new_text: str):
    try:
        doc = db.query(ChatContext).filter(ChatContext.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        
        doc.extracted_text = new_text
        db.commit()
        db.refresh(doc)
        return doc
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al actualizar el documento: {str(e)}")
    finally:
        db.close()

def approve_chat(db: Session, chat_id: str):
    try:
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            raise HTTPException(status_code=404, detail="Trámite no encontrado")
        
        chat.state = "completed"
        db.commit()
        db.refresh(chat)
        return {"status": "success", "message": "Trámite aprobado con éxito", "chat_state": chat.state}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al aprobar el trámite: {str(e)}")
    finally:
        db.close()

def observe_chat(db: Session, chat_id: str):
    try:
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            raise HTTPException(status_code=404, detail="Trámite no encontrado")
        
        chat.state = "action"
        db.commit()
        db.refresh(chat)
        return {"status": "success", "message": "Trámite observado con éxito", "chat_state": chat.state}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al observar el trámite: {str(e)}")
    finally:
        db.close()

def change_user_role(db: Session, user_id: int, new_role: str):
    """
    Cambia el rol de un usuario. Solo administradores pueden hacerlo.
    Roles permitidos: 'user', 'admin'
    """
    try:
        if new_role not in ["user", "admin"]:
            raise HTTPException(status_code=400, detail="Rol no válido. Roles permitidos: 'user', 'admin'")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        user.role = new_role
        db.commit()
        db.refresh(user)
        
        return {
            "status": "success",
            "message": f"Rol del usuario actualizado a '{new_role}'",
            "user_id": user.id,
            "user_email": user.email,
            "user_role": user.role
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al cambiar el rol del usuario: {str(e)}")
    finally:
        db.close()

def get_all_users(db: Session):
    """
    Obtiene la lista de todos los usuarios con su información.
    Solo administradores pueden acceder a esto.
    """
    try:
        users = db.query(User).all()
        return [
            {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "document_type": user.document_type,
                "document_number": user.document_number,
                "role": user.role
            }
            for user in users
        ]
    finally:
        db.close()
