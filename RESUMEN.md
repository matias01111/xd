# 📊 Resumen Ejecutivo del Proyecto

## Sistema de Reservación de Espacios UDP

### 🎯 Objetivo del Proyecto

Desarrollar un sistema integral de gestión de reservas de espacios (salas y canchas deportivas) para la Universidad Diego Portales, implementando una arquitectura orientada a servicios (SOA) que permita escalabilidad, mantenibilidad y reutilización de componentes.

### 👥 Usuarios del Sistema

1. **Estudiantes**: Consultan disponibilidad y realizan reservas
2. **Administradores**: Gestionan espacios, aprueban reservas, manejan incidencias y generan reportes

### 🏗️ Arquitectura Técnica

#### Patrón Arquitectónico: SOA (Service-Oriented Architecture)

**9 Microservicios Independientes:**
- AUTH (5001): Autenticación y autorización
- USER (5002): Gestión de usuarios
- SPACE (5003): Administración de espacios
- AVAIL (5004): Consulta de disponibilidad
- BOOK (5005): Gestión de reservas
- INCID (5006): Manejo de incidencias
- ADMIN (5007): Configuración del sistema
- NOTIF (5008): Sistema de notificaciones
- REPRT (5009): Generación de reportes

**2 Clientes Web:**
- Cliente Estudiantes (3000): Portal para usuarios finales
- Cliente Administradores (3001): Panel de control administrativo

**Base de Datos Centralizada:**
- PostgreSQL con 9 tablas relacionales
- Modelo entidad-relación normalizado
- Sistema completo de auditoría

### 📋 Funcionalidades Implementadas

#### RF1: Autenticación y Autorización
- Login con RUT y correo institucional
- Tokens JWT para sesiones
- Roles: estudiante y administrador

#### RF2: Gestión de Usuarios
- CRUD completo de usuarios
- Perfiles con información académica
- Activación/desactivación de cuentas

#### RF3: Administración de Espacios
- Gestión de salas, canchas y laboratorios
- Capacidad y características
- Control de disponibilidad

#### RF4: Consulta de Disponibilidad
- Búsqueda en tiempo real
- Filtros múltiples (fecha, hora, tipo)
- Calendario visual interactivo

#### RF5: Sistema de Reservas
- Creación con validaciones
- Estados: pendiente, aprobada, rechazada, cancelada
- Reservas recurrentes (diaria/semanal)
- Límites configurables por usuario
- Aprobación administrativa

#### RF6: Gestión de Incidencias
- Registro de problemas en espacios
- Prioridades: baja, media, alta, crítica
- Estados de seguimiento
- Bloqueo automático de espacios
- Cancelación de reservas afectadas

#### RF7: Configuración del Sistema
- Parámetros dinámicos
- Horarios de operación
- Límites de reservas
- Anticipación mínima
- Auditoría de cambios

#### RF8: Sistema de Notificaciones
- 5 plantillas de correo profesionales
- Eventos: creación, aprobación, rechazo, cancelación, bloqueo
- Prevención de duplicados
- Historial de envíos
- Integración automática con eventos

#### RF9: Reportes y Auditoría
- Estadísticas generales del sistema
- Reporte de uso de espacios
- Historial completo de auditoría
- Reporte de incidencias
- Tasas de aprobación/rechazo
- Exportación de datos

### 💻 Stack Tecnológico

#### Backend
- **Lenguaje**: Python 3.13
- **Framework**: FastAPI 0.109
- **ORM**: SQLAlchemy 2.0
- **Base de Datos**: PostgreSQL 14
- **Autenticación**: JWT (python-jose)
- **Servidor**: Uvicorn (ASGI)

#### Frontend
- **Runtime**: Node.js 20.x
- **Framework**: Express.js 4.x
- **Template Engine**: EJS
- **CSS Framework**: Bootstrap 5.1
- **Icons**: Font Awesome 6.0
- **HTTP Client**: Axios

#### Protocolo SOA
- Formato personalizado: `[LONGITUD:5][SERVICIO:5][DATOS:JSON]`
- Comunicación HTTP entre servicios
- Mensajes en formato JSON/UTF-8

