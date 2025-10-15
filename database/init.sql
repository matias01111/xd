-- Base de datos para Sistema de Reservación de Salas y Canchas - UDP
-- Creado basado en el informe de arquitectura

-- Crear base de datos
CREATE DATABASE reservas_udp;

-- Conectar a la base de datos
\c reservas_udp;

-- Tabla Usuarios
CREATE TABLE usuarios (
    id_usuario SERIAL PRIMARY KEY,
    rut VARCHAR(12) UNIQUE NOT NULL,
    correo_institucional VARCHAR(100) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    tipo_usuario VARCHAR(20) CHECK (tipo_usuario IN ('estudiante', 'funcionario', 'administrador')) NOT NULL,
    activo BOOLEAN DEFAULT true,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla Espacios
CREATE TABLE espacios (
    id_espacio SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    tipo VARCHAR(10) CHECK (tipo IN ('sala', 'cancha')) NOT NULL,
    capacidad INTEGER NOT NULL,
    activo BOOLEAN DEFAULT true,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla Reservas
CREATE TABLE reservas (
    id_reserva SERIAL PRIMARY KEY,
    id_usuario INTEGER REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    id_espacio INTEGER REFERENCES espacios(id_espacio) ON DELETE CASCADE,
    fecha_inicio TIMESTAMP NOT NULL,
    fecha_fin TIMESTAMP NOT NULL,
    estado VARCHAR(20) CHECK (estado IN ('pendiente', 'aprobada', 'rechazada', 'cancelada', 'bloqueo')) DEFAULT 'pendiente',
    motivo TEXT,
    fecha_solicitud TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    recurrente BOOLEAN DEFAULT false,
    patron_recurrencia VARCHAR(50),
    tipo_reserva VARCHAR(20) CHECK (tipo_reserva IN ('normal', 'bloqueo', 'incidencia')) DEFAULT 'normal',
    descripcion_incidencia TEXT,
    id_administrador_aprobador INTEGER REFERENCES usuarios(id_usuario),
    fecha_aprobacion TIMESTAMP
);

-- Tabla Configuraciones
CREATE TABLE configuraciones (
    id_config SERIAL PRIMARY KEY,
    ventana_anticipacion_dias INTEGER DEFAULT 7,
    max_reservas_usuario INTEGER DEFAULT 1,
    duracion_max_horas INTEGER DEFAULT 4,
    hora_inicio TIME DEFAULT '08:00',
    hora_fin TIME DEFAULT '22:00',
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla Incidencias
CREATE TABLE incidencias (
    id_incidencia SERIAL PRIMARY KEY,
    id_espacio INTEGER REFERENCES espacios(id_espacio) ON DELETE CASCADE,
    tipo_incidencia VARCHAR(50) NOT NULL,
    descripcion TEXT NOT NULL,
    estado VARCHAR(20) CHECK (estado IN ('abierta', 'en_progreso', 'resuelta', 'cerrada')) DEFAULT 'abierta',
    fecha_reporte TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_resolucion TIMESTAMP,
    id_usuario_reporta INTEGER REFERENCES usuarios(id_usuario),
    id_usuario_resuelve INTEGER REFERENCES usuarios(id_usuario),
    solucion TEXT
);

-- Tabla Auditoría
CREATE TABLE auditoria (
    id_auditoria SERIAL PRIMARY KEY,
    tabla_afectada VARCHAR(50) NOT NULL,
    accion VARCHAR(20) NOT NULL,
    id_registro INTEGER,
    datos_anteriores JSONB,
    datos_nuevos JSONB,
    id_usuario INTEGER REFERENCES usuarios(id_usuario),
    fecha_accion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla Notificaciones
CREATE TABLE notificaciones (
    id_notificacion SERIAL PRIMARY KEY,
    tipo_notificacion VARCHAR(50) NOT NULL,
    destinatario_email VARCHAR(100) NOT NULL,
    asunto VARCHAR(200) NOT NULL,
    contenido TEXT NOT NULL,
    enviada BOOLEAN DEFAULT false,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_envio TIMESTAMP,
    id_reserva INTEGER REFERENCES reservas(id_reserva),
    datos_adicionales JSONB
);

-- Insertar configuración inicial
INSERT INTO configuraciones (ventana_anticipacion_dias, max_reservas_usuario, duracion_max_horas, hora_inicio, hora_fin) 
VALUES (7, 1, 4, '08:00', '22:00');

-- Insertar usuario administrador inicial
INSERT INTO usuarios (rut, correo_institucional, nombre, tipo_usuario) 
VALUES ('12345678-9', 'admin@udp.cl', 'Administrador Sistema', 'administrador');

-- Insertar algunos espacios de ejemplo
INSERT INTO espacios (nombre, tipo, capacidad) VALUES 
('Sala A', 'sala', 30),
('Sala B', 'sala', 25),
('Cancha 1', 'cancha', 10),
('Cancha 2', 'cancha', 8);

-- Crear índices para optimizar consultas
CREATE INDEX idx_reservas_fecha_inicio ON reservas(fecha_inicio);
CREATE INDEX idx_reservas_fecha_fin ON reservas(fecha_fin);
CREATE INDEX idx_reservas_estado ON reservas(estado);
CREATE INDEX idx_reservas_id_usuario ON reservas(id_usuario);
CREATE INDEX idx_reservas_id_espacio ON reservas(id_espacio);
CREATE INDEX idx_usuarios_rut ON usuarios(rut);
CREATE INDEX idx_usuarios_correo ON usuarios(correo_institucional);
CREATE INDEX idx_espacios_tipo ON espacios(tipo);
CREATE INDEX idx_incidencias_estado ON incidencias(estado);
CREATE INDEX idx_auditoria_fecha ON auditoria(fecha_accion);

