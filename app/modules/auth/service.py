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

# =========================
# UTILIDADES SEGURAS
# =========================

def clean_text(text: str) -> str:
    if not text:
        return ""

    return (
        unicodedata.normalize("NFD", text)
        .encode("ascii", "ignore")
        .decode("utf-8")
        .replace(",", "")
        .lower()
        .strip()
    )


def validate_name(name: str):
    if not name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")

    if not re.fullmatch(r"[a-zA-ZáéíóúÁÉÍÓÚñÑ ]+", name):
        raise HTTPException(
            status_code=400,
            detail="El nombre solo debe contener letras y espacios"
        )

    if len(name.strip()) < 3:
        raise HTTPException(
            status_code=400,
            detail="El nombre es demasiado corto"
        )


def validate_dni(dni: str):
    if not re.fullmatch(r"\d{8}", dni):
        raise HTTPException(
            status_code=400,
            detail="El DNI debe tener exactamente 8 números"
        )


def validate_ce(ce: str):
    if not re.fullmatch(r"[a-zA-Z0-9]{9,12}", ce):
        raise HTTPException(
            status_code=400,
            detail="Carné inválido (9 a 12 caracteres alfanuméricos)"
        )


def validate_password(password: str):
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Mínimo 8 caracteres")

    if not re.search(r"[A-Z]", password):
        raise HTTPException(status_code=400, detail="Debe tener una mayúscula")

    if not re.search(r"[0-9]", password):
        raise HTTPException(status_code=400, detail="Debe tener un número")

def logout_user():
    return {
        "status": "success",
        "message": "Sesión cerrada correctamente"
    }


# =========================
# LOGIN
# =========================

def login_with_dni(data: LoginRequest):
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.document_number == data.document).first()

        if not user or not verify_password_hash(data.password, user.password):
            raise HTTPException(status_code=401, detail="Credenciales inválidas")

        return {
            "access_token": create_token({
                "user_id": user.id,
                "email": user.email
            }),
            "token_type": "bearer"
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        db.close()


# =========================
# REGISTER DNI
# =========================

def register_with_dni(data: DNIRegisterRequest):
    db: Session = SessionLocal()

    try:
        validate_dni(data.dni)
        validate_name(data.fullname)
        validate_password(data.password)

        if db.query(User).filter(User.email == data.email).first():
            raise HTTPException(status_code=400, detail="Correo ya registrado")

        if db.query(User).filter(User.document_number == data.dni).first():
            raise HTTPException(status_code=400, detail="DNI ya registrado")

        reniec = ReniecClient()
        reniec_data = reniec.validate_dni(data.dni)

        if not reniec_data:
            raise HTTPException(status_code=400, detail="DNI no válido")

        if clean_text(reniec_data.get("nombre_completo")) != clean_text(data.fullname):
            raise HTTPException(status_code=400, detail="Nombre no coincide con RENIEC")

        user = User(
            full_name=data.fullname,
            email=data.email,
            password=hash_password(data.password),
            document_type="dni",
            document_number=data.dni
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return {
            "access_token": create_token({
                "user_id": user.id,
                "email": user.email
            }),
            "token_type": "bearer"
        }

    except HTTPException as e:
        db.rollback()
        raise e

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        db.close()


# =========================
# REGISTER CE
# =========================

def register_with_immigrationcard(data: ImmigrationCardRegisterRequest):
    db: Session = SessionLocal()

    try:
        validate_ce(data.immigration_card)
        validate_name(data.fullname)
        validate_password(data.password)

        if db.query(User).filter(User.email == data.email).first():
            raise HTTPException(status_code=400, detail="Correo ya registrado")

        if db.query(User).filter(User.document_number == data.immigration_card).first():
            raise HTTPException(status_code=400, detail="Carné ya registrado")

        user = User(
            full_name=data.fullname,
            email=data.email,
            password=hash_password(data.password),
            document_type="immigration_card",
            document_number=data.immigration_card
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return {
            "access_token": create_token({
                "user_id": user.id,
                "email": user.email
            }),
            "token_type": "bearer"
        }

    except HTTPException as e:
        db.rollback()
        raise e

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        db.close()


def get_user_profile(user_id: int, db: Session):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

def update_user_email(user_id: int, new_email: str, db: Session):
    existing_user = db.query(User).filter(User.email == new_email).first()
    if existing_user:
        if existing_user.id != user_id:
            raise HTTPException(status_code=400, detail="El correo ya está registrado por otro usuario")
        else:
            return existing_user

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    user.email = new_email
    db.commit()
    db.refresh(user)
    return user

    