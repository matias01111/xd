"""
Servicio de Usuarios (USER) - Sistema de Reservación UDP
Puerto: 5002
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
from database.models import Usuario, Auditoria
from services.common.soa_protocol import SOAProtocol
from datetime import datetime

app = FastAPI(title="Servicio de Usuarios - USER")

# Inicializar base de datos
init_db()

# Modelos Pydantic
class UsuarioCreate(BaseModel):
    rut: str
    correo_institucional: str
    nombre: str
    tipo_usuario: str

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    tipo_usuario: Optional[str] = None
    activo: Optional[bool] = None

class UsuarioResponse(BaseModel):
    id: int
    rut: str
    correo_institucional: str
    nombre: str
    tipo_usuario: str
    activo: bool
    fecha_creacion: datetime

class ChangeRoleRequest(BaseModel):
    user_id: int
    new_role: str

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

@app.post("/users/create", response_model=UsuarioResponse)
async def create_user(user_data: UsuarioCreate, db: Session = Depends(get_db)):
    """Crear nuevo usuario"""
    try:
        # Verificar si ya existe un usuario con el mismo RUT o correo
        existing_user = db.query(Usuario).filter(
            (Usuario.rut == user_data.rut) | 
            (Usuario.correo_institucional == user_data.correo_institucional)
        ).first()
        
        if existing_user:
            raise HTTPException(status_code=400, detail="Usuario ya existe con ese RUT o correo")
        
        # Crear nuevo usuario
        new_user = Usuario(
            rut=user_data.rut,
            correo_institucional=user_data.correo_institucional,
            nombre=user_data.nombre,
            tipo_usuario=user_data.tipo_usuario
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Registrar en auditoría
        log_audit(db, "usuarios", "crear", new_user.id_usuario, {}, {
            "rut": user_data.rut,
            "correo": user_data.correo_institucional,
            "nombre": user_data.nombre,
            "tipo_usuario": user_data.tipo_usuario
        }, 1)  # ID del administrador que crea
        
        return UsuarioResponse(
            id=new_user.id_usuario,
            rut=new_user.rut,
            correo_institucional=new_user.correo_institucional,
            nombre=new_user.nombre,
            tipo_usuario=new_user.tipo_usuario,
            activo=new_user.activo,
            fecha_creacion=new_user.fecha_creacion
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users", response_model=List[UsuarioResponse])
async def get_all_users(db: Session = Depends(get_db)):
    """Obtener todos los usuarios"""
    try:
        users = db.query(Usuario).all()
        return [
            UsuarioResponse(
                id=user.id_usuario,
                rut=user.rut,
                correo_institucional=user.correo_institucional,
                nombre=user.nombre,
                tipo_usuario=user.tipo_usuario,
                activo=user.activo,
                fecha_creacion=user.fecha_creacion
            )
            for user in users
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}", response_model=UsuarioResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Obtener usuario por ID"""
    try:
        user = db.query(Usuario).filter(Usuario.id_usuario == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        return UsuarioResponse(
            id=user.id_usuario,
            rut=user.rut,
            correo_institucional=user.correo_institucional,
            nombre=user.nombre,
            tipo_usuario=user.tipo_usuario,
            activo=user.activo,
            fecha_creacion=user.fecha_creacion
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/users/{user_id}", response_model=UsuarioResponse)
async def update_user(user_id: int, user_data: UsuarioUpdate, db: Session = Depends(get_db)):
    """Actualizar usuario"""
    try:
        user = db.query(Usuario).filter(Usuario.id_usuario == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Guardar datos anteriores para auditoría
        datos_anteriores = {
            "nombre": user.nombre,
            "tipo_usuario": user.tipo_usuario,
            "activo": user.activo
        }
        
        # Actualizar campos
        if user_data.nombre is not None:
            user.nombre = user_data.nombre
        if user_data.tipo_usuario is not None:
            user.tipo_usuario = user_data.tipo_usuario
        if user_data.activo is not None:
            user.activo = user_data.activo
        
        db.commit()
        db.refresh(user)
        
        # Registrar en auditoría
        datos_nuevos = {
            "nombre": user.nombre,
            "tipo_usuario": user.tipo_usuario,
            "activo": user.activo
        }
        log_audit(db, "usuarios", "actualizar", user_id, datos_anteriores, datos_nuevos, 1)
        
        return UsuarioResponse(
            id=user.id_usuario,
            rut=user.rut,
            correo_institucional=user.correo_institucional,
            nombre=user.nombre,
            tipo_usuario=user.tipo_usuario,
            activo=user.activo,
            fecha_creacion=user.fecha_creacion
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/users/change-role")
async def change_user_role(request: ChangeRoleRequest, db: Session = Depends(get_db)):
    """Cambiar rol de usuario"""
    try:
        user = db.query(Usuario).filter(Usuario.id_usuario == request.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Guardar datos anteriores para auditoría
        datos_anteriores = {"tipo_usuario": user.tipo_usuario}
        
        # Actualizar rol
        user.tipo_usuario = request.new_role
        db.commit()
        
        # Registrar en auditoría
        datos_nuevos = {"tipo_usuario": request.new_role}
        log_audit(db, "usuarios", "cambiar_rol", request.user_id, datos_anteriores, datos_nuevos, 1)
        
        return {"updated": True, "new_role": request.new_role}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/users/{user_id}")
async def deactivate_user(user_id: int, db: Session = Depends(get_db)):
    """Desactivar usuario (soft delete)"""
    try:
        user = db.query(Usuario).filter(Usuario.id_usuario == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Guardar datos anteriores para auditoría
        datos_anteriores = {"activo": user.activo}
        
        # Desactivar usuario
        user.activo = False
        db.commit()
        
        # Registrar en auditoría
        datos_nuevos = {"activo": False}
        log_audit(db, "usuarios", "desactivar", user_id, datos_anteriores, datos_nuevos, 1)
        
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
        
        if service_code.strip() == "user":
            db = next(get_db())
            
            if "create" in data:
                # Crear usuario
                user_data = UsuarioCreate(**data["create"])
                result = await create_user(user_data, db)
                response_data = {
                    "id": result.id,
                    "status": "created"
                }
            
            elif "getall" in data:
                # Obtener todos los usuarios
                users = await get_all_users(db)
                response_data = [
                    {
                        "id": user.id,
                        "rut": user.rut,
                        "tipo": user.tipo_usuario
                    }
                    for user in users
                ]
            
            elif "changerole" in data:
                # Cambiar rol
                if "user" in data["changerole"] and "rol" in data["changerole"]:
                    request = ChangeRoleRequest(
                        user_id=int(data["changerole"]["user"]),
                        new_role=data["changerole"]["rol"]
                    )
                    result = await change_user_role(request, db)
                    response_data = {"updated": result["updated"]}
                else:
                    response_data = {"error": "Parámetros faltantes"}
            
            else:
                response_data = {"error": "Comando no reconocido"}
        
        else:
            response_data = {"error": "Servicio no reconocido"}
        
        # Formatear respuesta según protocolo SOA
        return protocol.format_message("user", response_data)
        
    except Exception as e:
        return SOAProtocol().format_message("user", {"error": str(e)})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5002)

