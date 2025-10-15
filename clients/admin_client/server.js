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
        const [usersResponse, spacesResponse, bookingsResponse, incidentsResponse] = await Promise.all([
            axios.get(`${SERVICES.user}/users`),
            axios.get(`${SERVICES.space}/spaces`),
            axios.get(`${SERVICES.book}/bookings/user/1`), // Obtener todas las reservas
            axios.get(`${SERVICES.incid}/incidents`)
        ]);
        
        const users = usersResponse.data;
        const spaces = spacesResponse.data;
        const bookings = bookingsResponse.data;
        const incidents = incidentsResponse.data;
        
        res.render('dashboard', {
            title: 'Panel de Administración',
            user: req.user,
            stats: {
                totalUsers: users.length,
                totalSpaces: spaces.length,
                totalBookings: bookings.length,
                totalIncidents: incidents.length
            },
            recentBookings: bookings.slice(0, 10),
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
            users: users
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
        res.redirect('/usuarios?error=Error al crear usuario');
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
        res.redirect('/usuarios?error=Error al cambiar rol');
    }
});

// Gestión de Reservas
app.get('/reservas', requireAdminAuth, async (req, res) => {
    try {
        const response = await axios.get(`${SERVICES.book}/bookings/user/1`);
        const bookings = response.data;
        
        res.render('reservas', {
            title: 'Gestión de Reservas',
            user: req.user,
            bookings: bookings
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
        const response = await axios.get(`${SERVICES.incid}/incidents`);
        const incidents = response.data;
        
        res.render('incidencias', {
            title: 'Gestión de Incidencias',
            user: req.user,
            incidents: incidents
        });
    } catch (error) {
        console.error('Error cargando incidencias:', error.message);
        res.render('incidencias', {
            title: 'Gestión de Incidencias',
            user: req.user,
            incidents: [],
            error: 'Error cargando incidencias'
        });
    }
});

app.post('/incidencias/resolver', requireAdminAuth, async (req, res) => {
    try {
        const { incident_id, solucion } = req.body;
        
        await axios.post(`${SERVICES.incid}/incidents/resolve`, {
            id_incidencia: parseInt(incident_id),
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
        
        res.render('configuracion', {
            title: 'Configuración del Sistema',
            user: req.user,
            config: config
        });
    } catch (error) {
        console.error('Error cargando configuración:', error.message);
        res.render('configuracion', {
            title: 'Configuración del Sistema',
            user: req.user,
            config: {},
            error: 'Error cargando configuración'
        });
    }
});

app.post('/configuracion/actualizar', requireAdminAuth, async (req, res) => {
    try {
        const configData = req.body;
        
        await axios.put(`${SERVICES.admin}/admin/config`, configData);
        
        res.redirect('/configuracion?success=Configuración actualizada exitosamente');
    } catch (error) {
        console.error('Error actualizando configuración:', error.message);
        res.redirect('/configuracion?error=Error al actualizar configuración');
    }
});

// Reportes
app.get('/reportes', requireAdminAuth, async (req, res) => {
    try {
        const fechaInicio = req.query.fecha_inicio || moment().subtract(30, 'days').format('YYYY-MM-DD');
        const fechaFin = req.query.fecha_fin || moment().format('YYYY-MM-DD');
        
        const response = await axios.post(`${SERVICES.report}/reports/uso`, {
            fecha_inicio: fechaInicio,
            fecha_fin: fechaFin
        });
        
        const reporte = response.data;
        
        res.render('reportes', {
            title: 'Reportes del Sistema',
            user: req.user,
            reporte: reporte,
            fechaInicio: fechaInicio,
            fechaFin: fechaFin
        });
    } catch (error) {
        console.error('Error generando reportes:', error.message);
        res.render('reportes', {
            title: 'Reportes del Sistema',
            user: req.user,
            reporte: null,
            error: 'Error generando reportes'
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




