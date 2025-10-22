/**
 * Servidor Cliente Web para Administradores
 * Sistema de Reservación UDP
 * Puerto: 3001
 */
const express = require('express');
const path = require('path');
const bodyParser = require('body-parser');
const cookieParser = require('cookie-parser');
const axios = require('axios');
const moment = require('moment');

const app = express();
const PORT = process.env.PORT || 3001;

// Configuración
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));
app.use(express.static(path.join(__dirname, 'public')));
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());
app.use(cookieParser());

// Configuración de servicios
const SERVICES = {
    auth: 'http://localhost:5001',
    user: 'http://localhost:5002',
    space: 'http://localhost:5003',
    avail: 'http://localhost:5004',
    book: 'http://localhost:5005',
    incid: 'http://localhost:5006',
    admin: 'http://localhost:5007',
    notif: 'http://localhost:5008',
    report: 'http://localhost:5009'
};

// Middleware para verificar autenticación de administrador
const requireAdminAuth = async (req, res, next) => {
    const token = req.cookies.token;
    if (!token) {
        return res.redirect('/login');
    }
    
    try {
        const response = await axios.get(`${SERVICES.auth}/auth/verify/${token}`);
        if (response.data.valid && response.data.user_info.tipo_usuario === 'administrador') {
            req.user = response.data.user_info;
            next();
        } else {
            res.clearCookie('token');
            res.redirect('/login?error=Acceso denegado. Se requiere rol de administrador.');
        }
    } catch (error) {
        console.error('Error verificando token:', error.message);
        res.clearCookie('token');
        res.redirect('/login');
    }
};

// Rutas
app.get('/', (req, res) => {
    res.render('index', { title: 'Panel de Administración UDP' });
});

app.get('/login', (req, res) => {
    const error = req.query.error;
    res.render('login', { title: 'Acceso de Administrador', error });
});

app.post('/login', async (req, res) => {
    try {
        const { rut, password } = req.body;
        
        const response = await axios.post(`${SERVICES.auth}/auth/login`, {
            rut: rut,
            password: password
        });
        
        if (response.data.ok && response.data.user_info.tipo_usuario === 'administrador') {
            res.cookie('token', response.data.token, { httpOnly: true });
            res.redirect('/dashboard');
        } else {
            res.render('login', { 
                title: 'Acceso de Administrador',
                error: 'Credenciales inválidas o no tienes permisos de administrador'
            });
        }
    } catch (error) {
        console.error('Error en login:', error.message);
        res.render('login', { 
            title: 'Acceso de Administrador',
            error: 'Error al iniciar sesión'
        });
    }
});

app.get('/logout', (req, res) => {
    res.clearCookie('token');
    res.redirect('/');
});

app.get('/dashboard', requireAdminAuth, async (req, res) => {
    try {
        // Obtener estadísticas generales
        const [usersResponse, spacesResponse] = await Promise.all([
            axios.get(`${SERVICES.user}/users`),
            axios.get(`${SERVICES.space}/spaces`)
        ]);
        
        const users = usersResponse.data;
        const spaces = spacesResponse.data;
        
        // Obtener todas las reservas para estadísticas
        let allBookings = [];
        let pendingBookings = [];
        try {
            const allBookingsResponse = await axios.get(`${SERVICES.book}/bookings`);
            allBookings = allBookingsResponse.data;
            pendingBookings = allBookings.filter(b => b.estado === 'pendiente');
            console.log(`Total reservas: ${allBookings.length}, Pendientes: ${pendingBookings.length}`);
        } catch (e) {
            console.log('Error obteniendo reservas:', e.message);
        }
        
        // Obtener incidencias
        let incidents = [];
        try {
            const incidentsResponse = await axios.get(`${SERVICES.incid}/incidents`);
            incidents = incidentsResponse.data;
        } catch (e) {
            console.log('Error obteniendo incidencias:', e.message);
        }
        
        res.render('dashboard', {
            title: 'Panel de Administración',
            user: req.user,
            stats: {
                totalUsers: users.length,
                totalSpaces: spaces.length,
                totalBookings: allBookings.length,
                totalIncidents: incidents.length
            },
            recentBookings: pendingBookings.slice(0, 10),
            recentIncidents: incidents.slice(0, 5)
        });
    } catch (error) {
        console.error('Error cargando dashboard:', error.message);
        res.render('dashboard', {
            title: 'Panel de Administración',
            user: req.user,
            stats: { totalUsers: 0, totalSpaces: 0, totalBookings: 0, totalIncidents: 0 },
            recentBookings: [],
            recentIncidents: [],
            error: 'Error cargando datos'
        });
    }
});

