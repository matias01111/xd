"""
Servicio de Administración (ADMIN) - Sistema de Reservación UDP
Puerto: 5007
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
import uvicorn

from database.db_config import get_db, init_db
from database.models import Configuracion, Auditoria
from services.common.soa_protocol import SOAProtocol

app = FastAPI(title="Servicio de Administración - ADMIN")

# Inicializar base de datos
init_db()

# Modelos Pydantic
class ConfigUpdate(BaseModel):
    ventana_anticipacion_dias: Optional[int] = None
    max_reservas_usuario: Optional[int] = None
    duracion_max_horas: Optional[int] = None
    hora_inicio: Optional[str] = None
    hora_fin: Optional[str] = None

class ConfigResponse(BaseModel):
    ventana_anticipacion_dias: int
    max_reservas_usuario: int
    duracion_max_horas: int
    hora_inicio: str
    hora_fin: str

class AuditoriaResponse(BaseModel):
    id: int
    tabla_afectada: str
    accion: str
    id_registro: Optional[int]
    fecha_accion: datetime
    usuario_id: Optional[int]

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

@app.get("/admin/config", response_model=ConfigResponse)
async def get_config(db: Session = Depends(get_db)):
    """Obtener configuración actual"""
    try:
        config = db.query(Configuracion).first()
        if not config:
            # Crear configuración por defecto
            config = Configuracion()
            db.add(config)
            db.commit()
            db.refresh(config)
        
        return ConfigResponse(
            ventana_anticipacion_dias=config.ventana_anticipacion_dias,
            max_reservas_usuario=config.max_reservas_usuario,
            duracion_max_horas=config.duracion_max_horas,
            hora_inicio=str(config.hora_inicio),
            hora_fin=str(config.hora_fin)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/admin/config")
async def update_config(config_data: ConfigUpdate, db: Session = Depends(get_db)):
    """Actualizar configuración"""
    try:
        config = db.query(Configuracion).first()
        if not config:
            config = Configuracion()
            db.add(config)
        
        # Guardar datos anteriores para auditoría
        datos_anteriores = {
            "ventana_anticipacion_dias": config.ventana_anticipacion_dias,
            "max_reservas_usuario": config.max_reservas_usuario,
            "duracion_max_horas": config.duracion_max_horas,
            "hora_inicio": str(config.hora_inicio),
            "hora_fin": str(config.hora_fin)
        }
        
        # Actualizar configuración
        if config_data.ventana_anticipacion_dias is not None:
            config.ventana_anticipacion_dias = config_data.ventana_anticipacion_dias
        if config_data.max_reservas_usuario is not None:
            config.max_reservas_usuario = config_data.max_reservas_usuario
        if config_data.duracion_max_horas is not None:
            config.duracion_max_horas = config_data.duracion_max_horas
        if config_data.hora_inicio is not None:
            config.hora_inicio = config_data.hora_inicio
        if config_data.hora_fin is not None:
            config.hora_fin = config_data.hora_fin
        
        config.fecha_actualizacion = datetime.now()
        db.commit()
        
        # Registrar en auditoría
        datos_nuevos = {
            "ventana_anticipacion_dias": config.ventana_anticipacion_dias,
            "max_reservas_usuario": config.max_reservas_usuario,
            "duracion_max_horas": config.duracion_max_horas,
            "hora_inicio": str(config.hora_inicio),
            "hora_fin": str(config.hora_fin)
        }
        log_audit(db, "configuraciones", "actualizar", config.id_config, datos_anteriores, datos_nuevos, 1)
        
        return {"configurado": True}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/audit", response_model=List[AuditoriaResponse])
async def get_audit_log(fecha: Optional[str] = None, db: Session = Depends(get_db)):
    """Obtener log de auditoría"""
    try:
        query = db.query(Auditoria)
        
        if fecha:
            fecha_parseada = datetime.strptime(fecha, "%Y-%m-%d").date()
            query = query.filter(Auditoria.fecha_accion >= fecha_parseada)
        
        audit_logs = query.order_by(Auditoria.fecha_accion.desc()).limit(100).all()
        
        return [
            AuditoriaResponse(
                id=log.id_auditoria,
                tabla_afectada=log.tabla_afectada,
                accion=log.accion,
                id_registro=log.id_registro,
                fecha_accion=log.fecha_accion,
                usuario_id=log.id_usuario
            )
            for log in audit_logs
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint para el protocolo SOA
@app.post("/soa/message")
async def handle_soa_message(message: str):
    """Manejar mensajes del protocolo SOA"""
    try:
        protocol = SOAProtocol()
        service_code, data = protocol.parse_message(message)
        
        if service_code.strip() == "admin":
            db = next(get_db())
            
            if "config" in data:
                # Configurar parámetros
                config_data = ConfigUpdate(**data["config"])
                result = await update_config(config_data, db)
                response_data = {"configurado": result["configurado"]}
            
            elif "getconfig" in data:
                # Consultar parámetros
                result = await get_config(db)
                response_data = {
                    "ventana_anticipacion": result.ventana_anticipacion_dias,
                    "max_reservas": result.max_reservas_usuario,
                    "duracion_max": result.duracion_max_horas
                }
            
            elif "getaudit" in data and "fecha" in data["getaudit"]:
                # Consultar auditoría
                results = await get_audit_log(data["getaudit"]["fecha"], db)
                response_data = [
                    {
                        "accion": log.accion,
                        "usuario": str(log.usuario_id),
                        "fecha": log.fecha_accion.isoformat()
                    }
                    for log in results
                ]
            
            else:
                response_data = {"error": "Comando no reconocido"}
        
        else:
            response_data = {"error": "Servicio no reconocido"}
        
        # Formatear respuesta según protocolo SOA
        return protocol.format_message("admin", response_data)
        
    except Exception as e:
        return SOAProtocol().format_message("admin", {"error": str(e)})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5007)




