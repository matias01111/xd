"""
Servicio de Reportes (REPRT) - Sistema de Reservación UDP
Puerto: 5009
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date
import uvicorn

from database.db_config import get_db, init_db
from database.models import Reserva, Espacio, Usuario, Auditoria, Incidencia
from services.common.soa_protocol import SOAProtocol

app = FastAPI(title="Servicio de Reportes - REPRT")

# Inicializar base de datos
init_db()

# Modelos Pydantic
class ReporteUsoRequest(BaseModel):
    fecha_inicio: str  # YYYY-MM-DD
    fecha_fin: str     # YYYY-MM-DD

class ReporteAuditoriaRequest(BaseModel):
    fecha: str  # YYYY-MM-DD

class ReporteUsoResponse(BaseModel):
    ocupacion_porcentaje: float
    total_reservas: int
    espacios_mas_usados: List[dict]
    reservas_por_estado: dict

class ReporteAuditoriaResponse(BaseModel):
    acciones_por_dia: List[dict]
    acciones_por_tipo: dict

@app.post("/reports/uso", response_model=ReporteUsoResponse)
async def generate_usage_report(request: ReporteUsoRequest, db: Session = Depends(get_db)):
    """Generar reporte de uso"""
    try:
        fecha_inicio = datetime.strptime(request.fecha_inicio, "%Y-%m-%d").date()
        fecha_fin = datetime.strptime(request.fecha_fin, "%Y-%m-%d").date()
        
        # Total de reservas en el período
        total_reservas = db.query(Reserva).filter(
            and_(
                Reserva.fecha_inicio >= fecha_inicio,
                Reserva.fecha_inicio <= fecha_fin,
                Reserva.estado.in_(['aprobada', 'pendiente'])
            )
        ).count()
        
        # Reservas por estado
        reservas_por_estado = {}
        for estado in ['aprobada', 'pendiente', 'rechazada', 'cancelada']:
            count = db.query(Reserva).filter(
                and_(
                    Reserva.fecha_inicio >= fecha_inicio,
                    Reserva.fecha_inicio <= fecha_fin,
                    Reserva.estado == estado
                )
            ).count()
            reservas_por_estado[estado] = count
        
        # Espacios más usados
        espacios_usados = db.query(
            Espacio.nombre,
            func.count(Reserva.id_reserva).label('uso_count')
        ).join(Reserva).filter(
            and_(
                Reserva.fecha_inicio >= fecha_inicio,
                Reserva.fecha_inicio <= fecha_fin,
                Reserva.estado == 'aprobada'
            )
        ).group_by(Espacio.nombre).order_by(func.count(Reserva.id_reserva).desc()).limit(5).all()
        
        espacios_mas_usados = [
            {"nombre": espacio.nombre, "uso": espacio.uso_count}
            for espacio in espacios_usados
        ]
        
        # Calcular ocupación (simplificado)
        # En un sistema real, esto sería más complejo considerando horarios y capacidad
        total_espacios = db.query(Espacio).filter(Espacio.activo == True).count()
        if total_espacios > 0:
            ocupacion_porcentaje = min((total_reservas / (total_espacios * 10)) * 100, 100)  # Simplificado
        else:
            ocupacion_porcentaje = 0
        
        return ReporteUsoResponse(
            ocupacion_porcentaje=round(ocupacion_porcentaje, 2),
            total_reservas=total_reservas,
            espacios_mas_usados=espacios_mas_usados,
            reservas_por_estado=reservas_por_estado
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reports/audit", response_model=ReporteAuditoriaResponse)
async def generate_audit_report(request: ReporteAuditoriaRequest, db: Session = Depends(get_db)):
    """Generar reporte de auditoría"""
    try:
        fecha_reporte = datetime.strptime(request.fecha, "%Y-%m-%d").date()
        
        # Acciones por día
        acciones_por_dia = db.query(
            func.date(Auditoria.fecha_accion).label('fecha'),
            func.count(Auditoria.id_auditoria).label('cantidad')
        ).filter(
            func.date(Auditoria.fecha_accion) == fecha_reporte
        ).group_by(func.date(Auditoria.fecha_accion)).all()
        
        acciones_por_dia_list = [
            {"fecha": str(accion.fecha), "cantidad": accion.cantidad}
            for accion in acciones_por_dia
        ]
        
        # Acciones por tipo
        acciones_por_tipo = {}
        tipos_accion = ['crear', 'actualizar', 'eliminar', 'aprobar', 'cancelar', 'configurar']
        
        for tipo in tipos_accion:
            count = db.query(Auditoria).filter(
                and_(
                    func.date(Auditoria.fecha_accion) == fecha_reporte,
                    Auditoria.accion == tipo
                )
            ).count()
            acciones_por_tipo[tipo] = count
        
        return ReporteAuditoriaResponse(
            acciones_por_dia=acciones_por_dia_list,
            acciones_por_tipo=acciones_por_tipo
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports/incidencias")
async def get_incident_report(db: Session = Depends(get_db)):
    """Obtener reporte de incidencias"""
    try:
        # Incidencias por estado
        incidencias_por_estado = {}
        for estado in ['abierta', 'en_progreso', 'resuelta', 'cerrada']:
            count = db.query(Incidencia).filter(Incidencia.estado == estado).count()
            incidencias_por_estado[estado] = count
        
        # Incidencias por tipo
        tipos_incidencia = db.query(
            Incidencia.tipo_incidencia,
            func.count(Incidencia.id_incidencia).label('cantidad')
        ).group_by(Incidencia.tipo_incidencia).all()
        
        incidencias_por_tipo = {
            tipo.tipo_incidencia: tipo.cantidad
            for tipo in tipos_incidencia
        }
        
        return {
            "incidencias_por_estado": incidencias_por_estado,
            "incidencias_por_tipo": incidencias_por_tipo,
            "total_incidencias": sum(incidencias_por_estado.values())
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
        
        if service_code.strip() == "report":
            db = next(get_db())
            
            if "uso" in data and "fecha_inicio" in data["uso"] and "fecha_fin" in data["uso"]:
                # Generar reporte de uso
                request = ReporteUsoRequest(
                    fecha_inicio=data["uso"]["fecha_inicio"],
                    fecha_fin=data["uso"]["fecha_fin"]
                )
                result = await generate_usage_report(request, db)
                response_data = {
                    "ocupacion": result.ocupacion_porcentaje,
                    "total_reservas": result.total_reservas,
                    "espacios_mas_usados": result.espacios_mas_usados
                }
            
            elif "audit" in data and "fecha" in data["audit"]:
                # Generar reporte de auditoría
                request = ReporteAuditoriaRequest(fecha=data["audit"]["fecha"])
                result = await generate_audit_report(request, db)
                response_data = [
                    {
                        "accion": accion["fecha"],
                        "usuario": "Sistema",
                        "fecha": accion["fecha"]
                    }
                    for accion in result.acciones_por_dia
                ]
            
            else:
                response_data = {"error": "Comando no reconocido"}
        
        else:
            response_data = {"error": "Servicio no reconocido"}
        
        # Formatear respuesta según protocolo SOA
        return protocol.format_message("report", response_data)
        
    except Exception as e:
        return SOAProtocol().format_message("report", {"error": str(e)})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5009)




