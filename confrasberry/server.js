// /**
//  * Fire Monitor - Node.js Web Server
//  * Servidor web para visualizar imágenes de detección de incendios
//  */

// const express = require('express');
// const mqtt = require('mqtt');
// const path = require('path');
// const fs = require('fs');
// const http = require('http');
// const socketIo = require('socket.io');
// const os = require('os');

// // ============================================
// // CONFIGURACIÓN
// // ============================================

// const PORT = process.env.PORT || 3000;
// const MQTT_BROKER = process.env.MQTT_BROKER || 'mqtt://localhost:1883';

// // Directorios multiplataforma
// const BASE_DIR = path.join(__dirname);
// const PUBLIC_DIR = path.join(BASE_DIR, 'public');
// const IMAGES_DIR = process.platform === 'win32' 
//   ? path.join(os.homedir(), 'fire_monitor', 'images')
//   : '/home/pi/fire_images';

// const LATEST_IMAGE = path.join(PUBLIC_DIR, 'latest.jpg');

// // Topics MQTT
// const TOPIC_ALERT = 'fire/alert';
// const TOPIC_STATUS = 'fire/status';
// const TOPIC_IMAGE_META = 'fire/image/meta';
// const TOPIC_CAPTURE = 'fire/capture';

// // ============================================
// // INICIALIZACIÓN
// // ============================================

// const app = express();
// const server = http.createServer(app);
// const io = socketIo(server);

// // Middleware
// app.use(express.json());
// app.use(express.static(PUBLIC_DIR));

// // Crear directorios necesarios
// [PUBLIC_DIR, IMAGES_DIR].forEach(dir => {
//   if (!fs.existsSync(dir)) {
//     fs.mkdirSync(dir, { recursive: true });
//     console.log(`✓ Directorio creado: ${dir}`);
//   }
// });

// // Middleware para servir imágenes con manejo de errores
// app.use('/images', (req, res, next) => {
//   const filePath = path.join(IMAGES_DIR, req.path);
  
//   if (fs.existsSync(filePath)) {
//     res.sendFile(filePath);
//   } else {
//     res.status(404).json({ error: 'Imagen no encontrada' });
//   }
// });

// // Estado global
// let systemStatus = {
//   esp32Connected: false,
//   lastAlert: null,
//   totalDetections: 0,
//   lastImage: null,
//   esp32IP: null,
//   fireActive: false // Nuevo: indica si hay fuego activo
// };

// // ============================================
// // MQTT CLIENT
// // ============================================

// // Función para obtener fecha/hora en zona horaria de Bogotá
// function getBogotaTime(timestamp) {
//   const date = timestamp ? new Date(timestamp) : new Date();
//   return new Date(date.toLocaleString('en-US', { timeZone: 'America/Bogota' }));
// }

// const mqttClient = mqtt.connect(MQTT_BROKER, {
//   clientId: `NodeJS-WebServer-${Math.random().toString(16).substr(2, 8)}`,
//   clean: true,
//   reconnectPeriod: 5000
// });

// mqttClient.on('connect', () => {
//   console.log('✓ Conectado al broker MQTT');
  
//   const topics = [TOPIC_ALERT, TOPIC_STATUS, TOPIC_IMAGE_META];
  
//   mqttClient.subscribe(topics, (err) => {
//     if (err) {
//       console.error('❌ Error suscribiéndose a topics:', err);
//     } else {
//       console.log('✓ Suscrito a topics MQTT:', topics.join(', '));
//     }
//   });
// });

// mqttClient.on('message', (topic, message) => {
//   try {
//     const data = JSON.parse(message.toString());
    
//     // Alerta de fuego
//     if (topic === TOPIC_ALERT) {
//       const isFireDetected = data.alert === 'FIRE_DETECTED';
//       const bogotaTime = getBogotaTime(data.timestamp);
      
//       systemStatus.lastAlert = {
//         type: data.alert,
//         timestamp: bogotaTime,
//         detections: data.detections || 0
//       };
      
//       if (isFireDetected) {
//         systemStatus.fireActive = true;
//         systemStatus.totalDetections = data.detections || 0;
//         console.log(`🔥 Alerta de fuego recibida (Detecciones: ${data.detections}) - ${bogotaTime.toLocaleString('es-CO')}`);
//       } else {
//         // Marcar como seguro para cualquier alerta que NO sea FIRE_DETECTED
//         systemStatus.fireActive = false;
//         console.log(`✓ Alerta despejada (${data.alert}) - ${bogotaTime.toLocaleString('es-CO')}`);
//       }
      
