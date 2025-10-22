"""
Servicio de Disponibilidad (AVAIL) - Sistema de Reservación UDP
Puerto: 5004
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
from database.models import Reserva, Espacio, Configuracion
from services.common.soa_protocol import SOAProtocol

app = FastAPI(title="Servicio de Disponibilidad - AVAIL")

# Inicializar base de datos
init_db()

# Modelos Pydantic
class DisponibilidadRequest(BaseModel):
    id_espacio: int
    fecha_inicio: str  # ISO format
    fecha_fin: str     # ISO format

class DisponibilidadResponse(BaseModel):
    disponible: bool
    id_espacio: int
    espacio_nombre: str
    fecha_inicio: datetime
    fecha_fin: datetime
    conflictos: List[dict] = []

class HorariosDisponiblesRequest(BaseModel):
    id_espacio: int
    fecha: str  # ISO format (solo fecha)
    duracion_horas: int = 2

class SlotDisponible(BaseModel):
    hora_inicio: str
    hora_fin: str
    disponible: bool

class EspaciosDisponiblesRequest(BaseModel):
    tipo: Optional[str] = None  # sala o cancha
    fecha_inicio: str
    fecha_fin: str

class EspacioDisponible(BaseModel):
    id: int
    nombre: str
    tipo: str
    capacidad: int
    disponible: bool

def get_configuracion(db: Session) -> Configuracion:
    """Obtener configuración actual del sistema"""
    config = db.query(Configuracion).first()
    if not config:
        config = Configuracion()
        db.add(config)
        db.commit()
        db.refresh(config)
    return config

@app.post("/availability/check", response_model=DisponibilidadResponse)
async def check_availability(request: DisponibilidadRequest, db: Session = Depends(get_db)):
    """Verificar disponibilidad de un espacio en un rango de fechas"""
    try:
        # Parsear fechas
        fecha_inicio = datetime.fromisoformat(request.fecha_inicio.replace('Z', '+00:00'))
        fecha_fin = datetime.fromisoformat(request.fecha_fin.replace('Z', '+00:00'))
        
        # Verificar que el espacio existe
        espacio = db.query(Espacio).filter(Espacio.id_espacio == request.id_espacio).first()
        if not espacio:
            raise HTTPException(status_code=404, detail="Espacio no encontrado")
        
        if not espacio.activo:
            return DisponibilidadResponse(
                disponible=False,
                id_espacio=request.id_espacio,
                espacio_nombre=espacio.nombre,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                conflictos=[{"motivo": "Espacio no activo"}]
            )
        
        # Buscar reservas que se solapen
        reservas_conflicto = db.query(Reserva).filter(
            and_(
                Reserva.id_espacio == request.id_espacio,
                Reserva.estado.in_(['aprobada', 'pendiente']),
                or_(
                    and_(Reserva.fecha_inicio <= fecha_inicio, Reserva.fecha_fin > fecha_inicio),
                    and_(Reserva.fecha_inicio < fecha_fin, Reserva.fecha_fin >= fecha_fin),
                    and_(Reserva.fecha_inicio >= fecha_inicio, Reserva.fecha_fin <= fecha_fin)
                )
            )
        ).all()
        
        conflictos = []
        if reservas_conflicto:
            for reserva in reservas_conflicto:
                conflictos.append({
                    "id_reserva": reserva.id_reserva,
                    "fecha_inicio": reserva.fecha_inicio.isoformat(),
                    "fecha_fin": reserva.fecha_fin.isoformat(),
                    "estado": reserva.estado
                })
        
        disponible = len(conflictos) == 0
        
        return DisponibilidadResponse(
            disponible=disponible,
            id_espacio=request.id_espacio,
            espacio_nombre=espacio.nombre,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            conflictos=conflictos
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/availability/slots", response_model=List[SlotDisponible])
async def get_available_slots(request: HorariosDisponiblesRequest, db: Session = Depends(get_db)):
    """Obtener slots horarios disponibles para un espacio en una fecha específica"""
    try:
        # Parsear fecha
        fecha = datetime.fromisoformat(request.fecha).date()
        
        # Verificar que el espacio existe
        espacio = db.query(Espacio).filter(Espacio.id_espacio == request.id_espacio).first()
        if not espacio:
            raise HTTPException(status_code=404, detail="Espacio no encontrado")
        
        # Obtener configuración
        config = get_configuracion(db)
        
        # Generar slots horarios
        hora_actual = datetime.combine(fecha, config.hora_inicio)
        hora_cierre = datetime.combine(fecha, config.hora_fin)
        
        slots = []
        while hora_actual + timedelta(hours=request.duracion_horas) <= hora_cierre:
            slot_fin = hora_actual + timedelta(hours=request.duracion_horas)
            
            # Verificar si el slot está disponible
            reservas_conflicto = db.query(Reserva).filter(
                and_(
                    Reserva.id_espacio == request.id_espacio,
                    Reserva.estado.in_(['aprobada', 'pendiente']),
                    or_(
                        and_(Reserva.fecha_inicio <= hora_actual, Reserva.fecha_fin > hora_actual),
                        and_(Reserva.fecha_inicio < slot_fin, Reserva.fecha_fin >= slot_fin),
                        and_(Reserva.fecha_inicio >= hora_actual, Reserva.fecha_fin <= slot_fin)
                    )
                )
            ).first()
            
            disponible = reservas_conflicto is None
            
            slots.append(SlotDisponible(
                hora_inicio=hora_actual.time().strftime('%H:%M'),
                hora_fin=slot_fin.time().strftime('%H:%M'),
                disponible=disponible
            ))
            
            # Avanzar 1 hora para el siguiente slot
            hora_actual += timedelta(hours=1)
        
        return slots
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/availability/spaces", response_model=List[EspacioDisponible])
async def get_available_spaces(request: EspaciosDisponiblesRequest, db: Session = Depends(get_db)):
    """Obtener espacios disponibles en un rango de fechas"""
    try:
        # Parsear fechas
        fecha_inicio = datetime.fromisoformat(request.fecha_inicio.replace('Z', '+00:00'))
        fecha_fin = datetime.fromisoformat(request.fecha_fin.replace('Z', '+00:00'))
        
        # Obtener espacios según filtro de tipo
        query = db.query(Espacio).filter(Espacio.activo == True)
        
        if request.tipo:
            if request.tipo not in ['sala', 'cancha']:
                raise HTTPException(status_code=400, detail="Tipo debe ser 'sala' o 'cancha'")
            query = query.filter(Espacio.tipo == request.tipo)
        
        espacios = query.all()
        
        resultado = []
        for espacio in espacios:
            # Verificar si el espacio tiene reservas en ese rango
            reservas_conflicto = db.query(Reserva).filter(
                and_(
                    Reserva.id_espacio == espacio.id_espacio,
                    Reserva.estado.in_(['aprobada', 'pendiente']),
                    or_(
                        and_(Reserva.fecha_inicio <= fecha_inicio, Reserva.fecha_fin > fecha_inicio),
                        and_(Reserva.fecha_inicio < fecha_fin, Reserva.fecha_fin >= fecha_fin),
                        and_(Reserva.fecha_inicio >= fecha_inicio, Reserva.fecha_fin <= fecha_fin)
                    )
                )
            ).first()
            
            disponible = reservas_conflicto is None
            
            resultado.append(EspacioDisponible(
                id=espacio.id_espacio,
                nombre=espacio.nombre,
                tipo=espacio.tipo,
                capacidad=espacio.capacidad,
                disponible=disponible
            ))
        
        return resultado
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/availability/space/{space_id}/calendar")
async def get_space_calendar(
    space_id: int,
    fecha_inicio: str,
    fecha_fin: str,
    db: Session = Depends(get_db)
):
    """Obtener calendario de reservas de un espacio"""
    try:
        # Verificar que el espacio existe
        espacio = db.query(Espacio).filter(Espacio.id_espacio == space_id).first()
        if not espacio:
            raise HTTPException(status_code=404, detail="Espacio no encontrado")
        
        # Parsear fechas
        fecha_inicio_dt = datetime.fromisoformat(fecha_inicio)
        fecha_fin_dt = datetime.fromisoformat(fecha_fin)
        
        # Obtener reservas del espacio en el rango
        reservas = db.query(Reserva).filter(
            and_(
                Reserva.id_espacio == space_id,
                Reserva.estado.in_(['aprobada', 'pendiente']),
                Reserva.fecha_inicio >= fecha_inicio_dt,
                Reserva.fecha_fin <= fecha_fin_dt
            )
        ).order_by(Reserva.fecha_inicio).all()
        
        calendario = []
        for reserva in reservas:
            calendario.append({
                "id_reserva": reserva.id_reserva,
                "fecha_inicio": reserva.fecha_inicio.isoformat(),
                "fecha_fin": reserva.fecha_fin.isoformat(),
                "estado": reserva.estado,
                "usuario": reserva.usuario.nombre if reserva.usuario else "Desconocido"
            })
        
        return {
            "espacio": {
                "id": espacio.id_espacio,
                "nombre": espacio.nombre,
                "tipo": espacio.tipo
            },
            "reservas": calendario
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/availability/config")
async def get_availability_config(db: Session = Depends(get_db)):
    """Obtener configuración de disponibilidad"""
    try:
        config = get_configuracion(db)
        
        return {
            "ventana_anticipacion_dias": config.ventana_anticipacion_dias,
            "max_reservas_usuario": config.max_reservas_usuario,
            "duracion_max_horas": config.duracion_max_horas,
            "hora_inicio": config.hora_inicio.strftime('%H:%M'),
            "hora_fin": config.hora_fin.strftime('%H:%M')
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint para el protocolo SOA
@app.post("/soa/message")
async def handle_soa_message(message: str):
    """Manejar mensajes del protocolo SOA"""
    try:
        protocol = SOAProtocol()
        service_code, data = protocol.parse_message(message)
        
        if service_code.strip() == "avail":
            db = next(get_db())
            
            if "check" in data:
                # Verificar disponibilidad
                check_data = data["check"]
                request = DisponibilidadRequest(
                    id_espacio=int(check_data["espacio"]),
                    fecha_inicio=check_data["inicio"],
                    fecha_fin=check_data["fin"]
                )
                result = await check_availability(request, db)
                response_data = {
                    "disponible": result.disponible,
                    "espacio": result.espacio_nombre,
                    "conflictos": len(result.conflictos)
                }
            
            elif "slots" in data:
                # Obtener slots disponibles
                slots_data = data["slots"]
                request = HorariosDisponiblesRequest(
                    id_espacio=int(slots_data["espacio"]),
                    fecha=slots_data["fecha"],
                    duracion_horas=slots_data.get("duracion", 2)
                )
                result = await get_available_slots(request, db)
                response_data = {
                    "slots": [
                        {
                            "inicio": slot.hora_inicio,
                            "fin": slot.hora_fin,
                            "disponible": slot.disponible
                        }
                        for slot in result
                    ]
                }
            
            elif "spaces" in data:
                # Obtener espacios disponibles
                spaces_data = data["spaces"]
                request = EspaciosDisponiblesRequest(
                    tipo=spaces_data.get("tipo"),
                    fecha_inicio=spaces_data["inicio"],
                    fecha_fin=spaces_data["fin"]
                )
                result = await get_available_spaces(request, db)
                response_data = {
                    "espacios": [
                        {
                            "id": esp.id,
                            "nombre": esp.nombre,
                            "disponible": esp.disponible
                        }
                        for esp in result
                    ]
                }
            
            elif "config" in data:
                # Obtener configuración
                result = await get_availability_config(db)
                response_data = result
            
            else:
                response_data = {"error": "Comando no reconocido"}
        
        else:
            response_data = {"error": "Servicio no reconocido"}
        
        # Formatear respuesta según protocolo SOA
        return protocol.format_message("avail", response_data)
        
    except Exception as e:
        return SOAProtocol().format_message("avail", {"error": str(e)})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5004)