// Gestión de Usuarios
app.get('/usuarios', requireAdminAuth, async (req, res) => {
    try {
        const response = await axios.get(`${SERVICES.user}/users`);
        const users = response.data;
        
        res.render('usuarios', {
            title: 'Gestión de Usuarios',
            user: req.user,
            users: users,
            success: req.query.success,
            error: req.query.error
        });
    } catch (error) {
        console.error('Error cargando usuarios:', error.message);
        res.render('usuarios', {
            title: 'Gestión de Usuarios',
            user: req.user,
            users: [],
            error: 'Error cargando usuarios'
        });
    }
});

app.post('/usuarios/crear', requireAdminAuth, async (req, res) => {
    try {
        const { rut, correo_institucional, nombre, tipo_usuario } = req.body;
        
        await axios.post(`${SERVICES.user}/users/create`, {
            rut,
            correo_institucional,
            nombre,
            tipo_usuario
        });
        
        res.redirect('/usuarios?success=Usuario creado exitosamente');
    } catch (error) {
        console.error('Error creando usuario:', error.message);
        const errorMsg = error.response?.data?.detail || 'Error al crear usuario';
        res.redirect('/usuarios?error=' + encodeURIComponent(errorMsg));
    }
});

app.post('/usuarios/actualizar', requireAdminAuth, async (req, res) => {
    try {
        const { user_id, nombre, tipo_usuario } = req.body;
        
        await axios.put(`${SERVICES.user}/users/${user_id}`, {
            nombre,
            tipo_usuario
        });
        
        res.redirect('/usuarios?success=Usuario actualizado exitosamente');
    } catch (error) {
        console.error('Error actualizando usuario:', error.message);
        const errorMsg = error.response?.data?.detail || 'Error al actualizar usuario';
        res.redirect('/usuarios?error=' + encodeURIComponent(errorMsg));
    }
});

app.post('/usuarios/cambiar-rol', requireAdminAuth, async (req, res) => {
    try {
        const { user_id, new_role } = req.body;
        
        await axios.post(`${SERVICES.user}/users/change-role`, {
            user_id: parseInt(user_id),
            new_role: new_role
        });
        
        res.redirect('/usuarios?success=Rol actualizado exitosamente');
    } catch (error) {
        console.error('Error cambiando rol:', error.message);
        const errorMsg = error.response?.data?.detail || 'Error al cambiar rol';
        res.redirect('/usuarios?error=' + encodeURIComponent(errorMsg));
    }
});

app.post('/usuarios/desactivar', requireAdminAuth, async (req, res) => {
    try {
        const { user_id } = req.body;
        
        await axios.delete(`${SERVICES.user}/users/${user_id}`);
        
        res.redirect('/usuarios?success=Usuario desactivado exitosamente');
    } catch (error) {
        console.error('Error desactivando usuario:', error.message);
        const errorMsg = error.response?.data?.detail || 'Error al desactivar usuario';
        res.redirect('/usuarios?error=' + encodeURIComponent(errorMsg));
    }
});