//       // Emitir a todos los clientes web conectados
//       io.emit('fireAlert', {
//         detected: systemStatus.fireActive,
//         timestamp: bogotaTime.toISOString(),
//         detections: systemStatus.fireActive ? (data.detections || 0) : 0,
//         localTime: bogotaTime.toLocaleString('es-CO', {
//           timeZone: 'America/Bogota',
//           year: 'numeric',
//           month: '2-digit',
//           day: '2-digit',
//           hour: '2-digit',
//           minute: '2-digit',
//           second: '2-digit',
//           hour12: false
//         })
//       });
//     }
    
//     // Estado del dispositivo
//     else if (topic === TOPIC_STATUS) {
//       const isOnline = data.status === 'online';
//       systemStatus.esp32Connected = isOnline;
//       systemStatus.esp32IP = data.ip || null;
      
//       io.emit('deviceStatus', {
//         connected: isOnline,
//         ip: data.ip || 'N/A'
//       });
      
//       const bogotaTime = getBogotaTime();
//       console.log(`${isOnline ? '✓' : '⚠️'} ESP32-CAM ${data.status} ${data.ip ? `(${data.ip})` : ''} - ${bogotaTime.toLocaleString('es-CO')}`);
//     }
    
//     // Metadata de imagen
//     else if (topic === TOPIC_IMAGE_META) {
//       const bogotaTime = getBogotaTime(data.timestamp);
      
//       systemStatus.lastImage = {
//         timestamp: bogotaTime,
//         size: data.size || 0,
//         width: data.width || 0,
//         height: data.height || 0
//       };
      
//       // Notificar que hay nueva imagen disponible
//       const cacheBuster = Date.now();
//       io.emit('newImage', {
//         timestamp: bogotaTime.toISOString(),
//         localTime: bogotaTime.toLocaleString('es-CO', {
//           timeZone: 'America/Bogota',
//           year: 'numeric',
//           month: '2-digit',
//           day: '2-digit',
//           hour: '2-digit',
//           minute: '2-digit',
//           second: '2-digit',
//           hour12: false
//         }),
//         path: `/latest.jpg?t=${cacheBuster}`
//       });
      
//       console.log(`📸 Nueva imagen disponible (${data.width}x${data.height}, ${data.size} bytes) - ${bogotaTime.toLocaleString('es-CO')}`);
//     }
    
//   } catch (err) {
//     console.error('❌ Error procesando mensaje MQTT:', err.message);
//   }
// });

// mqttClient.on('error', (err) => {
//   console.error('❌ Error MQTT:', err.message);
// });

// mqttClient.on('reconnect', () => {
//   console.log('🔄 Reconectando a broker MQTT...');
// });

// // ============================================
// // ENDPOINTS API
// // ============================================

// // Estado del sistema
// app.get('/api/status', (req, res) => {
//   res.json({
//     success: true,
//     data: {
//       ...systemStatus,
//       server: {
//         uptime: process.uptime(),
//         platform: process.platform,
//         nodeVersion: process.version
//       }
//     }
//   });
// });

// // Lista de imágenes guardadas
// app.get('/api/images', (req, res) => {
//   // Verificar que el directorio existe
//   if (!fs.existsSync(IMAGES_DIR)) {
//     return res.json({
//       success: true,
//       data: [],
//       message: 'Directorio de imágenes vacío'
//     });
//   }

//   fs.readdir(IMAGES_DIR, (err, files) => {
//     if (err) {
//       console.error('Error leyendo directorio:', err);
//       return res.status(500).json({
//         success: false,
//         error: 'Error leyendo directorio de imágenes'
//       });
//     }
    
//     const images = files
//       .filter(file => file.toLowerCase().endsWith('.jpg'))
//       .sort((a, b) => {
//         // Ordenar por fecha de modificación (más reciente primero)
//         const statA = fs.statSync(path.join(IMAGES_DIR, a));
//         const statB = fs.statSync(path.join(IMAGES_DIR, b));
//         return statB.mtime - statA.mtime;
//       })
//       .slice(0, 50) // Últimas 50 imágenes
//       .map(file => {
//         const stat = fs.statSync(path.join(IMAGES_DIR, file));
//         return {
//           filename: file,
//           path: `/images/${file}`,
//           timestamp: file.replace('fire_capture_', '').replace('.jpg', ''),
//           size: stat.size,
//           modified: stat.mtime.toISOString()
//         };
//       });
    
