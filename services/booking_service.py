"""
Servicio de Reservas (BOOK) - Sistema de Reservación UDP
Puerto: 5005
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
import uvicorn

from database.db_config import get_db, init_db
from database.models import Reserva, Usuario, Espacio, Configuracion, Auditoria, Notificacion
from services.common.soa_protocol import SOAProtocol
import requests

app = FastAPI(title="Servicio de Reservas - BOOK")

# URL del servicio de notificaciones
NOTIFICATION_SERVICE = "http://localhost:5008"

# Inicializar base de datos
init_db()

# Modelos Pydantic
class ReservaCreate(BaseModel):
    id_usuario: int
    id_espacio: int
    fecha_inicio: str  # ISO format
    fecha_fin: str     # ISO format
    motivo: Optional[str] = None
    recurrente: bool = False
    patron_recurrencia: Optional[str] = None

class ReservaResponse(BaseModel):
    id: int
    id_usuario: int
    id_espacio: int
    fecha_inicio: datetime
    fecha_fin: datetime
    estado: str
    motivo: Optional[str]
    fecha_solicitud: datetime
    recurrente: bool
    espacio_nombre: str
    usuario_nombre: str

class AprobarReservaRequest(BaseModel):
    id_reserva: int
    estado: str  # aprobada o rechazada
    id_administrador: int
    motivo: Optional[str] = None

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

def create_notification(db: Session, tipo: str, id_reserva: int, email_destinatario: str, asunto: str, contenido: str):
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

def send_notification_async(tipo: str, reserva_id: int, usuario_id: int):
    """Enviar notificación al servicio de notificaciones de forma asíncrona"""
    try:
        response = requests.post(
            f"{NOTIFICATION_SERVICE}/notifications/send",
            json={
                "tipo": tipo,
                "reserva_id": reserva_id,
                "usuario_id": usuario_id
            },
            timeout=5
        )
        if response.status_code == 200:
            print(f"Notificación '{tipo}' enviada para reserva #{reserva_id}")
        else:
            print(f"Error al enviar notificación: {response.status_code}")
    except Exception as e:
        print(f"Error al conectar con servicio de notificaciones: {e}")

def get_configuracion(db: Session) -> Configuracion:
    """Obtener configuración actual del sistema"""
    config = db.query(Configuracion).first()
    if not config:
        config = Configuracion()
        db.add(config)
        db.commit()
        db.refresh(config)
    return config

def validate_reserva_times(fecha_inicio: datetime, fecha_fin: datetime, config: Configuracion) -> tuple:
    """Validar horarios de reserva"""
    # Verificar duración máxima
    duracion_horas = (fecha_fin - fecha_inicio).total_seconds() / 3600
    if duracion_horas > config.duracion_max_horas:
        return False, f"La duración máxima permitida es {config.duracion_max_horas} horas"
    
    # Verificar horario operativo
    hora_inicio = fecha_inicio.time()
    hora_fin_reserva = fecha_fin.time()
    if hora_inicio < config.hora_inicio or hora_fin_reserva > config.hora_fin:
        return False, f"La reserva debe estar dentro del horario operativo ({config.hora_inicio} - {config.hora_fin})"
    
    # Verificar ventana de anticipación
    fecha_actual = datetime.now().date()
    fecha_reserva = fecha_inicio.date()
    dias_anticipacion = (fecha_reserva - fecha_actual).days
    if dias_anticipacion < config.ventana_anticipacion_dias:
        return False, f"La reserva debe hacerse con al menos {config.ventana_anticipacion_dias} días de anticipación"
    
    return True, "OK"

@app.post("/bookings/create", response_model=ReservaResponse)
async def create_booking(booking_data: ReservaCreate, db: Session = Depends(get_db)):
    """Crear nueva reserva"""
    try:
        # Parsear fechas
        fecha_inicio = datetime.fromisoformat(booking_data.fecha_inicio.replace('Z', '+00:00'))
        fecha_fin = datetime.fromisoformat(booking_data.fecha_fin.replace('Z', '+00:00'))
        
        # Verificar que el usuario y espacio existen
        usuario = db.query(Usuario).filter(Usuario.id_usuario == booking_data.id_usuario).first()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        espacio = db.query(Espacio).filter(Espacio.id_espacio == booking_data.id_espacio).first()
        if not espacio:
            raise HTTPException(status_code=404, detail="Espacio no encontrado")
        
        # Obtener configuración
        config = get_configuracion(db)
        
        # Validar horarios
        is_valid, error_msg = validate_reserva_times(fecha_inicio, fecha_fin, config)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Verificar límite de reservas por usuario
        reservas_activas = db.query(Reserva).filter(
            and_(
                Reserva.id_usuario == booking_data.id_usuario,
                Reserva.estado.in_(['pendiente', 'aprobada']),
                Reserva.fecha_fin >= datetime.now()
            )
        ).count()
        
        if reservas_activas >= config.max_reservas_usuario:
            raise HTTPException(
                status_code=400, 
                detail=f"Límite de reservas activas alcanzado ({config.max_reservas_usuario})"
            )
        
        # Verificar disponibilidad (no solape)
        reservas_conflicto = db.query(Reserva).filter(
            and_(
                Reserva.id_espacio == booking_data.id_espacio,
                Reserva.estado.in_(['aprobada', 'pendiente']),
                or_(
                    and_(Reserva.fecha_inicio <= fecha_inicio, Reserva.fecha_fin > fecha_inicio),
                    and_(Reserva.fecha_inicio < fecha_fin, Reserva.fecha_fin >= fecha_fin),
                    and_(Reserva.fecha_inicio >= fecha_inicio, Reserva.fecha_fin <= fecha_fin)
                )
            )
        ).first()
        
        if reservas_conflicto:
            raise HTTPException(status_code=400, detail="El espacio no está disponible en ese horario")
        
        # Crear reserva
        new_booking = Reserva(
            id_usuario=booking_data.id_usuario,
            id_espacio=booking_data.id_espacio,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            motivo=booking_data.motivo,
            recurrente=booking_data.recurrente,
            patron_recurrencia=booking_data.patron_recurrencia,
            estado='pendiente'
        )
        
        db.add(new_booking)
        db.commit()
        db.refresh(new_booking)
        
        # Registrar en auditoría
        log_audit(db, "reservas", "crear", new_booking.id_reserva, {}, {
            "id_usuario": booking_data.id_usuario,
            "id_espacio": booking_data.id_espacio,
            "fecha_inicio": booking_data.fecha_inicio,
            "fecha_fin": booking_data.fecha_fin,
            "estado": "pendiente"
        }, booking_data.id_usuario)
        
        # Enviar notificación de creación
        send_notification_async("creacion", new_booking.id_reserva, booking_data.id_usuario)
        
        return ReservaResponse(
            id=new_booking.id_reserva,
            id_usuario=new_booking.id_usuario,
            id_espacio=new_booking.id_espacio,
            fecha_inicio=new_booking.fecha_inicio,
            fecha_fin=new_booking.fecha_fin,
            estado=new_booking.estado,
            motivo=new_booking.motivo,
            fecha_solicitud=new_booking.fecha_solicitud,
            recurrente=new_booking.recurrente,
            espacio_nombre=espacio.nombre,
            usuario_nombre=usuario.nombre
        )
        
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        print(f"Error creating booking: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/bookings/user/{user_id}", response_model=List[ReservaResponse])
async def get_user_bookings(user_id: int, db: Session = Depends(get_db)):
    """Obtener reservas de un usuario"""
    try:
        print(f"Buscando reservas para usuario ID: {user_id}")
        reservas = db.query(Reserva).filter(
            Reserva.id_usuario == user_id
        ).order_by(Reserva.fecha_solicitud.desc()).all()
        
        print(f"Encontradas {len(reservas)} reservas")
        
        result = []
        for reserva in reservas:
            # Obtener espacio y usuario relacionados
            espacio = db.query(Espacio).filter(Espacio.id_espacio == reserva.id_espacio).first()
            usuario = db.query(Usuario).filter(Usuario.id_usuario == reserva.id_usuario).first()
            
            print(f"Reserva ID {reserva.id_reserva}: {espacio.nombre if espacio else 'N/A'} - Estado: {reserva.estado}")
            
            result.append(ReservaResponse(
                id=reserva.id_reserva,
                id_usuario=reserva.id_usuario,
                id_espacio=reserva.id_espacio,
                fecha_inicio=reserva.fecha_inicio,
                fecha_fin=reserva.fecha_fin,
                estado=reserva.estado,
                motivo=reserva.motivo,
                fecha_solicitud=reserva.fecha_solicitud,
                recurrente=reserva.recurrente,
                espacio_nombre=espacio.nombre if espacio else "Desconocido",
                usuario_nombre=usuario.nombre if usuario else "Desconocido"
            ))
        
        return result
    except Exception as e:
        print(f"Error obteniendo reservas: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/bookings", response_model=List[ReservaResponse])
async def get_all_bookings(estado: Optional[str] = None, db: Session = Depends(get_db)):
    """Obtener todas las reservas, opcionalmente filtradas por estado"""
    try:
        print(f"Obteniendo todas las reservas. Estado filtro: {estado}")
        
        query = db.query(Reserva)
        if estado:
            query = query.filter(Reserva.estado == estado)
        
        reservas = query.order_by(Reserva.fecha_solicitud.desc()).all()
        print(f"Encontradas {len(reservas)} reservas")
        
        result = []
        for reserva in reservas:
            # Obtener espacio y usuario relacionados
            espacio = db.query(Espacio).filter(Espacio.id_espacio == reserva.id_espacio).first()
            usuario = db.query(Usuario).filter(Usuario.id_usuario == reserva.id_usuario).first()
            
            result.append(ReservaResponse(
                id=reserva.id_reserva,
                id_usuario=reserva.id_usuario,
                id_espacio=reserva.id_espacio,
                fecha_inicio=reserva.fecha_inicio,
                fecha_fin=reserva.fecha_fin,
                estado=reserva.estado,
                motivo=reserva.motivo,
                fecha_solicitud=reserva.fecha_solicitud,
                recurrente=reserva.recurrente,
                espacio_nombre=espacio.nombre if espacio else "Desconocido",
                usuario_nombre=usuario.nombre if usuario else "Desconocido"
            ))
        
        return result
    except Exception as e:
        print(f"Error obteniendo todas las reservas: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/bookings/approve")
async def approve_booking(request: AprobarReservaRequest, db: Session = Depends(get_db)):
    """Aprobar o rechazar reserva"""
    try:
        reserva = db.query(Reserva).filter(Reserva.id_reserva == request.id_reserva).first()
        if not reserva:
            raise HTTPException(status_code=404, detail="Reserva no encontrada")
        
        if reserva.estado != 'pendiente':
            raise HTTPException(status_code=400, detail="La reserva no está pendiente")
        
        # Guardar datos anteriores para auditoría
        datos_anteriores = {"estado": reserva.estado}
        
        # Actualizar estado
        reserva.estado = request.estado
        reserva.id_administrador_aprobador = request.id_administrador
        reserva.fecha_aprobacion = datetime.now()
        if request.motivo:
            reserva.motivo = request.motivo
        
        db.commit()
        
        # Registrar en auditoría
        datos_nuevos = {"estado": request.estado}
        log_audit(db, "reservas", "aprobar", request.id_reserva, datos_anteriores, datos_nuevos, request.id_administrador)
        
        # Enviar notificación
        tipo_notif = "aprobacion" if request.estado == "aprobada" else "rechazo"
        send_notification_async(tipo_notif, reserva.id_reserva, reserva.id_usuario)
        
        return {"updated": True, "notificado": True}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/bookings/{booking_id}")
async def cancel_booking(booking_id: int, db: Session = Depends(get_db)):
    """Cancelar reserva"""
    try:
        reserva = db.query(Reserva).filter(Reserva.id_reserva == booking_id).first()
        if not reserva:
            raise HTTPException(status_code=404, detail="Reserva no encontrada")
        
        if reserva.estado in ['cancelada', 'rechazada']:
            raise HTTPException(status_code=400, detail="La reserva ya está cancelada o rechazada")
        
        # Guardar datos anteriores para auditoría
        datos_anteriores = {"estado": reserva.estado}
        
        # Cancelar reserva
        reserva.estado = 'cancelada'
        db.commit()
        
        # Registrar en auditoría
        datos_nuevos = {"estado": "cancelada"}
        log_audit(db, "reservas", "cancelar", booking_id, datos_anteriores, datos_nuevos, reserva.id_usuario)
        
        # Enviar notificación de cancelación
        send_notification_async("cancelacion", reserva.id_reserva, reserva.id_usuario)
        
        return {"cancelado": True}
        
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
        
        if service_code.strip() == "book":
            db = next(get_db())
            
            if "user" in data and "space" in data and "inicio" in data and "fin" in data:
                # Crear reserva
                booking_data = ReservaCreate(
                    id_usuario=int(data["user"]),
                    id_espacio=int(data["space"]),
                    fecha_inicio=data["inicio"],
                    fecha_fin=data["fin"]
                )
                result = await create_booking(booking_data, db)
                response_data = {
                    "id": result.id,
                    "estado": result.estado
                }
            
            elif "approve" in data and "reserva" in data["approve"] and "estado" in data["approve"]:
                # Aprobar/Rechazar reserva
                request = AprobarReservaRequest(
                    id_reserva=int(data["approve"]["reserva"]),
                    estado=data["approve"]["estado"],
                    id_administrador=1  # ID del administrador
                )
                result = await approve_booking(request, db)
                response_data = {"updated": result["updated"], "notificado": result["notificado"]}
            
            elif "getmyreservas" in data:
                # Obtener reservas del usuario
                user_id = int(data["getmyreservas"])
                results = await get_user_bookings(user_id, db)
                response_data = [
                    {
                        "id": result.id,
                        "espacio": result.espacio_nombre,
                        "estado": result.estado
                    }
                    for result in results
                ]
            
            elif "cancel" in data:
                # Cancelar reserva
                booking_id = int(data["cancel"])
                result = await cancel_booking(booking_id, db)
                response_data = {"cancelado": result["cancelado"]}
            
            else:
                response_data = {"error": "Comando no reconocido"}
        
        else:
            response_data = {"error": "Servicio no reconocido"}
        
        # Formatear respuesta según protocolo SOA
        return protocol.format_message("book", response_data)
        
    except Exception as e:
        return SOAProtocol().format_message("book", {"error": str(e)})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5005)




