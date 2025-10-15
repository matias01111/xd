"""
Servicio de Espacios (SPACE) - Sistema de Reservación UDP
Puerto: 5003
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

from database.db_config import get_db, init_db
from database.models import Espacio, Auditoria
from services.common.soa_protocol import SOAProtocol
from datetime import datetime

app = FastAPI(title="Servicio de Espacios - SPACE")

# Inicializar base de datos
init_db()

# Modelos Pydantic
class EspacioCreate(BaseModel):
    nombre: str
    tipo: str  # sala o cancha
    capacidad: int

class EspacioUpdate(BaseModel):
    nombre: Optional[str] = None
    tipo: Optional[str] = None
    capacidad: Optional[int] = None
    activo: Optional[bool] = None

class EspacioResponse(BaseModel):
    id: int
    nombre: str
    tipo: str
    capacidad: int
    activo: bool
    fecha_creacion: datetime

def log_audit(db: Session, tabla: str, accion: str, id_registro: int, datos_anteriores: dict, datos_nuevos: dict, id_usuario: int):
    """Registrar acción en auditoría"""
    audit = Auditoria(
        tabla_afectada=tabla,
        accion=accion,
        id_registro=id_registro,
        datos_anteriores=datos_anteriores,
        datos_nuevos=datos_nuevos,
        id_usuario=id_usuario
    )
    db.add(audit)
    db.commit()

@app.post("/spaces/create", response_model=EspacioResponse)
async def create_space(space_data: EspacioCreate, db: Session = Depends(get_db)):
    """Crear nuevo espacio"""
    try:
        # Validar tipo de espacio
        if space_data.tipo not in ['sala', 'cancha']:
            raise HTTPException(status_code=400, detail="Tipo de espacio debe ser 'sala' o 'cancha'")
        
        # Verificar si ya existe un espacio con el mismo nombre
        existing_space = db.query(Espacio).filter(Espacio.nombre == space_data.nombre).first()
        if existing_space:
            raise HTTPException(status_code=400, detail="Ya existe un espacio con ese nombre")
        
        # Crear nuevo espacio
        new_space = Espacio(
            nombre=space_data.nombre,
            tipo=space_data.tipo,
            capacidad=space_data.capacidad
        )
        
        db.add(new_space)
        db.commit()
        db.refresh(new_space)
        
        # Registrar en auditoría
        log_audit(db, "espacios", "crear", new_space.id_espacio, {}, {
            "nombre": space_data.nombre,
            "tipo": space_data.tipo,
            "capacidad": space_data.capacidad
        }, 1)  # ID del administrador que crea
        
        return EspacioResponse(
            id=new_space.id_espacio,
            nombre=new_space.nombre,
            tipo=new_space.tipo,
            capacidad=new_space.capacidad,
            activo=new_space.activo,
            fecha_creacion=new_space.fecha_creacion
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/spaces", response_model=List[EspacioResponse])
async def get_all_spaces(db: Session = Depends(get_db)):
    """Obtener todos los espacios"""
    try:
        spaces = db.query(Espacio).all()
        return [
            EspacioResponse(
                id=space.id_espacio,
                nombre=space.nombre,
                tipo=space.tipo,
                capacidad=space.capacidad,
                activo=space.activo,
                fecha_creacion=space.fecha_creacion
            )
            for space in spaces
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/spaces/{space_id}", response_model=EspacioResponse)
async def get_space(space_id: int, db: Session = Depends(get_db)):
    """Obtener espacio por ID"""
    try:
        space = db.query(Espacio).filter(Espacio.id_espacio == space_id).first()
        if not space:
            raise HTTPException(status_code=404, detail="Espacio no encontrado")
        
        return EspacioResponse(
            id=space.id_espacio,
            nombre=space.nombre,
            tipo=space.tipo,
            capacidad=space.capacidad,
            activo=space.activo,
            fecha_creacion=space.fecha_creacion
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/spaces/type/{tipo}")
async def get_spaces_by_type(tipo: str, db: Session = Depends(get_db)):
    """Obtener espacios por tipo (sala o cancha)"""
    try:
        if tipo not in ['sala', 'cancha']:
            raise HTTPException(status_code=400, detail="Tipo debe ser 'sala' o 'cancha'")
        
        spaces = db.query(Espacio).filter(
            Espacio.tipo == tipo,
            Espacio.activo == True
        ).all()
        
        return [
            EspacioResponse(
                id=space.id_espacio,
                nombre=space.nombre,
                tipo=space.tipo,
                capacidad=space.capacidad,
                activo=space.activo,
                fecha_creacion=space.fecha_creacion
            )
            for space in spaces
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/spaces/{space_id}", response_model=EspacioResponse)
async def update_space(space_id: int, space_data: EspacioUpdate, db: Session = Depends(get_db)):
    """Actualizar espacio"""
    try:
        space = db.query(Espacio).filter(Espacio.id_espacio == space_id).first()
        if not space:
            raise HTTPException(status_code=404, detail="Espacio no encontrado")
        
        # Guardar datos anteriores para auditoría
        datos_anteriores = {
            "nombre": space.nombre,
            "tipo": space.tipo,
            "capacidad": space.capacidad,
            "activo": space.activo
        }
        
        # Actualizar campos
        if space_data.nombre is not None:
            space.nombre = space_data.nombre
        if space_data.tipo is not None:
            if space_data.tipo not in ['sala', 'cancha']:
                raise HTTPException(status_code=400, detail="Tipo debe ser 'sala' o 'cancha'")
            space.tipo = space_data.tipo
        if space_data.capacidad is not None:
            space.capacidad = space_data.capacidad
        if space_data.activo is not None:
            space.activo = space_data.activo
        
        db.commit()
        db.refresh(space)
        
        # Registrar en auditoría
        datos_nuevos = {
            "nombre": space.nombre,
            "tipo": space.tipo,
            "capacidad": space.capacidad,
            "activo": space.activo
        }
        log_audit(db, "espacios", "actualizar", space_id, datos_anteriores, datos_nuevos, 1)
        
        return EspacioResponse(
            id=space.id_espacio,
            nombre=space.nombre,
            tipo=space.tipo,
            capacidad=space.capacidad,
            activo=space.activo,
            fecha_creacion=space.fecha_creacion
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/spaces/{space_id}")
async def deactivate_space(space_id: int, db: Session = Depends(get_db)):
    """Desactivar espacio (soft delete)"""
    try:
        space = db.query(Espacio).filter(Espacio.id_espacio == space_id).first()
        if not space:
            raise HTTPException(status_code=404, detail="Espacio no encontrado")
        
        # Guardar datos anteriores para auditoría
        datos_anteriores = {"activo": space.activo}
        
        # Desactivar espacio
        space.activo = False
        db.commit()
        
        # Registrar en auditoría
        datos_nuevos = {"activo": False}
        log_audit(db, "espacios", "desactivar", space_id, datos_anteriores, datos_nuevos, 1)
        
        return {"deactivated": True}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint para el protocolo SOA
@app.post("/soa/message")
async def handle_soa_message(message: str):
    """Manejar mensajes del protocolo SOA"""
    try:
        protocol = SOAProtocol()
        service_code, data = protocol.parse_message(message)
        
        if service_code.strip() == "space":
            db = next(get_db())
            
            if "create" in data:
                # Crear espacio
                space_data = EspacioCreate(**data["create"])
                result = await create_space(space_data, db)
                response_data = {
                    "id": result.id,
                    "status": "created"
                }
            
            elif "getall" in data:
                # Obtener todos los espacios
                spaces = await get_all_spaces(db)
                response_data = [
                    {
                        "id": space.id,
                        "nombre": space.nombre,
                        "tipo": space.tipo
                    }
                    for space in spaces
                ]
            
            else:
                response_data = {"error": "Comando no reconocido"}
        
        else:
            response_data = {"error": "Servicio no reconocido"}
        
        # Formatear respuesta según protocolo SOA
        return protocol.format_message("space", response_data)
        
    except Exception as e:
        return SOAProtocol().format_message("space", {"error": str(e)})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5003)

