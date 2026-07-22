from app.db.session import SessionLocal
from app.models.feedback_category import FeedbackCategory
from app.models.chat_context import ChatContext
from app.models.chat import Chat
from app.models.user import User
import uuid

def init_data():
    db = SessionLocal()
    try:
        # Seeder de categorías
        if db.query(FeedbackCategory).count() == 0:
            categories = [
                FeedbackCategory(title="Matrimonio Civil", description="..."),
                FeedbackCategory(title="Actas de Nacimiento", description="..."),
                FeedbackCategory(title="Bienes y Propiedades", description="...")
            ]
            db.add_all(categories)
            db.commit()

        if db.query(ChatContext).count() == 0:
            action_chats = db.query(Chat).filter(Chat.state == "action").all()
            
            if not action_chats:
                first_user = db.query(User).first()
                if not first_user:
                    from app.core.security import hash_password
                    first_user = User(
                        full_name="AGIP RUBIO RICARDO GERMAN",
                        email="user@example.com",
                        password=hash_password("Prueba123"),
                        document_type="DNI",
                        document_number="27440013"
                    )
                    db.add(first_user)
                    db.commit()
                    db.refresh(first_user)
                
                chat1 = Chat(id="217365", user_id=first_user.id, title="Pasos para Matrimonio Civil", state="action")
                chat2 = Chat(id="597357", user_id=first_user.id, title="Registro de Acta de Nacimiento", state="action")
                chat3 = Chat(id="105873", user_id=first_user.id, title="Validación de Impuesto Predial", state="action")
                db.add_all([chat1, chat2, chat3])
                db.commit()
                action_chats = [chat1, chat2, chat3]

            mock_docs = [
                {
                    "chat_id": "217365",
                    "filename": "acta_nacimiento_ricardo.pdf",
                    "extracted_text": "ACTA DE NACIMIENTO\nNombre del Titular: Ricardo German Agip Rubio\nFecha de Registro: 15 de Mayo de 1995\nLugar: Lince, Lima\n\n[OBSERVACIÓN ADMINISTRATIVA]\nEl sello de la municipalidad de origen está parcialmente borroso en la esquina inferior izquierda. Por favor, verificar el código de barra digital o re-escanear el documento para corregir la nitidez."
                },
                {
                    "chat_id": "597357",
                    "filename": "solicitud_matrimonio_civil.pdf",
                    "extracted_text": "SOLICITUD DE MATRIMONIO CIVIL\nContrayente A: Ricardo German Agip Rubio (DNI 27440013)\nContrayente B: Maria Paula Gomez Diaz (DNI 44556677)\n\n[OBSERVACIÓN ADMINISTRATIVA]\nFalta adjuntar la firma digital o manuscrita del testigo número 2 en la sección de declaraciones juradas (Página 3). Es requisito obligatorio para continuar."
                },
                {
                    "chat_id": "105873",
                    "filename": "recibo_servicios_luz.pdf",
                    "extracted_text": "RECIBO DE ENERGÍA ELÉCTRICA - ENEL\nSuministro: 2984572-1\nDirección: Av. Arequipa 1234, Lince\nMes de Consumo: Enero 2026\n\n[OBSERVACIÓN ADMINISTRATIVA]\nEl recibo presentado corresponde a un periodo superior a los 3 meses de antigüedad permitidos. Por favor, subir el recibo del mes en curso o del mes anterior inmediato."
                }
            ]

            for doc in mock_docs:
                chat_id = doc["chat_id"]
                exists = db.query(Chat).filter(Chat.id == chat_id).first()
                if not exists and len(action_chats) > 0:
                    # Si el chat específico no existe en la base de datos local, usar uno existente
                    chat_id = action_chats[0].id

                new_doc = ChatContext(
                    id=str(uuid.uuid4()),
                    chat_id=chat_id,
                    filename=doc["filename"],
                    extracted_text=doc["extracted_text"]
                )
                db.add(new_doc)
            db.commit()
    finally:
        db.close()
