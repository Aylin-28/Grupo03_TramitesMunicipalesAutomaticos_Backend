from fastapi import HTTPException
from sqlalchemy.orm import Session
import re
import unicodedata

from app.modules.auth.schemas import (
    DNIRegisterRequest,
    ImmigrationCardRegisterRequest,
    LoginRequest
)

from app.models.user import User

from app.db.session import SessionLocal

from app.integrations.reniec.client import ReniecClient

from app.core.security import (
    create_token,
    hash_password,
    verify_password_hash
)


# =========================================
# UTILIDADES
# =========================================

# Este funciona en los nombres del form y de RENIEC. Les da un formato para compararlos y ver si coinciden
def clean_text(text: str):

    return (
        unicodedata.normalize("NFD", text)
        .encode("ascii", "ignore")
        .decode("utf-8")
        .replace(",", "")
        .lower()
        .strip()
    )

def validate_password(password: str):

    # La contrasena debe tener minimo 8 caracteres
    if len(password) < 8:
        raise HTTPException(
            status_code=400,
            detail="La contraseña debe tener mínimo 8 caracteres"
        )
    # La contrasena debe tener al menos una mayuscula
    if not re.search(r"[A-Z]", password):
        raise HTTPException(
            status_code=400,
            detail="La contraseña debe tener al menos una mayúscula"
        )

    if not re.search(r"[0-9]", password):
        raise HTTPException(
            status_code=400,
            detail="La contraseña debe tener al menos un número"
        )

def login_with_dni(data : LoginRequest):
    ## COMPLETAR LOGICA
    return None

# Registro con dni

def register_with_dni(data: DNIRegisterRequest):

    db: Session = SessionLocal()

    try:

        # Valida dni

        if len(data.dni) != 8:
            raise HTTPException(
                status_code=400,
                detail="El DNI debe tener 8 dígitos"
            )

        if not data.dni.isdigit():
            raise HTTPException(
                status_code=400,
                detail="El DNI solo debe contener números"
            )

        # Valida contrasena

        validate_password(data.password)

        # Verifica que el email o el dni no existan en la bd aun.

        existing_email = db.query(User).filter(
            User.email == data.email
        ).first()

        if existing_email:
            raise HTTPException(
                status_code=400,
                detail="El correo ya existe"
            )

        existing_dni = db.query(User).filter(
            User.document_number == data.dni
        ).first()

        if existing_dni:
            raise HTTPException(
                status_code=400,
                detail="El DNI ya existe"
            )

        
        # Creamos el objeto ReniecCliet para acceder al metodo de validar dni
        reniec = ReniecClient()

        # Verificamos que el dni existe
        reniec_data = reniec.validate_dni(
            data.dni
        )

        if not reniec_data:
            raise HTTPException(
                status_code=400,
                detail="DNI no válido"
            )

        # Verificamos que el nombre ingresado coincida con el de RENIEC

        api_name = clean_text(
            reniec_data.get("nombre_completo", "")
        )

        form_name = clean_text(
            data.fullname
        )

        # Convertimos los nombres en listas de palabras

        api_words = api_name.split()
        form_words = form_name.split()

        matches = (
            len(api_words) == len(form_words)
            and all(word in form_words for word in api_words)
        )

        if not matches:
            raise HTTPException(
                status_code=400,
                detail="El nombre no coincide con RENIEC"
         )
        
        if not data.user_type.strip():
            raise HTTPException(
            status_code=400,
            detail="El tipo de usuario es obligatorio"
            )

        # Hasheamos la contrasena

        hashed_password = hash_password(
            data.password
        )

        

        # Creamos un objeto de tipo Usuario

        user = User(
            full_name=data.fullname,
            email=data.email,
            password=hashed_password,
            document_type="dni",
            document_number=data.dni,
            user_type=data.user_type
        )

        # Guardamos en la bd al usuario (el id se genera automaticamente)
        db.add(user)

        # Confirmamos nuestros cambios
        db.commit()

        # Actualiza el objeto user con los datos reales guardados en la BD.
        db.refresh(user)

        token = create_token({
            "user_id": user.id,   # Tiene el valor del id del usuario guardado gracias a refresh
            "email": user.email,   # Tiene el valor del email del usuario guardado gracias a refresh
            "user_type:" : user.user_type
        })

        return {
            "access_token": token,
            "token_type": "bearer"
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

    
# Registro con carne de extranjeria

def register_with_immigrationcard(
    data: ImmigrationCardRegisterRequest
):

    db: Session = SessionLocal()

    try:

        # Valida contrasena

        validate_password(data.password)

        # Verifica que el email y el carnet no existan aun

        existing_email = db.query(User).filter(
            User.email == data.email
        ).first()

        if existing_email:
            raise HTTPException(
                status_code=400,
                detail="El correo ya existe"
            )

        existing_document = db.query(User).filter(
            User.document_number == data.immigration_card
        ).first()

        if existing_document:
            raise HTTPException(
                status_code=400,
                detail="El carnet ya existe"
            )
        
        if not data.user_type.strip():
            raise HTTPException(
            status_code=400,
            detail="El tipo de usuario es obligatorio"
            )

        # Hashea la contrasena

        hashed_password = hash_password(
            data.password
        )

        # Crea el usuario

        user = User(
            full_name=data.fullname,
            email=data.email,
            password=hashed_password,
            document_type="immigration_card",
            document_number=data.immigration_card
        )

        db.add(user)

        db.commit()

        db.refresh(user)

        # Crea el token

        token = create_token({
            "user_id": user.id,
            "email": user.email
        })

        return {
            "access_token": token,
            "token_type": "bearer"
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