app.post('/usuarios/activar', requireAdminAuth, async (req, res) => {
    try {
        const { user_id } = req.body;
        
        await axios.put(`${SERVICES.user}/users/${user_id}`, {
            activo: true
        });
        
        res.redirect('/usuarios?success=Usuario activado exitosamente');
    } catch (error) {
        console.error('Error activando usuario:', error.message);
        const errorMsg = error.response?.data?.detail || 'Error al activar usuario';
        res.redirect('/usuarios?error=' + encodeURIComponent(errorMsg));
    }
});

// Gestión de Espacios
app.get('/espacios', requireAdminAuth, async (req, res) => {
    try {
        const response = await axios.get(`${SERVICES.space}/spaces`);
        const spaces = response.data;
        
        res.render('espacios', {
            title: 'Gestión de Espacios',
            user: req.user,
            spaces: spaces,
            success: req.query.success,
            error: req.query.error
        });
    } catch (error) {
        console.error('Error cargando espacios:', error.message);
        res.render('espacios', {
            title: 'Gestión de Espacios',
            user: req.user,
            spaces: [],
            error: 'Error cargando espacios'
        });
    }
});

app.post('/espacios/crear', requireAdminAuth, async (req, res) => {
    try {
        const { nombre, tipo, capacidad } = req.body;
        
        await axios.post(`${SERVICES.space}/spaces/create`, {
            nombre,
            tipo,
            capacidad: parseInt(capacidad)
        });
        
        res.redirect('/espacios?success=Espacio creado exitosamente');
    } catch (error) {
        console.error('Error creando espacio:', error.message);
        const errorMsg = error.response?.data?.detail || 'Error al crear espacio';
        res.redirect('/espacios?error=' + encodeURIComponent(errorMsg));
    }
});

app.post('/espacios/actualizar', requireAdminAuth, async (req, res) => {
    try {
        const { space_id, nombre, tipo, capacidad } = req.body;
        
        await axios.put(`${SERVICES.space}/spaces/${space_id}`, {
            nombre,
            tipo,
            capacidad: parseInt(capacidad)
        });
        
        res.redirect('/espacios?success=Espacio actualizado exitosamente');
    } catch (error) {
        console.error('Error actualizando espacio:', error.message);
        const errorMsg = error.response?.data?.detail || 'Error al actualizar espacio';
        res.redirect('/espacios?error=' + encodeURIComponent(errorMsg));
    }
});

app.post('/espacios/desactivar', requireAdminAuth, async (req, res) => {
    try {
        const { space_id } = req.body;
        
        await axios.delete(`${SERVICES.space}/spaces/${space_id}`);
        
        res.redirect('/espacios?success=Espacio desactivado exitosamente');
    } catch (error) {
        console.error('Error desactivando espacio:', error.message);
        const errorMsg = error.response?.data?.detail || 'Error al desactivar espacio';
        res.redirect('/espacios?error=' + encodeURIComponent(errorMsg));
    }
});

app.post('/espacios/activar', requireAdminAuth, async (req, res) => {
    try {
        const { space_id } = req.body;
        
        await axios.put(`${SERVICES.space}/spaces/${space_id}`, {
            activo: true
        });
        
        res.redirect('/espacios?success=Espacio activado exitosamente');
    } catch (error) {
        console.error('Error activando espacio:', error.message);
        const errorMsg = error.response?.data?.detail || 'Error al activar espacio';
        res.redirect('/espacios?error=' + encodeURIComponent(errorMsg));
    }
});

// Gestión de Reservas
app.get('/reservas', requireAdminAuth, async (req, res) => {
    try {
        // Obtener todas las reservas (sin filtro de estado para ver todas)
        const response = await axios.get(`${SERVICES.book}/bookings`);
        const bookings = response.data;
        
        res.render('reservas', {
            title: 'Gestión de Reservas',
            user: req.user,
            bookings: bookings,
            success: req.query.success,
            error: req.query.error
        });
    } catch (error) {
        console.error('Error cargando reservas:', error.message);
        res.render('reservas', {
            title: 'Gestión de Reservas',
            user: req.user,
            bookings: [],
            error: 'Error cargando reservas'
        });
    }
});

