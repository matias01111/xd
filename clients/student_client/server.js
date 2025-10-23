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
app.use(express.urlencoded({ extended: true }));
app.use(express.json());
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
        console.log('Obteniendo reservas para usuario ID:', req.user.id);
        const bookingsResponse = await axios.get(`${SERVICES.book}/bookings/user/${req.user.id}`);
        const bookings = bookingsResponse.data;
        console.log('Reservas obtenidas:', bookings.length, 'reservas');
        
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
        user: req.user,
        searchParams: null,
        results: null,
        error: null
    });
});

app.post('/disponibilidad', requireAuth, async (req, res) => {
    try {
        const { fecha, hora, duracion, tipo_espacio } = req.body;
        
        // Construir fecha_inicio y fecha_fin
        const fecha_inicio = `${fecha}T${hora}:00`;
        const fecha_inicio_dt = new Date(fecha_inicio);
        const fecha_fin_dt = new Date(fecha_inicio_dt.getTime() + (parseInt(duracion) * 60 * 60 * 1000));
        const fecha_fin = fecha_fin_dt.toISOString();
        
        const response = await axios.post(`${SERVICES.avail}/availability/spaces`, {
            tipo: tipo_espacio || null,
            fecha_inicio: fecha_inicio,
            fecha_fin: fecha_fin
        });
        
        res.render('disponibilidad', {
            title: 'Consultar Disponibilidad',
            user: req.user,
            results: response.data,
            searchParams: req.body,
            error: null
        });
    } catch (error) {
        console.error('Error consultando disponibilidad:', error.message);
        console.error('Error details:', error.response?.data);
        res.render('disponibilidad', {
            title: 'Consultar Disponibilidad',
            user: req.user,
            error: 'Error consultando disponibilidad',
            searchParams: req.body,
            results: null
        });
    }
});

app.post('/reservar', requireAuth, async (req, res) => {
  try {
    // 1) user y token desde la sesión
    const user = req.session?.user;
    const token = req.session?.token;

    if (!user || !token) {
      console.error('[RESERVAR] No hay sesión/tokén');
      return res.redirect('/login');
    }

    const { id_espacio, space_id, fecha_inicio, inicio, fecha_fin, fin, motivo } = req.body;

    const bookingData = {
      id_usuario: Number(user.id),
      id_espacio: Number(id_espacio ?? space_id),
      fecha_inicio: (fecha_inicio ?? inicio),
      fecha_fin: (fecha_fin ?? fin),
      motivo: motivo || null
    };

    if (!bookingData.id_espacio || !bookingData.fecha_inicio || !bookingData.fecha_fin) {
      console.error('[RESERVAR] payload incompleto:', bookingData);
      return res.render('disponibilidad', {
        title: 'Consultar Disponibilidad',
        results: req.session.lastResults || [],
        searchParams: req.session.lastSearch || {},
        error: 'Faltan datos para reservar (espacio/fechas).'
      });
    }

    console.log('[RESERVAR] → 5005/bookings/create', bookingData);

    const response = await axios.post(`${SERVICES.book}/bookings/create`, bookingData, {
      headers: { Authorization: `Bearer ${token}` }
    });

    console.log('[RESERVAR] ←', response.status, response.data);

    return res.redirect('/panel');
  } catch (err) {
    const msg = err?.response?.data?.error || err?.response?.data || err.message;
    console.error('[RESERVAR] error:', msg);
    return res.render('disponibilidad', {
      title: 'Consultar Disponibilidad',
      results: req.session.lastResults || [],
      searchParams: req.session.lastSearch || {},
      error: `No se pudo crear la reserva: ${msg}`
    });
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




