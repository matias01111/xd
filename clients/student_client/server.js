/**
 * Servidor Cliente Web para Estudiantes
 * Sistema de Reservación UDP
 * Puerto: 3000
 */
const express = require('express');
const path = require('path');
const bodyParser = require('body-parser');
const cookieParser = require('cookie-parser');
const axios = require('axios');
const moment = require('moment');

const app = express();
const PORT = process.env.PORT || 3000;

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
    avail: 'http://localhost:5004',
    book: 'http://localhost:5005',
    space: 'http://localhost:5003'
};

// Middleware para verificar autenticación
const requireAuth = async (req, res, next) => {
    const token = req.cookies.token;
    if (!token) {
        return res.redirect('/login');
    }
    
    try {
        const response = await axios.get(`${SERVICES.auth}/auth/verify/${token}`);
        if (response.data.valid) {
            req.user = response.data.user_info;
            next();
        } else {
            res.clearCookie('token');
            res.redirect('/login');
        }
    } catch (error) {
        console.error('Error verificando token:', error.message);
        res.clearCookie('token');
        res.redirect('/login');
    }
};

// Rutas
app.get('/', (req, res) => {
    res.render('index', { title: 'Sistema de Reservas UDP' });
});

app.get('/login', (req, res) => {
    res.render('login', { title: 'Iniciar Sesión' });
});

app.post('/login', async (req, res) => {
    try {
        const { rut, password } = req.body;
        
        const response = await axios.post(`${SERVICES.auth}/auth/login`, {
            rut: rut,
            password: password
        });
        
        if (response.data.ok) {
            res.cookie('token', response.data.token, { httpOnly: true });
            res.redirect('/dashboard');
        } else {
            res.render('login', { 
                title: 'Iniciar Sesión',
                error: 'Credenciales inválidas'
            });
        }
    } catch (error) {
        console.error('Error en login:', error.message);
        res.render('login', { 
            title: 'Iniciar Sesión',
            error: 'Error al iniciar sesión'
        });
    }
});

app.get('/logout', (req, res) => {
    res.clearCookie('token');
    res.redirect('/');
});

app.get('/dashboard', requireAuth, async (req, res) => {
    try {
        // Obtener reservas del usuario
        const bookingsResponse = await axios.get(`${SERVICES.book}/bookings/user/${req.user.id}`);
        const bookings = bookingsResponse.data;
        
        // Obtener espacios disponibles
        const spacesResponse = await axios.get(`${SERVICES.space}/spaces`);
        const spaces = spacesResponse.data;
        
        res.render('dashboard', {
            title: 'Mi Panel de Reservas',
            user: req.user,
            bookings: bookings,
            spaces: spaces
        });
    } catch (error) {
        console.error('Error cargando dashboard:', error.message);
        res.render('dashboard', {
            title: 'Mi Panel de Reservas',
            user: req.user,
            bookings: [],
            spaces: [],
            error: 'Error cargando datos'
        });
    }
});

app.get('/disponibilidad', requireAuth, (req, res) => {
    res.render('disponibilidad', {
        title: 'Consultar Disponibilidad',
        user: req.user
    });
});

app.post('/disponibilidad', requireAuth, async (req, res) => {
    try {
        const { fecha, hora, duracion, tipo_espacio } = req.body;
        
        const response = await axios.post(`${SERVICES.avail}/availability/check`, {
            fecha: fecha,
            hora: hora,
            duracion: parseInt(duracion),
            tipo_espacio: tipo_espacio || null
        });
        
        res.render('disponibilidad', {
            title: 'Consultar Disponibilidad',
            user: req.user,
            results: response.data,
            searchParams: req.body
        });
    } catch (error) {
        console.error('Error consultando disponibilidad:', error.message);
        res.render('disponibilidad', {
            title: 'Consultar Disponibilidad',
            user: req.user,
            error: 'Error consultando disponibilidad'
        });
    }
});

app.post('/reservar', requireAuth, async (req, res) => {
    try {
        const { id_espacio, fecha_inicio, fecha_fin, motivo } = req.body;
        
        const response = await axios.post(`${SERVICES.book}/bookings/create`, {
            id_usuario: req.user.id,
            id_espacio: parseInt(id_espacio),
            fecha_inicio: fecha_inicio,
            fecha_fin: fecha_fin,
            motivo: motivo
        });
        
        res.redirect('/dashboard?success=Reserva creada exitosamente');
    } catch (error) {
        console.error('Error creando reserva:', error.message);
        res.redirect('/dashboard?error=Error al crear reserva');
    }
});

app.post('/cancelar-reserva', requireAuth, async (req, res) => {
    try {
        const { booking_id } = req.body;
        
        await axios.delete(`${SERVICES.book}/bookings/${booking_id}`);
        
        res.redirect('/dashboard?success=Reserva cancelada exitosamente');
    } catch (error) {
        console.error('Error cancelando reserva:', error.message);
        res.redirect('/dashboard?error=Error al cancelar reserva');
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
    console.log(`Cliente Web Estudiantes ejecutándose en http://localhost:${PORT}`);
});