//     res.json({
//       success: true,
//       data: images
//     });
//   });
// });

// // Solicitar captura manual
// app.post('/api/capture', (req, res) => {
//   if (!mqttClient.connected) {
//     return res.status(503).json({
//       success: false,
//       error: 'Broker MQTT no conectado'
//     });
//   }

//   mqttClient.publish(TOPIC_CAPTURE, 'CAPTURE', (err) => {
//     if (err) {
//       console.error('Error publicando comando de captura:', err);
//       return res.status(500).json({
//         success: false,
//         error: 'Error enviando comando de captura'
//       });
//     }

//     console.log('📸 Captura manual solicitada');
//     res.json({
//       success: true,
//       message: 'Captura solicitada correctamente'
//     });
//   });
// });

// // Health check
// app.get('/api/health', (req, res) => {
//   res.json({
//     status: 'ok',
//     mqtt: mqttClient.connected,
//     uptime: process.uptime()
//   });
// });

// // ============================================
// // WEBSOCKET
// // ============================================

// io.on('connection', (socket) => {
//   console.log(`🔌 Cliente web conectado (${socket.id})`);
  
//   // Enviar estado inicial
//   socket.emit('initialState', systemStatus);
  
//   socket.on('disconnect', () => {
//     console.log(`🔌 Cliente web desconectado (${socket.id})`);
//   });
  
//   // Manejar solicitud de captura desde web
//   socket.on('requestCapture', () => {
//     if (mqttClient.connected) {
//       mqttClient.publish(TOPIC_CAPTURE, 'CAPTURE');
//       console.log('📸 Captura solicitada desde web');
//       socket.emit('captureRequested', { success: true });
//     } else {
//       socket.emit('captureRequested', { 
//         success: false, 
//         error: 'MQTT no conectado' 
//       });
//     }
//   });
// });

// // ============================================
// // PÁGINA WEB
// // ============================================

// app.get('/', (req, res) => {
//   res.sendFile(path.join(PUBLIC_DIR, 'index.html'));
// });

// // ============================================
// // INICIAR SERVIDOR
// // ============================================

// // Obtener IP local
// function getLocalIP() {
//   const interfaces = os.networkInterfaces();
//   for (const name of Object.keys(interfaces)) {
//     for (const iface of interfaces[name]) {
//       if (iface.family === 'IPv4' && !iface.internal) {
//         return iface.address;
//       }
//     }
//   }
//   return 'localhost';
// }

// server.listen(PORT, () => {
//   const localIP = getLocalIP();
  
//   console.log('='.repeat(50));
//   console.log('🔥 Fire Monitor Web Server');
//   console.log('='.repeat(50));
//   console.log(`✓ Servidor web escuchando en puerto ${PORT}`);
//   console.log(`🌐 Acceso local: http://localhost:${PORT}`);
//   console.log(`🌐 Acceso en red: http://${localIP}:${PORT}`);
//   console.log(`📡 Broker MQTT: ${MQTT_BROKER}`);
//   console.log(`📁 Directorio imágenes: ${IMAGES_DIR}`);
//   console.log('='.repeat(50));
// });

// // Manejo de errores
// process.on('uncaughtException', (err) => {
//   console.error('❌ Error no capturado:', err);
// });

// process.on('unhandledRejection', (reason, promise) => {
//   console.error('❌ Promesa rechazada no manejada:', reason);
// });

// process.on('SIGINT', () => {
//   console.log('\n\n🛑 Cerrando servidor...');
  
//   if (mqttClient.connected) {
//     mqttClient.end(true);
//   }
  
//   server.close(() => {
//     console.log('✓ Servidor cerrado');
//     process.exit(0);
//   });
// });

/**
 * Fire Monitor - Node.js Web Server
 * Servidor web para visualizar imágenes de detección de incendios
 */

const express = require('express');
const mqtt = require('mqtt');
const path = require('path');
const fs = require('fs');
const http = require('http');
const socketIo = require('socket.io');
const os = require('os');

