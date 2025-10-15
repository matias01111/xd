"""
Modelos de base de datos para el Sistema de Reservación UDP
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Time, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .db_config import Base

class Usuario(Base):
    __tablename__ = "usuarios"
    
    id_usuario = Column(Integer, primary_key=True, index=True)
    rut = Column(String(12), unique=True, nullable=False, index=True)
    correo_institucional = Column(String(100), unique=True, nullable=False, index=True)
    nombre = Column(String(100), nullable=False)
    tipo_usuario = Column(String(20), nullable=False)  # estudiante, funcionario, administrador
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    reservas = relationship("Reserva", back_populates="usuario")
    incidencias_reportadas = relationship("Incidencia", foreign_keys="Incidencia.id_usuario_reporta", back_populates="usuario_reporta")
    incidencias_resueltas = relationship("Incidencia", foreign_keys="Incidencia.id_usuario_resuelve", back_populates="usuario_resuelve")
    auditorias = relationship("Auditoria", back_populates="usuario")

class Espacio(Base):
    __tablename__ = "espacios"
    
    id_espacio = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    tipo = Column(String(10), nullable=False)  # sala, cancha
    capacidad = Column(Integer, nullable=False)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    reservas = relationship("Reserva", back_populates="espacio")
    incidencias = relationship("Incidencia", back_populates="espacio")

class Reserva(Base):
    __tablename__ = "reservas"
    
    id_reserva = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    id_espacio = Column(Integer, ForeignKey("espacios.id_espacio"), nullable=False)
    fecha_inicio = Column(DateTime(timezone=True), nullable=False)
    fecha_fin = Column(DateTime(timezone=True), nullable=False)
    estado = Column(String(20), default="pendiente")  # pendiente, aprobada, rechazada, cancelada, bloqueo
    motivo = Column(Text)
    fecha_solicitud = Column(DateTime(timezone=True), server_default=func.now())
    recurrente = Column(Boolean, default=False)
    patron_recurrencia = Column(String(50))
    tipo_reserva = Column(String(20), default="normal")  # normal, bloqueo, incidencia
    descripcion_incidencia = Column(Text)
    id_administrador_aprobador = Column(Integer, ForeignKey("usuarios.id_usuario"))
    fecha_aprobacion = Column(DateTime(timezone=True))
    
    # Relaciones
    usuario = relationship("Usuario", foreign_keys=[id_usuario], back_populates="reservas")
    espacio = relationship("Espacio", back_populates="reservas")
    administrador_aprobador = relationship("Usuario", foreign_keys=[id_administrador_aprobador])
    notificaciones = relationship("Notificacion", back_populates="reserva")

class Configuracion(Base):
    __tablename__ = "configuraciones"
    
    id_config = Column(Integer, primary_key=True, index=True)
    ventana_anticipacion_dias = Column(Integer, default=7)
    max_reservas_usuario = Column(Integer, default=1)
    duracion_max_horas = Column(Integer, default=4)
    hora_inicio = Column(Time, default='08:00')
    hora_fin = Column(Time, default='22:00')
    fecha_actualizacion = Column(DateTime(timezone=True), server_default=func.now())

class Incidencia(Base):
    __tablename__ = "incidencias"
    
    id_incidencia = Column(Integer, primary_key=True, index=True)
    id_espacio = Column(Integer, ForeignKey("espacios.id_espacio"), nullable=False)
    tipo_incidencia = Column(String(50), nullable=False)
    descripcion = Column(Text, nullable=False)
    estado = Column(String(20), default="abierta")  # abierta, en_progreso, resuelta, cerrada
    fecha_reporte = Column(DateTime(timezone=True), server_default=func.now())
    fecha_resolucion = Column(DateTime(timezone=True))
    id_usuario_reporta = Column(Integer, ForeignKey("usuarios.id_usuario"))
    id_usuario_resuelve = Column(Integer, ForeignKey("usuarios.id_usuario"))
    solucion = Column(Text)
    
    # Relaciones
    espacio = relationship("Espacio", back_populates="incidencias")
    usuario_reporta = relationship("Usuario", foreign_keys=[id_usuario_reporta], back_populates="incidencias_reportadas")
    usuario_resuelve = relationship("Usuario", foreign_keys=[id_usuario_resuelve], back_populates="incidencias_resueltas")

class Auditoria(Base):
    __tablename__ = "auditoria"
    
    id_auditoria = Column(Integer, primary_key=True, index=True)
    tabla_afectada = Column(String(50), nullable=False)
    accion = Column(String(20), nullable=False)
    id_registro = Column(Integer)
    datos_anteriores = Column(JSON)
    datos_nuevos = Column(JSON)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"))
    fecha_accion = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="auditorias")

class Notificacion(Base):
    __tablename__ = "notificaciones"
    
    id_notificacion = Column(Integer, primary_key=True, index=True)
    tipo_notificacion = Column(String(50), nullable=False)
    destinatario_email = Column(String(100), nullable=False)
    asunto = Column(String(200), nullable=False)
    contenido = Column(Text, nullable=False)
    enviada = Column(Boolean, default=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_envio = Column(DateTime(timezone=True))
    id_reserva = Column(Integer, ForeignKey("reservas.id_reserva"))
    datos_adicionales = Column(JSON)
    
    # Relaciones
    reserva = relationship("Reserva", back_populates="notificaciones")

