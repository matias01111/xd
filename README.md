# Sistema de Reservación de Salas y Canchas - UDP

Sistema desarrollado para la Universidad Diego Portales que permite la gestión digital de reservas de salas y canchas utilizando arquitectura SOA.

## Arquitectura del Sistema

El sistema está implementado con **Arquitectura Orientada a Servicios (SOA)** con los siguientes componentes:

### Servicios Backend
1. **AUTH** - Servicio de Autenticación
2. **USER** - Servicio de Usuarios
3. **SPACE** - Servicio de Espacios
4. **AVAIL** - Servicio de Disponibilidad
5. **BOOK** - Servicio de Reservas
6. **INCID** - Servicio de Incidencias
7. **ADMIN** - Servicio de Administración
8. **NOTIF** - Servicio de Notificaciones
9. **REPRT** - Servicio de Reportes

### Clientes
1. **Cliente Web Estudiantes**
2. **Cliente Web Administradores**

### Base de Datos
- **PostgreSQL** con las siguientes tablas principales:
  - `usuarios`
  - `espacios`
  - `reservas`
  - `configuraciones`

## Requisitos del Sistema

- Python 3.8+
- PostgreSQL 12+
- Node.js 16+ (para clientes web)

## Instalación

1. Clonar el repositorio
2. Configurar base de datos PostgreSQL
3. Ejecutar scripts de inicialización
4. Instalar dependencias de Python
5. Ejecutar servicios backend
6. Instalar dependencias de clientes web
7. Ejecutar clientes web

## Uso

### Servicios Backend
Cada servicio se ejecuta en un puerto diferente y se comunican a través del bus de servicios (puerto 5000).

### Clientes Web
- Cliente Estudiantes: Puerto 3000
- Cliente Administradores: Puerto 3001

## Comunicación SOA

Los servicios se comunican usando el formato:
```
NNNNNSSSSSDATOS
```

Donde:
- `NNNNN`: Longitud del mensaje (5 dígitos)
- `SSSSS`: Código del servicio (5 caracteres)
- `DATOS`: JSON en UTF-8