// ============================================
// CONFIGURACIÓN
// ============================================

const PORT = process.env.PORT || 3000;
const MQTT_BROKER = process.env.MQTT_BROKER || 'mqtt://localhost:1883';

// Directorios multiplataforma
const BASE_DIR = path.join(__dirname);
const PUBLIC_DIR = path.join(BASE_DIR, 'public');
const IMAGES_DIR = process.platform === 'win32' 
  ? path.join(os.homedir(), 'fire_monitor', 'images')
  : '/home/pi/fire_images';

const LATEST_IMAGE = path.join(PUBLIC_DIR, 'latest.jpg');

// Topics MQTT
const TOPIC_ALERT = 'fire/alert';
const TOPIC_STATUS = 'fire/status';
const TOPIC_IMAGE_META = 'fire/image/meta';
const TOPIC_CAPTURE = 'fire/capture';

// ============================================
// INICIALIZACIÓN
// ============================================

const app = express();
const server = http.createServer(app);
const io = socketIo(server);

// Middleware
app.use(express.json());
app.use(express.static(PUBLIC_DIR));

// Crear directorios necesarios
[PUBLIC_DIR, IMAGES_DIR].forEach(dir => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
    console.log(`✓ Directorio creado: ${dir}`);
  }
});

// // Middleware para servir imágenes con manejo de errores
app.use('/images', (req, res, next) => {
  const filePath = path.join(IMAGES_DIR, req.path);
  
  if (fs.existsSync(filePath)) {
    res.sendFile(filePath);
  } else {
    res.status(404).json({ error: 'Imagen no encontrada' });
  }
});

// Estado global
let systemStatus = {
  esp32Connected: false,
  lastAlert: null,
  totalDetections: 0,
  lastImage: null,
  esp32IP: null,
  fireActive: false // Nuevo: indica si hay fuego activo
};

// ============================================
// MQTT CLIENT
// ============================================

// Función para obtener fecha/hora en zona horaria de Bogotá
function getBogotaTime(timestamp) {
  const date = timestamp ? new Date(timestamp) : new Date();
  return new Date(date.toLocaleString('en-US', { timeZone: 'America/Bogota' }));
}

const mqttClient = mqtt.connect(MQTT_BROKER, {
  clientId: `NodeJS-WebServer-${Math.random().toString(16).substr(2, 8)}`,
  clean: true,
  reconnectPeriod: 5000
});

mqttClient.on('connect', () => {
  console.log('✓ Conectado al broker MQTT');
  
  const topics = [TOPIC_ALERT, TOPIC_STATUS, TOPIC_IMAGE_META];
  
  mqttClient.subscribe(topics, (err) => {
    if (err) {
      console.error('❌ Error suscribiéndose a topics:', err);
    } else {
      console.log('✓ Suscrito a topics MQTT:', topics.join(', '));
    }
  });
});

mqttClient.on('message', (topic, message) => {
  try {
    const data = JSON.parse(message.toString());
    
    // Alerta de fuego
    if (topic === TOPIC_ALERT) {
      const isFireDetected = data.alert === 'FIRE_DETECTED';
      const bogotaTime = getBogotaTime(data.timestamp);
      
      systemStatus.lastAlert = {
        type: data.alert,
        timestamp: bogotaTime,
        detections: data.detections || 0
      };
      
      if (isFireDetected) {
        systemStatus.fireActive = true;
        systemStatus.totalDetections = data.detections || 0;
        console.log(`🔥 Alerta de fuego recibida (Detecciones: ${data.detections}) - ${bogotaTime.toLocaleString('es-CO')}`);
      } 
      
      // Emitir a todos los clientes web conectados
      io.emit('fireAlert', {
        detected: systemStatus.fireActive,
        timestamp: bogotaTime.toISOString(),
        detections: systemStatus.fireActive ? (data.detections || 0) : 0,
        localTime: bogotaTime.toLocaleString('es-CO', {
          timeZone: 'America/Bogota',
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: false
        })
      });
    }
    
    // Estado del dispositivo
    else if (topic === TOPIC_STATUS) {
      const isOnline = data.status === 'online';
      systemStatus.esp32Connected = isOnline;
      systemStatus.esp32IP = data.ip || null;
      
      io.emit('deviceStatus', {
        connected: isOnline,
        ip: data.ip || 'N/A'
      });
      
      const bogotaTime = getBogotaTime();
      console.log(`${isOnline ? '✓' : '⚠️'} ESP32-CAM ${data.status} ${data.ip ? `(${data.ip})` : ''} - ${bogotaTime.toLocaleString('es-CO')}`);
    }
    
    // Metadata de imagen
    else if (topic === TOPIC_IMAGE_META) {
      const bogotaTime = getBogotaTime(data.timestamp);
      
      systemStatus.lastImage = {
        timestamp: bogotaTime,
        size: data.size || 0,
        width: data.width || 0,
        height: data.height || 0
      };
      
      // Notificar que hay nueva imagen disponible
      const cacheBuster = Date.now();
      io.emit('newImage', {
        timestamp: bogotaTime.toISOString(),
        localTime: bogotaTime.toLocaleString('es-CO', {
          timeZone: 'America/Bogota',
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: false
        }),
        path: `/latest.jpg?t=${cacheBuster}`
      });
      
      console.log(`📸 Nueva imagen disponible (${data.width}x${data.height}, ${data.size} bytes) - ${bogotaTime.toLocaleString('es-CO')}`);
    }
    
  } catch (err) {
    console.error('❌ Error procesando mensaje MQTT:', err.message);
  }
});

