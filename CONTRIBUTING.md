# Guía de Contribución

## 🎓 Proyecto Académico

Este es un proyecto académico para el curso de Arquitectura de Software de la Universidad Diego Portales.

## 🤝 Cómo Contribuir

### Reportar Bugs

Si encuentras un bug, por favor abre un issue con:
- Descripción clara del problema
- Pasos para reproducirlo
- Comportamiento esperado vs. comportamiento actual
- Capturas de pantalla si es posible
- Información del entorno (SO, versiones de Python/Node.js)

### Sugerir Mejoras

Para sugerir nuevas funcionalidades:
1. Abre un issue describiendo la funcionalidad
2. Explica por qué sería útil
3. Proporciona ejemplos de uso

### Pull Requests

1. **Fork** el repositorio
2. **Crea una rama** para tu feature (`git checkout -b feature/NuevaFuncionalidad`)
3. **Commit** tus cambios (`git commit -m 'Añade nueva funcionalidad'`)
4. **Push** a la rama (`git push origin feature/NuevaFuncionalidad`)
5. Abre un **Pull Request**

## 📝 Estándares de Código

### Python
- Sigue PEP 8
- Usa type hints donde sea posible
- Documenta funciones con docstrings
- Máximo 120 caracteres por línea

```python
def crear_reserva(usuario_id: int, espacio_id: int, fecha: datetime) -> Reserva:
    """
    Crea una nueva reserva en el sistema.
    
    Args:
        usuario_id: ID del usuario que hace la reserva
        espacio_id: ID del espacio a reservar
        fecha: Fecha y hora de la reserva
        
    Returns:
        Objeto Reserva creado
        
    Raises:
        ValueError: Si los datos son inválidos
    """
    pass
```

### JavaScript/Node.js
- Usa nombres descriptivos
- Comenta código complejo
- Usa `async/await` en lugar de callbacks
- Maneja errores apropiadamente

```javascript
async function aprobarReserva(reservaId) {
    try {
        const response = await axios.post(`/api/reservas/${reservaId}/aprobar`);
        return response.data;
    } catch (error) {
        console.error('Error aprobando reserva:', error);
        throw error;
    }
}
```

## 🏗️ Estructura de Commits

Usa mensajes de commit descriptivos siguiendo este formato:

```
tipo(alcance): descripción corta

Descripción más detallada si es necesario.

- Cambio 1
- Cambio 2
```

**Tipos:**
- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Cambios en documentación
- `style`: Formato, sin cambios de código
- `refactor`: Refactorización de código
- `test`: Añadir o modificar tests
- `chore`: Tareas de mantenimiento

**Ejemplos:**
```
feat(reservas): añade validación de horarios

Implementa validación para evitar reservas fuera del horario permitido.

- Valida hora mínima y máxima
- Verifica días de la semana
- Añade tests unitarios
```

## 🧪 Testing

Antes de hacer un PR, asegúrate de:
- [ ] Probar todos los servicios backend
- [ ] Verificar clientes web en diferentes navegadores
- [ ] Comprobar que no hay errores en consola
- [ ] Validar que la base de datos se inicializa correctamente

## 📚 Documentación

Al añadir nuevas funcionalidades:
- Actualiza el README.md si es necesario
- Documenta nuevos endpoints en el código
- Añade ejemplos de uso
- Actualiza diagramas si la arquitectura cambia

## 🔧 Configuración de Desarrollo

### Configurar Entorno

```bash
# Clonar repositorio
git clone https://github.com/Suxx12/ARQ-Software.git
cd ARQ-Software

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar base de datos
python setup_database.py
```

### Ejecutar en Modo Desarrollo

```bash
# Terminal 1: Servicios
python start_services.py

# Terminal 2: Clientes
python start_clients.py
```

## 🐛 Debugging

### Ver Logs de Servicios

Los servicios imprimen logs en consola. Para debugging más detallado:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Inspeccionar Base de Datos

```bash
psql -U postgres -d reservas_udp

# Ver todas las reservas
SELECT * FROM reservas;

# Ver usuarios
SELECT * FROM usuarios;
```

## 📞 Contacto

Para preguntas sobre el proyecto académico, contacta a los autores del equipo.

## ⚖️ Licencia

Este proyecto es de uso académico para la Universidad Diego Portales.
