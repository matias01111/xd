"""
Configuración de base de datos para el Sistema de Reservación UDP
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Configuración de la base de datos
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:password@localhost:5432/reservas_udp"
)

# Crear engine de SQLAlchemy
engine = create_engine(DATABASE_URL)

# Crear sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos
Base = declarative_base()

def get_db():
    """Función para obtener una sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Inicializar la base de datos"""
    Base.metadata.create_all(bind=engine)

