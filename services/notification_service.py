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
    """Enviar notificación - Evita duplicados"""
    try:
        # Verificar si ya existe una notificación enviada para esta reserva y tipo
        existing = db.query(Notificacion).filter(
            Notificacion.id_reserva == request.reserva_id,
            Notificacion.tipo_notificacion == request.tipo,
            Notificacion.enviada == True
        ).first()
        
        if existing:
            print(f"Notificación duplicada evitada: {request.tipo} para reserva {request.reserva_id}")
            return {"enviado": True, "email": existing.destinatario_email, "duplicado": True}
        
        # Obtener datos de la reserva y usuario
        reserva = db.query(Reserva).filter(Reserva.id_reserva == request.reserva_id).first()
        if not reserva:
            raise HTTPException(status_code=404, detail="Reserva no encontrada")
        
        usuario = db.query(Usuario).filter(Usuario.id_usuario == request.usuario_id).first()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Formatear fechas
        fecha_str = reserva.fecha_inicio.strftime('%d/%m/%Y')
        hora_inicio = reserva.fecha_inicio.strftime('%H:%M')
        hora_fin = reserva.fecha_fin.strftime('%H:%M')
        
        # Generar contenido según tipo
        if request.tipo == "creacion":
            asunto = "✅ Reserva Creada - Pendiente de Aprobación"
            contenido = f"""Estimado/a {usuario.nombre},

Su solicitud de reserva ha sido recibida y está pendiente de aprobación por un administrador.

📋 DETALLES DE LA RESERVA:
━━━━━━━━━━━━━━━━━━━━━━━━━━
🏢 Espacio: {reserva.espacio.nombre}
📅 Fecha: {fecha_str}
⏰ Horario: {hora_inicio} - {hora_fin}
🆔 ID Reserva: #{reserva.id_reserva}

Recibirá una notificación cuando su reserva sea aprobada o rechazada.

Saludos cordiales,
Sistema de Reservas UDP
"""
        
        elif request.tipo == "aprobacion":
            asunto = "✅ Reserva APROBADA"
            contenido = f"""Estimado/a {usuario.nombre},

¡Buenas noticias! Su reserva ha sido APROBADA.

📋 DETALLES DE LA RESERVA:
━━━━━━━━━━━━━━━━━━━━━━━━━━
🏢 Espacio: {reserva.espacio.nombre}
📅 Fecha: {fecha_str}
⏰ Horario: {hora_inicio} - {hora_fin}
🆔 ID Reserva: #{reserva.id_reserva}
✅ Estado: APROBADA

Por favor, llegue puntualmente y respete el horario asignado.

¡Que disfrute su reserva!

Saludos cordiales,
Sistema de Reservas UDP
"""
        
        elif request.tipo == "rechazo":
            asunto = "❌ Reserva RECHAZADA"
            contenido = f"""Estimado/a {usuario.nombre},

Lamentamos informarle que su reserva ha sido RECHAZADA.

📋 DETALLES DE LA RESERVA:
━━━━━━━━━━━━━━━━━━━━━━━━━━
🏢 Espacio: {reserva.espacio.nombre}
📅 Fecha: {fecha_str}
⏰ Horario: {hora_inicio} - {hora_fin}
🆔 ID Reserva: #{reserva.id_reserva}
❌ Estado: RECHAZADA
📝 Motivo: {reserva.motivo_rechazo or 'No especificado'}

Puede intentar reservar otro horario o espacio que se ajuste mejor a su necesidad.

Saludos cordiales,
Sistema de Reservas UDP
"""
        
        elif request.tipo == "cancelacion":
            asunto = "⚠️ Reserva CANCELADA"
            contenido = f"""Estimado/a {usuario.nombre},

Su reserva ha sido CANCELADA.

📋 DETALLES DE LA RESERVA:
━━━━━━━━━━━━━━━━━━━━━━━━━━
🏢 Espacio: {reserva.espacio.nombre}
📅 Fecha: {fecha_str}
⏰ Horario: {hora_inicio} - {hora_fin}
🆔 ID Reserva: #{reserva.id_reserva}
⚠️ Estado: CANCELADA

Si necesita realizar una nueva reserva, puede hacerlo a través del sistema.

Saludos cordiales,
Sistema de Reservas UDP
"""
        
        elif request.tipo == "bloqueo":
            asunto = "🚫 Reserva Cancelada por Bloqueo de Espacio"
            contenido = f"""Estimado/a {usuario.nombre},

Le informamos que su reserva ha sido CANCELADA debido a un bloqueo del espacio por incidencia.

📋 DETALLES DE LA RESERVA:
━━━━━━━━━━━━━━━━━━━━━━━━━━
🏢 Espacio: {reserva.espacio.nombre}
📅 Fecha: {fecha_str}
⏰ Horario: {hora_inicio} - {hora_fin}
🆔 ID Reserva: #{reserva.id_reserva}
🚫 Motivo: Bloqueo por incidencia en el espacio

Disculpe las molestias. Por favor, reserve otro espacio o espere a que se resuelva la incidencia.

Saludos cordiales,
Sistema de Reservas UDP
"""
        
        else:
            raise HTTPException(status_code=400, detail="Tipo de notificación no válido")
        
        # Crear notificación en BD
        notif = Notificacion(
            tipo_notificacion=request.tipo,
            destinatario_email=usuario.correo_institucional,
            asunto=asunto,
            contenido=contenido,
            id_reserva=request.reserva_id,
            datos_adicionales={
                "espacio": reserva.espacio.nombre,
                "fecha": fecha_str,
                "hora_inicio": hora_inicio,
                "hora_fin": hora_fin
            }
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
        
        return {"enviado": email_sent, "email": usuario.correo_institucional, "duplicado": False}
        
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

@app.get("/notifications/history")
async def get_notifications_history(
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    tipo: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Obtener historial de notificaciones con filtros"""
    try:
        query = db.query(Notificacion)
        
        # Aplicar filtros
        if fecha_inicio:
            fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
            query = query.filter(Notificacion.fecha_creacion >= fecha_inicio_dt)
        
        if fecha_fin:
            fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d")
            query = query.filter(Notificacion.fecha_creacion <= fecha_fin_dt)
        
        if tipo:
            query = query.filter(Notificacion.tipo_notificacion == tipo)
        
        notifications = query.order_by(Notificacion.fecha_creacion.desc()).limit(100).all()
        
        return [
            {
                "id": notif.id_notificacion,
                "tipo": notif.tipo_notificacion,
                "destinatario": notif.destinatario_email,
                "asunto": notif.asunto,
                "enviada": notif.enviada,
                "fecha_creacion": notif.fecha_creacion,
                "fecha_envio": notif.fecha_envio,
                "reserva_id": notif.id_reserva
            }
            for notif in notifications
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/notifications/templates")
async def get_templates():
    """Obtener plantillas disponibles"""
    templates = {
        "creacion": {
            "nombre": "Reserva Creada",
            "descripcion": "Notificación enviada cuando se crea una reserva",
            "variables": ["nombre", "espacio", "fecha", "hora_inicio", "hora_fin", "id_reserva"]
        },
        "aprobacion": {
            "nombre": "Reserva Aprobada",
            "descripcion": "Notificación enviada cuando se aprueba una reserva",
            "variables": ["nombre", "espacio", "fecha", "hora_inicio", "hora_fin", "id_reserva"]
        },
        "rechazo": {
            "nombre": "Reserva Rechazada",
            "descripcion": "Notificación enviada cuando se rechaza una reserva",
            "variables": ["nombre", "espacio", "fecha", "hora_inicio", "hora_fin", "id_reserva", "motivo"]
        },
        "cancelacion": {
            "nombre": "Reserva Cancelada",
            "descripcion": "Notificación enviada cuando se cancela una reserva",
            "variables": ["nombre", "espacio", "fecha", "hora_inicio", "hora_fin", "id_reserva"]
        },
        "bloqueo": {
            "nombre": "Cancelación por Bloqueo",
            "descripcion": "Notificación enviada cuando una reserva se cancela por bloqueo de espacio",
            "variables": ["nombre", "espacio", "fecha", "hora_inicio", "hora_fin", "id_reserva"]
        }
    }
    return templates

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