mqttClient.on('error', (err) => {
  console.error('❌ Error MQTT:', err.message);
});

mqttClient.on('reconnect', () => {
  console.log('🔄 Reconectando a broker MQTT...');
});

// ============================================
// ENDPOINTS API
// ============================================

// Estado del sistema
app.get('/api/status', (req, res) => {
  res.json({
    success: true,
    data: {
      ...systemStatus,
      server: {
        uptime: process.uptime(),
        platform: process.platform,
        nodeVersion: process.version
      }
    }
  });
});

// Lista de imágenes guardadas
app.get('/api/images', (req, res) => {
  // Verificar que el directorio existe
  if (!fs.existsSync(IMAGES_DIR)) {
    return res.json({
      success: true,
      data: [],
      message: 'Directorio de imágenes vacío'
    });
  }

  fs.readdir(IMAGES_DIR, (err, files) => {
    if (err) {
      console.error('Error leyendo directorio:', err);
      return res.status(500).json({
        success: false,
        error: 'Error leyendo directorio de imágenes'
      });
    }
    
    const images = files
      .filter(file => file.toLowerCase().endsWith('.jpg'))
      .sort((a, b) => {
        // Ordenar por fecha de modificación (más reciente primero)
        const statA = fs.statSync(path.join(IMAGES_DIR, a));
        const statB = fs.statSync(path.join(IMAGES_DIR, b));
        return statB.mtime - statA.mtime;
      })
      .slice(0, 50) // Últimas 50 imágenes
      .map(file => {
        const stat = fs.statSync(path.join(IMAGES_DIR, file));
        return {
          filename: file,
          path: `/images/${file}`,
          timestamp: file.replace('fire_capture_', '').replace('.jpg', ''),
          size: stat.size,
          modified: stat.mtime.toISOString()
        };
      });
    
    res.json({
      success: true,
      data: images
    });
  });
});

// Solicitar captura manual
app.post('/api/capture', (req, res) => {
  if (!mqttClient.connected) {
    return res.status(503).json({
      success: false,
      error: 'Broker MQTT no conectado'
    });
  }

  mqttClient.publish(TOPIC_CAPTURE, 'CAPTURE', (err) => {
    if (err) {
      console.error('Error publicando comando de captura:', err);
      return res.status(500).json({
        success: false,
        error: 'Error enviando comando de captura'
      });
    }

    console.log('📸 Captura manual solicitada');
    res.json({
      success: true,
      message: 'Captura solicitada correctamente'
    });
  });
});

// Health check
app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    mqtt: mqttClient.connected,
    uptime: process.uptime()
  });
});

