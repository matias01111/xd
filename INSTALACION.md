# Instalación y Configuración - Sistema de Reservación UDP

## Requisitos del Sistema

### Software Necesario
- **Python 3.8+** con pip
- **Node.js 16+** con npm
- **PostgreSQL 12+**
- **Git** (opcional, para clonar el repositorio)

### Sistema Operativo
- Windows 10/11
- macOS 10.14+
- Linux Ubuntu 18.04+

## Instalación Paso a Paso

### 1. Configurar Base de Datos PostgreSQL

#### Instalar PostgreSQL
```bash
# Windows (usando Chocolatey)
choco install postgresql

# macOS (usando Homebrew)
brew install postgresql

# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib
```

#### Configurar PostgreSQL
```bash
# Iniciar servicio PostgreSQL
# Windows
net start postgresql-x64-13

# macOS
brew services start postgresql

# Linux
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Crear usuario y configurar contraseña
sudo -u postgres psql
CREATE USER postgres WITH PASSWORD 'password';
ALTER USER postgres CREATEDB;
\q
```

### 2. Configurar el Proyecto

#### Clonar o descargar el proyecto
```bash
# Si tienes Git
git clone <url-del-repositorio>
cd reservas-udp

# O descargar y extraer el ZIP
```

#### Instalar dependencias de Python
```bash
# Crear entorno virtual (recomendado)
python -m venv venv

# Activar entorno virtual
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

#### Configurar variables de entorno
```bash
# Copiar archivo de configuración
cp config.env .env

# Editar configuración según tu setup
# DATABASE_URL=postgresql://postgres:password@localhost:5432/reservas_udp
# SECRET_KEY=tu_clave_secreta_muy_segura_aqui
```

### 3. Configurar Base de Datos

```bash
# Ejecutar script de configuración
python setup_database.py
```

Este script:
- Crea la base de datos `reservas_udp`
- Crea todas las tablas necesarias
- Inserta datos de prueba
- Configura índices y relaciones

### 4. Iniciar Servicios

#### Opción A: Iniciar todos los servicios backend
```bash
python start_services.py
```

#### Opción B: Iniciar servicios individualmente
```bash
# Terminal 1 - Bus de Servicios
python services/service_bus.py

# Terminal 2 - Servicio de Autenticación
python services/auth_service.py

# Terminal 3 - Servicio de Usuarios
python services/user_service.py

# ... y así sucesivamente para cada servicio
```

### 5. Iniciar Clientes Web

#### Opción A: Iniciar ambos clientes
```bash
python start_clients.py
```

#### Opción B: Iniciar clientes individualmente
```bash
# Terminal 1 - Cliente Estudiantes
cd clients/student_client
npm install
npm start

# Terminal 2 - Cliente Administradores
cd clients/admin_client
npm install
npm start
```

## Verificación de la Instalación

### 1. Verificar Servicios Backend
Abrir en el navegador:
- Bus de Servicios: http://localhost:5000
- Autenticación: http://localhost:5001/docs
- Usuarios: http://localhost:5002/docs
- Espacios: http://localhost:5003/docs
- Disponibilidad: http://localhost:5004/docs
- Reservas: http://localhost:5005/docs
- Incidencias: http://localhost:5006/docs
- Administración: http://localhost:5007/docs
- Notificaciones: http://localhost:5008/docs
- Reportes: http://localhost:5009/docs

### 2. Verificar Clientes Web
- Cliente Estudiantes: http://localhost:3000
- Cliente Administradores: http://localhost:3001

### 3. Probar Funcionalidad
1. **Como Estudiante:**
   - Ir a http://localhost:3000
   - Iniciar sesión con: RUT `12345678-9`
   - Crear una reserva
   - Consultar disponibilidad

2. **Como Administrador:**
   - Ir a http://localhost:3001
   - Iniciar sesión con: RUT `12345678-9`
   - Aprobar/rechazar reservas
   - Gestionar usuarios
   - Ver reportes

## Credenciales de Prueba

| Rol | RUT | Email | Contraseña |
|-----|-----|-------|------------|
| Administrador | 12345678-9 | admin@udp.cl | (cualquiera) |
| Estudiante | 87654321-0 | estudiante@udp.cl | (cualquiera) |

## Estructura del Proyecto

```
reservas-udp/
├── database/                 # Configuración de base de datos
│   ├── init.sql             # Script de inicialización
│   ├── db_config.py         # Configuración SQLAlchemy
│   └── models.py            # Modelos de datos
├── services/                # Servicios backend SOA
│   ├── service_bus.py       # Bus de servicios (puerto 5000)
│   ├── auth_service.py      # Autenticación (puerto 5001)
│   ├── user_service.py      # Usuarios (puerto 5002)
│   ├── space_service.py     # Espacios (puerto 5003)
│   ├── availability_service.py # Disponibilidad (puerto 5004)
│   ├── booking_service.py   # Reservas (puerto 5005)
│   ├── incident_service.py  # Incidencias (puerto 5006)
│   ├── admin_service.py     # Administración (puerto 5007)
│   ├── notification_service.py # Notificaciones (puerto 5008)
│   ├── report_service.py    # Reportes (puerto 5009)
│   └── common/              # Utilidades comunes
│       ├── auth_utils.py    # Utilidades de autenticación
│       └── soa_protocol.py  # Protocolo de comunicación SOA
├── clients/                 # Clientes web
│   ├── student_client/      # Cliente para estudiantes
│   └── admin_client/        # Cliente para administradores
├── start_services.py        # Script para iniciar servicios
├── start_clients.py         # Script para iniciar clientes
├── setup_database.py        # Script de configuración de BD
├── requirements.txt         # Dependencias Python
└── README.md               # Documentación principal
```

## Solución de Problemas

### Error de Conexión a Base de Datos
```bash
# Verificar que PostgreSQL esté ejecutándose
sudo systemctl status postgresql

# Verificar configuración en .env
DATABASE_URL=postgresql://postgres:password@localhost:5432/reservas_udp
```

### Error de Puerto en Uso
```bash
# Verificar puertos ocupados
netstat -tulpn | grep :5000

# Cambiar puerto en el archivo de configuración o detener proceso
```

### Error de Dependencias Node.js
```bash
# Limpiar cache y reinstalar
cd clients/student_client
rm -rf node_modules package-lock.json
npm install
```

### Error de Permisos
```bash
# Dar permisos de ejecución a scripts
chmod +x start_services.py
chmod +x start_clients.py
chmod +x setup_database.py
```

## Comandos Útiles

### Reiniciar Base de Datos
```bash
# Detener y eliminar base de datos
sudo -u postgres psql -c "DROP DATABASE IF EXISTS reservas_udp;"
python setup_database.py
```

### Ver Logs de Servicios
```bash
# Los servicios muestran logs en la consola
# Para servicios individuales, revisar la terminal donde se ejecutan
```

### Backup de Base de Datos
```bash
# Crear backup
pg_dump -h localhost -U postgres reservas_udp > backup.sql

# Restaurar backup
psql -h localhost -U postgres reservas_udp < backup.sql
```

## Soporte

Si encuentras problemas durante la instalación:

1. Verifica que todos los requisitos estén instalados
2. Revisa los logs de error en la consola
3. Asegúrate de que los puertos no estén ocupados
4. Verifica la configuración de PostgreSQL
5. Revisa las variables de entorno en `.env`

Para más información, consulta el archivo `README.md` principal.