### 📊 Métricas del Proyecto

#### Código
- **Líneas de código Python**: ~3,500
- **Líneas de código JavaScript**: ~2,000
- **Servicios backend**: 9
- **Endpoints REST**: 45+
- **Modelos de datos**: 9 tablas

#### Funcionalidades
- **Módulos funcionales**: 9
- **Vistas web**: 14 (7 por cliente)
- **Tipos de usuario**: 2 (estudiante, admin)
- **Estados de reserva**: 4
- **Tipos de notificación**: 5

### 🎓 Aprendizajes Técnicos

1. **Arquitectura SOA**
   - Diseño de servicios independientes
   - Comunicación inter-servicios
   - Protocolo de mensajería personalizado

2. **Desarrollo Full-Stack**
   - Backend con FastAPI
   - Frontend con Node.js/Express
   - Integración cliente-servidor

3. **Bases de Datos**
   - Diseño de esquema relacional
   - Optimización con índices
   - Sistema de auditoría

4. **Seguridad**
   - Autenticación JWT
   - Autorización basada en roles
   - Validación de datos

5. **Patrones de Diseño**
   - Repository pattern
   - Service layer
   - DTO (Data Transfer Objects)

### 📈 Escalabilidad y Mantenibilidad

#### Ventajas de la Arquitectura SOA

✅ **Escalabilidad Horizontal**: Cada servicio puede escalarse independientemente

✅ **Mantenibilidad**: Cambios aislados no afectan otros servicios

✅ **Reutilización**: Servicios pueden ser consumidos por múltiples clientes

✅ **Tecnología Agnóstica**: Cada servicio puede usar diferentes tecnologías

✅ **Desarrollo Paralelo**: Equipos pueden trabajar en servicios diferentes simultáneamente

✅ **Testing Independiente**: Servicios se prueban aisladamente

### 🔮 Posibles Mejoras Futuras

1. **Funcionalidades**
   - Sistema de pagos para espacios premium
   - Integración con calendario institucional
   - App móvil nativa (iOS/Android)
   - Sistema de rating de espacios
   - Chat en vivo con administradores

2. **Técnicas**
   - Containerización con Docker
   - Orquestación con Kubernetes
   - Cache con Redis
   - Message broker (RabbitMQ/Kafka)
   - Monitoreo con Prometheus/Grafana
   - CI/CD con GitHub Actions

3. **Seguridad**
   - 2FA (autenticación de dos factores)
   - CAPTCHA en formularios
   - Rate limiting avanzado
   - Encriptación de datos sensibles

### 📚 Documentación Entregable

- ✅ README.md completo
- ✅ Guía de instalación (INSTALACION.md)
- ✅ Guía de despliegue (DEPLOY.md)
- ✅ Guía de contribución (CONTRIBUTING.md)
- ✅ Changelog (CHANGELOG.md)
- ✅ Licencia (LICENSE)
- ✅ Informe técnico (Informe.tex)
- ✅ Diagramas de arquitectura
- ✅ Documentación de API (Swagger/OpenAPI)

### 🎯 Conclusiones

El proyecto logra exitosamente:

1. ✅ Implementar una arquitectura SOA funcional y escalable
2. ✅ Desarrollar 9 microservicios independientes y cohesivos
3. ✅ Crear interfaces web intuitivas para diferentes tipos de usuarios
4. ✅ Implementar todas las funcionalidades requeridas (RF1-RF9)
5. ✅ Documentar comprehensivamente el sistema
6. ✅ Aplicar buenas prácticas de desarrollo de software
7. ✅ Demostrar conocimientos en arquitectura de software moderna

El sistema es funcional, bien documentado y listo para ser utilizado como base para un sistema de reservas real en entorno universitario.

### 📞 Información del Proyecto

- **Universidad**: Universidad Diego Portales
- **Curso**: Arquitectura de Software
- **Año**: 2025
- **Tipo**: Proyecto Académico
- **Repositorio**: https://github.com/Suxx12/ARQ-Software

---

**Nota**: Este documento proporciona una visión general del proyecto. Para detalles técnicos completos, consultar la documentación específica de cada componente.