// Obtener estadísticas de los últimos 7 días
app.get('/api/statistics', (req, res) => {
  try {
    const db = require('better-sqlite3')('/home/pi/fire_monitor/fire_monitor.db');
    const stmt = db.prepare(`
      SELECT 
        date,
        total_detections,
        total_alerts,
        images_captured
      FROM daily_statistics
      WHERE date >= date('now', '-7 days')
      ORDER BY date ASC
    `);
    const statistics = stmt.all();
    
    res.json({
      success: true,
      data: statistics
    });
  } catch (error) {
    console.error('Error obteniendo estadísticas:', error);
    res.status(500).json({
      success: false,
      error: 'Error obteniendo estadísticas'
    });
  }
});

// Obtener alertas con información de imágenes
app.get('/api/alerts', (req, res) => {
  try {
    const db = require('better-sqlite3')('/home/pi/fire_monitor/fire_monitor.db');
    const stmt = db.prepare(`
      SELECT 
        a.id,
        a.alert_type,
        a.severity,
        a.status,
        a.detections_count,
        a.created_at,
        a.resolved_at,
        a.duration_seconds,
        COUNT(ci.id) as images_count,
        GROUP_CONCAT(ci.file_name) as image_files
      FROM alerts a
      LEFT JOIN captured_images ci ON a.id = ci.alert_id
      GROUP BY a.id
      ORDER BY a.created_at DESC
      LIMIT 50
    `);
    const alerts = stmt.all();
    
    res.json({
      success: true,
      data: alerts
    });
  } catch (error) {
    console.error('Error obteniendo alertas:', error);
    res.status(500).json({
      success: false,
      error: 'Error obteniendo alertas'
    });
  }
});

// ============================================
// WEBSOCKET
// ============================================

io.on('connection', (socket) => {
    console.log(`🔌 Cliente web conectado (${socket.id})`);
    socket.emit('initialState', systemStatus);

    // Escuchar evento de resolución manual
    socket.on('resolveAlert', () => {
        try {
            const db = require('better-sqlite3')('/home/pi/fire_monitor/fire_monitor.db');
            // Buscar la alerta activa
            const activeAlert = db.prepare("SELECT id FROM alerts WHERE status = 'ACTIVE' ORDER BY created_at DESC LIMIT 1").get();
            if (activeAlert && activeAlert.id) {
                db.prepare("UPDATE alerts SET status = 'RESOLVED', resolved_at = CURRENT_TIMESTAMP WHERE id = ?").run(activeAlert.id);
                systemStatus.fireActive = false;
                console.log(`✓ Alerta resuelta manualmente (ID: ${activeAlert.id})`);
                // Notificar a todos los clientes que la alerta fue resuelta
                io.emit('fireAlert', {
                    detected: false,
                    timestamp: new Date().toISOString(),
                    detections: 0
                });
            }
        } catch (err) {
            console.error('Error resolviendo alerta:', err.message);
        }
    });

    socket.on('disconnect', () => { /* ... */ });
});

// ============================================
// PÁGINA WEB
// ============================================

app.get('/', (req, res) => {
  res.sendFile(path.join(PUBLIC_DIR, 'index.html'));
});

// ============================================
// INICIAR SERVIDOR
// ============================================

// Obtener IP local
function getLocalIP() {
  const interfaces = os.networkInterfaces();
  for (const name of Object.keys(interfaces)) {
    for (const iface of interfaces[name]) {
      if (iface.family === 'IPv4' && !iface.internal) {
        return iface.address;
      }
    }
  }
  return 'localhost';
}

server.listen(PORT, () => {
  const localIP = getLocalIP();
  
  console.log('='.repeat(50));
  console.log('🔥 Fire Monitor Web Server');
  console.log('='.repeat(50));
  console.log(`✓ Servidor web escuchando en puerto ${PORT}`);
  console.log(`🌐 Acceso local: http://localhost:${PORT}`);
  console.log(`🌐 Acceso en red: http://${localIP}:${PORT}`);
  console.log(`📡 Broker MQTT: ${MQTT_BROKER}`);
  console.log(`📁 Directorio imágenes: ${IMAGES_DIR}`);
  console.log('='.repeat(50));
});

// Manejo de errores
process.on('uncaughtException', (err) => {
  console.error('❌ Error no capturado:', err);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('❌ Promesa rechazada no manejada:', reason);
});

process.on('SIGINT', () => {
  console.log('\n\n🛑 Cerrando servidor...');
  
  if (mqttClient.connected) {
    mqttClient.end(true);
  }
  
  server.close(() => {
    console.log('✓ Servidor cerrado');
    process.exit(0);
  });
});