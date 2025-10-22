# 🚀 Guía Rápida de Despliegue

Esta guía proporciona los pasos esenciales para poner en marcha el sistema rápidamente.

## ⚡ Inicio Rápido (5 minutos)

### 1. Prerequisitos
```bash
# Verificar instalaciones
python --version  # Debe ser 3.13+
node --version    # Debe ser 20.x+
psql --version    # Debe ser 14+
```

### 2. Clonar y Configurar
```bash
# Clonar repositorio
git clone https://github.com/Suxx12/ARQ-Software.git
cd ARQ-Software

# Instalar dependencias Python
pip install -r requirements.txt

# Instalar dependencias Node.js (ambos clientes)
cd clients/student_client && npm install && cd ../..
cd clients/admin_client && npm install && cd ../..
```

### 3. Configurar Base de Datos
```bash
# Editar config.env con tus credenciales de PostgreSQL
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=reservas_udp
# DB_USER=postgres
# DB_PASSWORD=tu_contraseña

# Inicializar base de datos
python setup_database.py
```

### 4. Iniciar Sistema
```bash
# Terminal 1: Servicios Backend
python start_services.py

# Terminal 2: Clientes Web (en nueva terminal)
python start_clients.py
```

### 5. Acceder
- **Cliente Estudiantes**: http://localhost:3000
- **Cliente Administradores**: http://localhost:3001

**Credenciales de prueba:**
- Usuario: `12345678-9` (estudiante)
- Usuario: `admin@udp.cl` (administrador)
- Contraseña: cualquiera (autenticación simplificada)

## 🐳 Docker (Próximamente)

```bash
# Construcción
docker-compose build

# Iniciar
docker-compose up -d

# Detener
docker-compose down
```

## ☁️ Despliegue en Producción

### Heroku

```bash
# Login
heroku login

# Crear app
heroku create arq-software-udp

# Añadir PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Deploy
git push heroku main
```

### Railway

1. Conecta tu repositorio de GitHub
2. Añade PostgreSQL addon
3. Configura variables de entorno
4. Deploy automático

### AWS EC2

```bash
# SSH a instancia
ssh -i key.pem ubuntu@ec2-instance

# Instalar dependencias
sudo apt update
sudo apt install python3 nodejs postgresql

# Clonar y configurar
git clone <repo>
cd ARQ-Software
pip3 install -r requirements.txt

# Configurar servicios como systemd
sudo systemctl start arq-services
```

## 🔧 Configuración Avanzada

### Variables de Entorno

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=reservas_udp
DB_USER=postgres
DB_PASSWORD=password

# JWT
SECRET_KEY=tu_clave_secreta_muy_larga_y_segura
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Email (opcional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_email@gmail.com
SMTP_PASSWORD=tu_password

# Servicios (puertos)
AUTH_PORT=5001
USER_PORT=5002
SPACE_PORT=5003
AVAIL_PORT=5004
BOOK_PORT=5005
INCID_PORT=5006
ADMIN_PORT=5007
NOTIF_PORT=5008
REPRT_PORT=5009

# Clientes (puertos)
STUDENT_CLIENT_PORT=3000
ADMIN_CLIENT_PORT=3001
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name tu-dominio.com;

    # Cliente Estudiantes
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Cliente Administradores
    location /admin {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # API Servicios
    location /api {
        proxy_pass http://localhost:5001;
    }
}
```

### PM2 para Node.js (Producción)

```bash
# Instalar PM2
npm install -g pm2

# Iniciar clientes
cd clients/student_client
pm2 start server.js --name student-client

cd ../admin_client
pm2 start server.js --name admin-client

# Ver status
pm2 status

# Ver logs
pm2 logs

# Reiniciar
pm2 restart all

# Auto-inicio en reboot
pm2 startup
pm2 save
```

### Supervisor para Python (Producción)

```ini
# /etc/supervisor/conf.d/arq-services.conf
[program:auth-service]
command=/path/to/venv/bin/python /path/to/services/auth_service.py
directory=/path/to/ARQ-Software
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/auth-service.err.log
stdout_logfile=/var/log/auth-service.out.log

# Repetir para cada servicio...
```

## 📊 Monitoreo

### Health Check Endpoints

```bash
# Verificar servicios
curl http://localhost:5001/health
curl http://localhost:5002/health
# ... para cada servicio
```

### Logs

```bash
# Ver logs en tiempo real
tail -f logs/auth_service.log
tail -f logs/booking_service.log
```

## 🔄 Actualización

```bash
# Detener servicios
pkill -f python
pkill -f node

# Actualizar código
git pull origin main

# Actualizar dependencias
pip install -r requirements.txt
cd clients/student_client && npm install
cd ../admin_client && npm install

# Migrar base de datos (si hay cambios)
python migrations/migrate.py

# Reiniciar servicios
python start_services.py
python start_clients.py
```

## 🛡️ Seguridad en Producción

- [ ] Cambiar SECRET_KEY a valor seguro
- [ ] Usar HTTPS (certificado SSL/TLS)
- [ ] Configurar firewall (solo puertos 80/443)
- [ ] Activar logs de auditoría
- [ ] Implementar rate limiting
- [ ] Configurar backups automáticos de BD
- [ ] Usar variables de entorno para credenciales
- [ ] Implementar autenticación real (no simplificada)

## 📞 Soporte

Para problemas de despliegue:
1. Revisar logs de servicios
2. Verificar variables de entorno
3. Comprobar conectividad a base de datos
4. Verificar puertos no estén ocupados

## ✅ Checklist Post-Despliegue

- [ ] Todos los servicios responden (9 servicios)
- [ ] Ambos clientes web accesibles
- [ ] Base de datos poblada con datos iniciales
- [ ] Login funciona correctamente
- [ ] Se pueden crear reservas
- [ ] Notificaciones se envían
- [ ] Reportes se generan correctamente
- [ ] Auditoría registra acciones
