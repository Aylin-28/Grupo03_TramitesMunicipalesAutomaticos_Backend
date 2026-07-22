from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import init_db
from app.db.session import Base, engine
from app.api.router import api_router
from app.db.init_db import init_data

from app.models import *

Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_data()
    yield

app = FastAPI(
    title="API de Trámites Municipales",
    description="""
    API encargada de gestionar autenticación, consultas a IA y feedback.

    Funcionalidades:
    - Registro e inicio de sesión.
    - Consultas al asistente de IA.
    - Continua tus tramites donde los dejaste
    - Envío de comentarios y sugerencias.

    """,
    version="1.0.0",
    lifespan=lifespan
)

origins = [
    "http://localhost:4200",
    "https://tramitesmunicipalesweb.onrender.com",
    "https://tramitesmunicipalesweb2.onrender.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")