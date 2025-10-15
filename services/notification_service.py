"""
Servicio de Notificaciones (NOTIF) - Sistema de Reservación UDP
Puerto: 5008
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uvicorn
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from database.db_config import get_db, init_db
from database.models import Notificacion, Reserva, Usuario
from services.common.soa_protocol import SOAProtocol

app = FastAPI(title="Servicio de Notificaciones - NOTIF")

# Inicializar base de datos
init_db()

# Modelos Pydantic
class NotificationSend(BaseModel):
    tipo: str
    reserva_id: int
    usuario_id: int

class TemplateConfig(BaseModel):
    tipo: str
    texto: str

def send_email(to_email: str, subject: str, body: str) -> bool:
    """Enviar email (simulado para este ejemplo)"""
    try:
        # En un sistema real, aquí configurarías SMTP
        print(f"Enviando email a {to_email}")
        print(f"Asunto: {subject}")
        print(f"Contenido: {body}")
        return True
    except Exception as e:
        print(f"Error enviando email: {e}")
        return False

@app.post("/notifications/send")
async def send_notification(request: NotificationSend, db: Session = Depends(get_db)):
    """Enviar notificación"""
    try:
        # Obtener datos de la reserva y usuario
        reserva = db.query(Reserva).filter(Reserva.id_reserva == request.reserva_id).first()
        if not reserva:
            raise HTTPException(status_code=404, detail="Reserva no encontrada")
        
        usuario = db.query(Usuario).filter(Usuario.id_usuario == request.usuario_id).first()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Generar contenido según tipo
        if request.tipo == "aprobacion":
            asunto = "Reserva Aprobada"
            contenido = f"Hola {usuario.nombre},\n\nSu reserva para {reserva.espacio.nombre} ha sido aprobada.\n\nDetalles:\n- Fecha: {reserva.fecha_inicio}\n- Hora: {reserva.fecha_inicio.strftime('%H:%M')} - {reserva.fecha_fin.strftime('%H:%M')}\n\n¡Que disfrute su reserva!"
        
        elif request.tipo == "rechazo":
            asunto = "Reserva Rechazada"
            contenido = f"Hola {usuario.nombre},\n\nSu reserva para {reserva.espacio.nombre} ha sido rechazada.\n\nDetalles:\n- Fecha: {reserva.fecha_inicio}\n- Motivo: {reserva.motivo or 'No especificado'}\n\nPor favor, intente con otro horario."
        
        elif request.tipo == "cancelacion":
            asunto = "Reserva Cancelada"
            contenido = f"Hola {usuario.nombre},\n\nSu reserva para {reserva.espacio.nombre} ha sido cancelada.\n\nDetalles:\n- Fecha: {reserva.fecha_inicio}\n- Hora: {reserva.fecha_inicio.strftime('%H:%M')} - {reserva.fecha_fin.strftime('%H:%M')}\n\nSi necesita una nueva reserva, puede crear una nueva solicitud."
        
        else:
            raise HTTPException(status_code=400, detail="Tipo de notificación no válido")
        
        # Crear notificación en BD
        notif = Notificacion(
            tipo_notificacion=request.tipo,
            destinatario_email=usuario.correo_institucional,
            asunto=asunto,
            contenido=contenido,
            id_reserva=request.reserva_id
        )
        
        db.add(notif)
        db.commit()
        db.refresh(notif)
        
        # Enviar email
        email_sent = send_email(usuario.correo_institucional, asunto, contenido)
        
        # Actualizar estado de envío
        notif.enviada = email_sent
        notif.fecha_envio = datetime.now() if email_sent else None
        db.commit()
        
        return {"enviado": email_sent, "email": usuario.correo_institucional}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/notifications/template")
async def configure_template(template_data: TemplateConfig, db: Session = Depends(get_db)):
    """Configurar plantilla de notificación"""
    try:
        # En un sistema real, aquí guardarías las plantillas en BD
        # Para este ejemplo, simplemente confirmamos la configuración
        return {"configurado": True}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/notifications/pending")
async def get_pending_notifications(db: Session = Depends(get_db)):
    """Obtener notificaciones pendientes"""
    try:
        pending = db.query(Notificacion).filter(Notificacion.enviada == False).all()
        return [
            {
                "id": notif.id_notificacion,
                "tipo": notif.tipo_notificacion,
                "destinatario": notif.destinatario_email,
                "asunto": notif.asunto,
                "fecha_creacion": notif.fecha_creacion
            }
            for notif in pending
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
        
        if service_code.strip() == "notif":
            db = next(get_db())
            
            if "send" in data and "tipo" in data["send"]:
                # Enviar notificación
                request = NotificationSend(
                    tipo=data["send"]["tipo"],
                    reserva_id=int(data["send"]["reserva"]),
                    usuario_id=int(data["send"]["usuario"])
                )
                result = await send_notification(request, db)
                response_data = {"enviado": result["enviado"], "email": result["email"]}
            
            elif "plantilla" in data and "tipo" in data["plantilla"]:
                # Configurar plantilla
                template_data = TemplateConfig(
                    tipo=data["plantilla"]["tipo"],
                    texto=data["plantilla"]["texto"]
                )
                result = await configure_template(template_data, db)
                response_data = {"configurado": result["configurado"]}
            
            else:
                response_data = {"error": "Comando no reconocido"}
        
        else:
            response_data = {"error": "Servicio no reconocido"}
        
        # Formatear respuesta según protocolo SOA
        return protocol.format_message("notif", response_data)
        
    except Exception as e:
        return SOAProtocol().format_message("notif", {"error": str(e)})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5008)