app.post('/reservas/aprobar', requireAdminAuth, async (req, res) => {
    try {
        const { booking_id, estado, motivo } = req.body;
        
        await axios.post(`${SERVICES.book}/bookings/approve`, {
            id_reserva: parseInt(booking_id),
            estado: estado,
            id_administrador: req.user.id,
            motivo: motivo
        });
        
        res.redirect('/reservas?success=Reserva ' + estado + ' exitosamente');
    } catch (error) {
        console.error('Error aprobando/rechazando reserva:', error.message);
        res.redirect('/reservas?error=Error al procesar reserva');
    }
});

// Gestión de Incidencias
app.get('/incidencias', requireAdminAuth, async (req, res) => {
    try {
        const [incidentsResponse, spacesResponse] = await Promise.all([
            axios.get(`${SERVICES.incid}/incidents`),
            axios.get(`${SERVICES.space}/spaces`)
        ]);
        
        const incidents = incidentsResponse.data;
        const spaces = spacesResponse.data;
        
        res.render('incidencias', {
            title: 'Gestión de Incidencias',
            user: req.user,
            incidents: incidents,
            spaces: spaces,
            success: req.query.success,
            error: req.query.error
        });
    } catch (error) {
        console.error('Error cargando incidencias:', error.message);
        res.render('incidencias', {
            title: 'Gestión de Incidencias',
            user: req.user,
            incidents: [],
            spaces: [],
            error: 'Error cargando incidencias'
        });
    }
});

app.post('/incidencias/reportar', requireAdminAuth, async (req, res) => {
    try {
        const { id_espacio, tipo_incidencia, descripcion } = req.body;
        
        console.log('Reportando incidencia:', {
            id_espacio,
            tipo_incidencia,
            descripcion,
            usuario_id: req.user.id,
            usuario_nombre: req.user.nombre
        });
        
        const response = await axios.post(`${SERVICES.incid}/incidents/report`, {
            id_espacio: parseInt(id_espacio),
            tipo_incidencia: tipo_incidencia,
            descripcion: descripcion,
            id_usuario_reporta: req.user.id
        });
        
        console.log('Incidencia creada:', response.data);
        res.redirect('/incidencias?success=Incidencia reportada exitosamente');
    } catch (error) {
        console.error('Error reportando incidencia:', error.response?.data || error.message);
        res.redirect('/incidencias?error=Error al reportar incidencia: ' + (error.response?.data?.detail || error.message));
    }
});

app.post('/incidencias/bloquear', requireAdminAuth, async (req, res) => {
    try {
        const { id_incidencia, fecha_inicio, fecha_fin } = req.body;
        
        await axios.post(`${SERVICES.incid}/incidents/block`, {
            id_incidencia: parseInt(id_incidencia),
            fecha_inicio: fecha_inicio,
            fecha_fin: fecha_fin,
            id_administrador: req.user.id
        });
        
        res.redirect('/incidencias?success=Bloqueo aplicado. Reservas afectadas han sido canceladas.');
    } catch (error) {
        console.error('Error aplicando bloqueo:', error.message);
        res.redirect('/incidencias?error=Error al aplicar bloqueo');
    }
});

app.post('/incidencias/resolver', requireAdminAuth, async (req, res) => {
    try {
        const { id_incidencia, solucion } = req.body;
        
        await axios.post(`${SERVICES.incid}/incidents/resolve`, {
            id_incidencia: parseInt(id_incidencia),
            solucion: solucion,
            id_usuario_resuelve: req.user.id
        });
        
        res.redirect('/incidencias?success=Incidencia resuelta exitosamente');
    } catch (error) {
        console.error('Error resolviendo incidencia:', error.message);
        res.redirect('/incidencias?error=Error al resolver incidencia');
    }
});

