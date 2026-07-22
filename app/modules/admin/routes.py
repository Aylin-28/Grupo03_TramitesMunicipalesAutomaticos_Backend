from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.modules.auth.dependencies import get_admin_user
from app.modules.admin.schemas import DocumentObservedResponse, DocumentUpdate, UserRoleUpdate
from app.modules.admin import service

router = APIRouter(
    dependencies=[Depends(get_admin_user)]
)

@router.get("/documents", response_model=list[DocumentObservedResponse])
def get_documents(admin_user = Depends(get_admin_user), db: Session = Depends(get_db)):
    """
    Obtiene la lista de todos los documentos y metadatos asociados a los trámites.
    Solo accesible por administradores.
    """
    return service.get_observed_documents(db)

@router.put("/documents/{document_id}")
def update_document(
    document_id: str, 
    data: DocumentUpdate, 
    admin_user = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza/Corrige el contenido de texto extraído de un documento observado.
    Solo accesible por administradores.
    """
    return service.update_document_text(db, document_id, data.extracted_text)

@router.put("/chats/{chat_id}/approve")
def approve_procedure(
    chat_id: str, 
    admin_user = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Aprueba un trámite municipal cambiando su estado a 'completed'.
    Solo accesible por administradores.
    """
    return service.approve_chat(db, chat_id)

@router.put("/chats/{chat_id}/observe")
def observe_procedure(
    chat_id: str, 
    admin_user = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Observa un trámite municipal cambiando su estado a 'action'.
    Solo accesible por administradores.
    """
    return service.observe_chat(db, chat_id)

@router.get("/users")
def get_users(admin_user = Depends(get_admin_user), db: Session = Depends(get_db)):
    """
    Obtiene la lista de todos los usuarios del sistema.
    Solo accesible por administradores.
    """
    return service.get_all_users(db)

@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    data: UserRoleUpdate,
    admin_user = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza el rol de un usuario. Solo administradores pueden hacer esto.
    Roles permitidos: 'user', 'admin'
    """
    return service.change_user_role(db, user_id, data.role)
