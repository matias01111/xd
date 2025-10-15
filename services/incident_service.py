"""
Servicio de Incidencias (INCID) - Sistema de Reservación UDP
Puerto: 5006
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uvicorn

from database.db_config import get_db, init_db
from database.models import Incidencia, Espacio, Usuario, Reserva, Notificacion, Auditoria
from services.common.soa_protocol import SOAProtocol

app = FastAPI(title="Servicio de Incidencias - INCID")

# Inicializar base de datos
init_db()

# Modelos Pydantic
class IncidenciaCreate(BaseModel):
    id_espacio: int
    tipo_incidencia: str
    descripcion: str
    id_usuario_reporta: int

class IncidenciaResponse(BaseModel):
    id: int
    id_espacio: int
    tipo_incidencia: str
    descripcion: str
    estado: str
    fecha_reporte: datetime
    espacio_nombre: str
    usuario_reporta_nombre: str

class BloqueoRequest(BaseModel):
    id_incidencia: int
    fecha_inicio: str
    fecha_fin: str
    id_administrador: int

class ResolverIncidenciaRequest(BaseModel):
    id_incidencia: int
    solucion: str
    id_usuario_resuelve: int

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

def create_notification(db: Session, tipo: str, email_destinatario: str, asunto: str, contenido: str, id_reserva: int = None):
    """Crear notificación"""
    notif = Notificacion(
        tipo_notificacion=tipo,
        destinatario_email=email_destinatario,
        asunto=asunto,
        contenido=contenido,
        id_reserva=id_reserva
    )
    db.add(notif)
    db.commit()

@app.post("/incidents/report", response_model=IncidenciaResponse)
async def report_incident(incident_data: IncidenciaCreate, db: Session = Depends(get_db)):
    """Reportar incidencia"""
    try:
        # Verificar que el espacio y usuario existen
        espacio = db.query(Espacio).filter(Espacio.id_espacio == incident_data.id_espacio).first()
        if not espacio:
            raise HTTPException(status_code=404, detail="Espacio no encontrado")
        
        usuario = db.query(Usuario).filter(Usuario.id_usuario == incident_data.id_usuario_reporta).first()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Crear incidencia
        new_incident = Incidencia(
            id_espacio=incident_data.id_espacio,
            tipo_incidencia=incident_data.tipo_incidencia,
            descripcion=incident_data.descripcion,
            id_usuario_reporta=incident_data.id_usuario_reporta,
            estado='abierta'
        )
        
        db.add(new_incident)
        db.commit()
        db.refresh(new_incident)
        
        # Registrar en auditoría
        log_audit(db, "incidencias", "crear", new_incident.id_incidencia, {}, {
            "id_espacio": incident_data.id_espacio,
            "tipo_incidencia": incident_data.tipo_incidencia,
            "descripcion": incident_data.descripcion,
            "estado": "abierta"
        }, incident_data.id_usuario_reporta)
        
        return IncidenciaResponse(
            id=new_incident.id_incidencia,
            id_espacio=new_incident.id_espacio,
            tipo_incidencia=new_incident.tipo_incidencia,
            descripcion=new_incident.descripcion,
            estado=new_incident.estado,
            fecha_reporte=new_incident.fecha_reporte,
            espacio_nombre=espacio.nombre,
            usuario_reporta_nombre=usuario.nombre
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/incidents", response_model=List[IncidenciaResponse])
async def get_incidents(db: Session = Depends(get_db)):
    """Obtener todas las incidencias"""
    try:
        incidents = db.query(Incidencia).join(Espacio).join(Usuario).all()
        
        return [
            IncidenciaResponse(
                id=incident.id_incidencia,
                id_espacio=incident.id_espacio,
                tipo_incidencia=incident.tipo_incidencia,
                descripcion=incident.descripcion,
                estado=incident.estado,
                fecha_reporte=incident.fecha_reporte,
                espacio_nombre=incident.espacio.nombre,
                usuario_reporta_nombre=incident.usuario_reporta.nombre
            )
            for incident in incidents
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/incidents/block")
async def apply_block(request: BloqueoRequest, db: Session = Depends(get_db)):
    """Aplicar bloqueo por incidencia"""
    try:
        # Verificar que la incidencia existe
        incident = db.query(Incidencia).filter(Incidencia.id_incidencia == request.id_incidencia).first()
        if not incident:
            raise HTTPException(status_code=404, detail="Incidencia no encontrada")
        
        # Parsear fechas
        fecha_inicio = datetime.fromisoformat(request.fecha_inicio.replace('Z', '+00:00'))
        fecha_fin = datetime.fromisoformat(request.fecha_fin.replace('Z', '+00:00'))
        
        # Crear bloqueo como reserva especial
        bloqueo = Reserva(
            id_usuario=1,  # Usuario sistema
            id_espacio=incident.id_espacio,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            estado='bloqueo',
            tipo_reserva='bloqueo',
            motivo=f"Bloqueo por incidencia: {incident.descripcion}",
            descripcion_incidencia=incident.descripcion
        )
        
        db.add(bloqueo)
        db.commit()
        db.refresh(bloqueo)
        
        # Cancelar reservas afectadas
        reservas_afectadas = db.query(Reserva).filter(
            and_(
                Reserva.id_espacio == incident.id_espacio,
                Reserva.estado.in_(['pendiente', 'aprobada']),
                Reserva.tipo_reserva == 'normal',
                Reserva.fecha_inicio >= fecha_inicio,
                Reserva.fecha_fin <= fecha_fin
            )
        ).all()
        
        reservas_canceladas = 0
        for reserva in reservas_afectadas:
            reserva.estado = 'cancelada'
            reserva.motivo = f"Cancelada por bloqueo por incidencia ID: {request.id_incidencia}"
            
            # Notificar cancelación
            create_notification(
                db, "reserva_cancelada", 
                reserva.usuario.correo_institucional,
                "Reserva Cancelada por Incidencia",
                f"Su reserva para {reserva.espacio.nombre} ha sido cancelada debido a una incidencia reportada.",
                reserva.id_reserva
            )
            reservas_canceladas += 1
        
        db.commit()
        
        # Actualizar estado de la incidencia
        incident.estado = 'en_progreso'
        db.commit()
        
        return {"bloqueado": True, "reservas_canceladas": reservas_canceladas}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/incidents/resolve")
async def resolve_incident(request: ResolverIncidenciaRequest, db: Session = Depends(get_db)):
    """Resolver incidencia"""
    try:
        incident = db.query(Incidencia).filter(Incidencia.id_incidencia == request.id_incidencia).first()
        if not incident:
            raise HTTPException(status_code=404, detail="Incidencia no encontrada")
        
        # Guardar datos anteriores para auditoría
        datos_anteriores = {"estado": incident.estado}
        
        # Resolver incidencia
        incident.estado = 'resuelta'
        incident.solucion = request.solucion
        incident.id_usuario_resuelve = request.id_usuario_resuelve
        incident.fecha_resolucion = datetime.now()
        
        db.commit()
        
        # Registrar en auditoría
        datos_nuevos = {"estado": "resuelta", "solucion": request.solucion}
        log_audit(db, "incidencias", "resolver", request.id_incidencia, datos_anteriores, datos_nuevos, request.id_usuario_resuelve)
        
        # Verificar si hay bloqueos activos para este espacio
        bloqueos_activos = db.query(Reserva).filter(
            and_(
                Reserva.id_espacio == incident.id_espacio,
                Reserva.tipo_reserva == 'bloqueo',
                Reserva.estado == 'bloqueo',
                Reserva.fecha_fin > datetime.now()
            )
        ).all()
        
        espacio_liberado = len(bloqueos_activos) > 0
        
        # Remover bloqueos activos
        for bloqueo in bloqueos_activos:
            bloqueo.estado = 'cancelada'
        
        db.commit()
        
        return {"resuelta": True, "espacio_liberado": espacio_liberado}
        
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
        
        if service_code.strip() == "incid":
            db = next(get_db())
            
            if "report" in data and "space" in data["report"]:
                # Reportar incidencia
                incident_data = IncidenciaCreate(
                    id_espacio=int(data["report"]["space"]),
                    tipo_incidencia=data["report"]["tipo"],
                    descripcion=data["report"]["descripcion"],
                    id_usuario_reporta=1  # Usuario por defecto
                )
                result = await report_incident(incident_data, db)
                response_data = {
                    "id_incidencia": result.id,
                    "estado": result.estado
                }
            
            elif "block" in data and "incidencia" in data["block"]:
                # Aplicar bloqueo
                request = BloqueoRequest(
                    id_incidencia=int(data["block"]["incidencia"]),
                    fecha_inicio=data["block"]["inicio"],
                    fecha_fin=data["block"]["fin"],
                    id_administrador=1
                )
                result = await apply_block(request, db)
                response_data = {"bloqueado": result["bloqueado"], "reservas_canceladas": result["reservas_canceladas"]}
            
            elif "resolve" in data and "incidencia" in data["resolve"]:
                # Resolver incidencia
                request = ResolverIncidenciaRequest(
                    id_incidencia=int(data["resolve"]["incidencia"]),
                    solucion=data["resolve"]["solucion"],
                    id_usuario_resuelve=1
                )
                result = await resolve_incident(request, db)
                response_data = {"resuelta": result["resuelta"], "espacio_liberado": result["espacio_liberado"]}
            
            else:
                response_data = {"error": "Comando no reconocido"}
        
        else:
            response_data = {"error": "Servicio no reconocido"}
        
        # Formatear respuesta según protocolo SOA
        return protocol.format_message("incid", response_data)
        
    except Exception as e:
        return SOAProtocol().format_message("incid", {"error": str(e)})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5006)