// Configuración del Sistema
app.get('/configuracion', requireAdminAuth, async (req, res) => {
    try {
        const response = await axios.get(`${SERVICES.admin}/admin/config`);
        const config = response.data;
        
        // Obtener auditoría si hay filtro de fecha
        let auditLogs = [];
        if (req.query.fecha) {
            try {
                const auditResponse = await axios.get(`${SERVICES.admin}/admin/audit`, {
                    params: { fecha: req.query.fecha }
                });
                auditLogs = auditResponse.data.filter(log => log.tabla_afectada === 'configuraciones');
            } catch (auditError) {
                console.error('Error cargando auditoría:', auditError.message);
            }
        }
        
        res.render('configuracion', {
            title: 'Configuración del Sistema',
            user: req.user,
            config: config,
            auditLogs: auditLogs,
            success: req.query.success,
            error: req.query.error
        });
    } catch (error) {
        console.error('Error cargando configuración:', error.message);
        res.render('configuracion', {
            title: 'Configuración del Sistema',
            user: req.user,
            config: {},
            auditLogs: [],
            error: 'Error cargando configuración'
        });
    }
});

app.get('/configuracion/auditoria', requireAdminAuth, async (req, res) => {
    res.redirect(`/configuracion${req.query.fecha ? '?fecha=' + req.query.fecha : ''}`);
});

app.post('/configuracion/actualizar', requireAdminAuth, async (req, res) => {
    try {
        const configData = req.body;
        
        await axios.put(`${SERVICES.admin}/admin/config`, configData);
        
        res.redirect('/configuracion?success=Configuración actualizada exitosamente');
    } catch (error) {
        console.error('Error actualizando configuración:', error.message);
        const errorMsg = error.response?.data?.detail || 'Error al actualizar configuración';
        res.redirect('/configuracion?error=' + encodeURIComponent(errorMsg));
    }
});

// API Reportes
app.get('/api/reports/estadisticas', requireAdminAuth, async (req, res) => {
    try {
        const response = await axios.get(`${SERVICES.report}/reports/estadisticas`);
        res.json(response.data);
    } catch (error) {
        console.error('Error obteniendo estadísticas:', error.message);
        res.status(500).json({ error: 'Error obteniendo estadísticas' });
    }
});

app.post('/api/reports/uso', requireAdminAuth, async (req, res) => {
    try {
        const response = await axios.post(`${SERVICES.report}/reports/uso`, req.body);
        res.json(response.data);
    } catch (error) {
        console.error('Error generando reporte de uso:', error.message);
        res.status(500).json({ error: 'Error generando reporte' });
    }
});

app.get('/api/reports/auditoria', requireAdminAuth, async (req, res) => {
    try {
        const response = await axios.get(`${SERVICES.report}/reports/auditoria`, {
            params: req.query
        });
        res.json(response.data);
    } catch (error) {
        console.error('Error obteniendo auditoría:', error.message);
        res.status(500).json({ error: 'Error obteniendo auditoría' });
    }
});

app.get('/api/reports/incidencias', requireAdminAuth, async (req, res) => {
    try {
        const response = await axios.get(`${SERVICES.report}/reports/incidencias`);
        res.json(response.data);
    } catch (error) {
        console.error('Error obteniendo reporte de incidencias:', error.message);
        res.status(500).json({ error: 'Error obteniendo reporte' });
    }
});

// Reportes
app.get('/reportes', requireAdminAuth, async (req, res) => {
    try {
        res.render('reportes', {
            title: 'Reportes y Auditoría',
            user: req.user
        });
    } catch (error) {
        console.error('Error cargando vista de reportes:', error.message);
        res.render('reportes', {
            title: 'Reportes y Auditoría',
            user: req.user,
            error: 'Error cargando reportes'
        });
    }
});

// Manejo de errores
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).render('error', {
        title: 'Error',
        error: 'Error interno del servidor'
    });
});

// Iniciar servidor
app.listen(PORT, () => {
    console.log(`Cliente Web Administradores ejecutándose en http://localhost:${PORT}`);
});




