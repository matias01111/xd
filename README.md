# 🏢 Sistema de Reservación de Espacios - Universidad Diego Portales

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-20.x-green.svg)](https://nodejs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-blue.svg)](https://www.postgresql.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-teal.svg)](https://fastapi.tiangolo.com/)

Sistema integral para la gestión digital de reservas de salas y canchas deportivas implementado con **Arquitectura Orientada a Servicios (SOA)**. Este proyecto permite a estudiantes realizar reservas de espacios mientras los administradores gestionan disponibilidad, aprobaciones, incidencias y generan reportes del sistema.

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Arquitectura SOA](#-arquitectura-soa)
- [Tecnologías](#-tecnologías)
- [Requisitos](#-requisitos)
- [Instalación](#-instalación)
- [Uso](#-uso)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Documentación Técnica](#-documentación-técnica)
- [Autores](#-autores)

## ✨ Características

### Funcionalidades Principales

#### Para Estudiantes 👨‍🎓
- ✅ Autenticación mediante RUT y correo institucional
- 📅 Consulta de disponibilidad de espacios en tiempo real
- 🎯 Creación de reservas con motivo y horario
- 📊 Visualización de historial de reservas
- 🔔 Notificaciones por correo sobre estado de reservas

#### Para Administradores 👨‍💼
- 🔐 Panel de administración completo
- 👥 Gestión de usuarios (estudiantes y administradores)
- 🏢 Administración de espacios (salas, canchas, laboratorios)
- ✅ Aprobación/rechazo de reservas pendientes
- 🚨 Gestión de incidencias con bloqueo automático
- 📧 Sistema de notificaciones con plantillas personalizables
- 📊 Reportes de uso, auditoría e incidencias
- ⚙️ Configuración del sistema (horarios, anticipación, límites)

### Funcionalidades Técnicas

- 🔄 Arquitectura SOA con 9 microservicios independientes
- 🔒 Autenticación basada en tokens JWT
- 📝 Sistema completo de auditoría
- 🚫 Prevención de duplicados en notificaciones
- 📈 Generación de reportes con estadísticas
- 🔁 Reservas recurrentes (diarias/semanales)
- ⏰ Validaciones de horarios y anticipación
- 🚨 Bloqueo automático de espacios por incidencias

## 🏗️ Arquitectura SOA

El sistema utiliza una arquitectura de microservicios donde cada componente es independiente y se comunica mediante un protocolo SOA personalizado.

### Servicios Backend (FastAPI + Python)

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| **AUTH** | 5001 | Autenticación y gestión de tokens JWT |
| **USER** | 5002 | CRUD de usuarios y perfiles |
| **SPACE** | 5003 | Gestión de espacios físicos |
| **AVAIL** | 5004 | Consulta de disponibilidad en tiempo real |
| **BOOK** | 5005 | Creación y gestión de reservas |
| **INCID** | 5006 | Registro y seguimiento de incidencias |
| **ADMIN** | 5007 | Configuración del sistema y auditoría |
| **NOTIF** | 5008 | Envío de notificaciones por correo |
| **REPRT** | 5009 | Generación de reportes estadísticos |

### Clientes Web (Node.js + Express + EJS)

| Cliente | Puerto | Usuarios |
|---------|--------|----------|
| **Cliente Estudiantes** | 3000 | Estudiantes UDP |
| **Cliente Administradores** | 3001 | Personal administrativo |

### Base de Datos (PostgreSQL)

Esquema relacional con 9 tablas principales:
- `usuarios` - Estudiantes y administradores
- `espacios` - Salas, canchas, laboratorios
- `reservas` - Solicitudes de reserva
- `disponibilidad` - Horarios disponibles
- `incidencias` - Reportes de problemas
- `notificaciones` - Historial de envíos
- `configuraciones` - Parámetros del sistema
- `auditoria` - Registro de acciones
- `bloqueos` - Espacios temporalmente no disponibles

## 🛠️ Tecnologías

### Backend
- **FastAPI** 0.109+ - Framework web de alto rendimiento
- **SQLAlchemy** 2.0+ - ORM para Python
- **Pydantic** - Validación de datos
- **python-jose** - Manejo de JWT
- **psycopg2** - Driver PostgreSQL
- **uvicorn** - Servidor ASGI

### Frontend
- **Node.js** 20.x - Runtime JavaScript
- **Express.js** 4.x - Framework web
- **EJS** - Motor de plantillas
- **Bootstrap** 5.1 - Framework CSS
- **Font Awesome** 6.0 - Iconos
- **Axios** - Cliente HTTP

### Base de Datos
- **PostgreSQL** 14+ - Sistema de gestión de BD

## 📦 Requisitos

### Software Necesario
- Python 3.13+ ([Descargar](https://www.python.org/downloads/))
- PostgreSQL 14+ ([Descargar](https://www.postgresql.org/download/))
- Node.js 20.x+ ([Descargar](https://nodejs.org/))
- Git ([Descargar](https://git-scm.com/downloads))

### Dependencias Python
Ver `requirements.txt`

### Dependencias Node.js
Ver `package.json` en cada carpeta de cliente

## 🚀 Instalación

### 1. Clonar el Repositorio

```bash
git clone https://github.com/Suxx12/ARQ-Software.git
cd ARQ-Software
```

### 2. Configurar Base de Datos

Asegúrate de tener PostgreSQL instalado y ejecutándose.

```bash
# Crear la base de datos
createdb reservas_udp

# O usando psql
psql -U postgres
CREATE DATABASE reservas_udp;
\q
```

### 3. Configurar Variables de Entorno

Edita el archivo `config.env` con tus credenciales:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=reservas_udp
DB_USER=postgres
DB_PASSWORD=tu_contraseña
```

### 4. Instalar Dependencias Python

```bash
pip install -r requirements.txt
```

### 5. Inicializar Base de Datos

```bash
python setup_database.py
```

Este script:
- ✅ Crea todas las tablas
- ✅ Inserta datos de prueba
- ✅ Crea usuarios predeterminados
- ✅ Configura espacios de ejemplo

### 6. Instalar Dependencias de Clientes

```bash
# Cliente Estudiantes
cd clients/student_client
npm install

# Cliente Administradores
cd ../admin_client
npm install
```

## 🎮 Uso

### Iniciar Todos los Servicios

```bash
# Opción 1: Usando el script de Python (Recomendado)
python start_services.py

# Opción 2: Iniciar servicios individualmente
cd services
python auth_service.py
python user_service.py
# ... etc para cada servicio
```

### Iniciar Clientes Web

```bash
# Opción 1: Usando el script de Python (Recomendado)
python start_clients.py

# Opción 2: Iniciar clientes individualmente
cd clients/student_client
node server.js

cd ../admin_client
node server.js
```

### Acceder al Sistema

#### Cliente Estudiantes
- **URL**: http://localhost:3000
- **Usuario de prueba**: `12345678-9`
- **Contraseña**: `password123`

#### Cliente Administradores
- **URL**: http://localhost:3001
- **Usuario de prueba**: `admin@udp.cl`
- **Contraseña**: `admin123`

### Detener el Sistema

Presiona `Ctrl+C` en las terminales donde están corriendo los scripts, o ejecuta:

```bash
# Windows PowerShell
Get-Process python,node | Stop-Process -Force

# Linux/Mac
pkill -f python
pkill -f node
```

## 📁 Estructura del Proyecto

```
ARQ-Software/
├── clients/                    # Aplicaciones web cliente
│   ├── admin_client/          # Panel de administración
│   │   ├── views/             # Plantillas EJS
│   │   ├── server.js          # Servidor Express
│   │   └── package.json
│   └── student_client/        # Portal estudiantes
│       ├── views/
│       ├── server.js
│       └── package.json
├── database/                   # Configuración de BD
│   ├── db_config.py           # Conexión a PostgreSQL
│   ├── models.py              # Modelos SQLAlchemy
│   └── init.sql               # Script SQL inicial
├── services/                   # Microservicios SOA
│   ├── auth_service.py        # Autenticación
│   ├── user_service.py        # Usuarios
│   ├── space_service.py       # Espacios
│   ├── availability_service.py # Disponibilidad
│   ├── booking_service.py     # Reservas
│   ├── incident_service.py    # Incidencias
│   ├── admin_service.py       # Administración
│   ├── notification_service.py # Notificaciones
│   ├── report_service.py      # Reportes
│   └── common/
│       ├── soa_protocol.py    # Protocolo SOA
│       └── auth_utils.py      # Utilidades JWT
├── config.env                  # Variables de entorno
├── requirements.txt            # Dependencias Python
├── setup_database.py           # Inicialización BD
├── start_services.py           # Iniciar servicios
├── start_clients.py            # Iniciar clientes
├── INSTALACION.md             # Guía detallada
├── Informe.tex                # Informe académico
└── README.md                   # Este archivo
```

## 📚 Documentación Técnica

### Protocolo SOA

Los servicios se comunican mediante mensajes con el siguiente formato:

```
[LONGITUD:5][SERVICIO:5][DATOS:JSON]
```

**Ejemplo:**
```
00045auth {"action":"login","rut":"12345678-9"}
```

### Códigos de Servicio

| Código | Servicio | Descripción |
|--------|----------|-------------|
| `auth` | AUTH | Autenticación |
| `user` | USER | Usuarios |
| `space` | SPACE | Espacios |
| `avail` | AVAIL | Disponibilidad |
| `book` | BOOK | Reservas |
| `incid` | INCID | Incidencias |
| `admin` | ADMIN | Administración |
| `notif` | NOTIF | Notificaciones |
| `reprt` | REPRT | Reportes |

### Endpoints API

Cada servicio expone endpoints REST. Documentación completa disponible en:
- AUTH: http://localhost:5001/docs
- USER: http://localhost:5002/docs
- SPACE: http://localhost:5003/docs
- ... (y así para cada servicio)

### Base de Datos

Ver modelo entidad-relación completo en `database/init.sql`

**Relaciones principales:**
- Usuario → Reservas (1:N)
- Espacio → Reservas (1:N)
- Espacio → Incidencias (1:N)
- Reserva → Notificaciones (1:N)
- Usuario → Auditoría (1:N)

## 🧪 Testing

```bash
# Probar endpoint de autenticación
python -c "import requests; r = requests.post('http://localhost:5001/auth/login', json={'rut': '12345678-9', 'password': 'password123'}); print(r.json())"

# Probar notificaciones
python services/test_notifications.py

# Verificar servicios activos
netstat -ano | findstr "5001 5002 5003 5004 5005 5006 5007 5008 5009"
```

## 🤝 Autores

**Proyecto Universitario - Universidad Diego Portales**

- Curso: Arquitectura de Software
- Año: 2025
- Institución: Universidad Diego Portales

## 📄 Licencia

Este proyecto es un trabajo académico para la Universidad Diego Portales.

## 🙏 Agradecimientos

- Universidad Diego Portales
- Profesores del curso de Arquitectura de Software
- Comunidad de FastAPI y Node.js

---

**Nota**: Este es un proyecto académico con fines educativos. Las credenciales y datos son solo para demostración

