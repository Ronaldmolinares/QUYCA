# 🔥 Fire Monitor - Resumen de Configuración del Sistema

## 📊 Clasificación de Severidad de Alertas

### Criterios de Clasificación

La severidad se determina según el **número acumulado de detecciones** desde que inició el ESP32:

```python
# Ubicación: fire_monitor.py, línea 180
severity = 'HIGH' if detections > 5 else 'MEDIUM' if detections > 2 else 'LOW'
```

| Nivel | Detecciones | Emoji | Descripción |
|-------|-------------|-------|-------------|
| **LOW** 🟡 | 1-2 | 🟡 | Detección inicial o aislada |
| **MEDIUM** 🟠 | 3-5 | 🟠 | Múltiples detecciones, riesgo moderado |
| **HIGH** 🔴 | >5 | 🔴 | Detecciones persistentes, riesgo alto |

### Ejemplo de Evolución de Alertas

```
Detección #1  → Alerta #1: LOW    🟡
Detección #2  → Alerta #2: LOW    🟡
Detección #3  → Alerta #3: MEDIUM 🟠
Detección #4  → Alerta #4: MEDIUM 🟠
Detección #5  → Alerta #5: MEDIUM 🟠
Detección #6  → Alerta #6: HIGH   🔴
Detección #7+ → Alerta #N: HIGH   🔴
```

---

## ⏱️ Tiempos de Sensado (ESP32)

### Intervalos de Lectura

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| **SENSOR_INTERVAL** | 250ms | Frecuencia de lectura del sensor KY-026 |
| **MQTT_PUBLISH_INTERVAL** | 1000ms (1s) | Intervalo de publicación MQTT |
| **FRAME_DELAY** | 100ms | Delay entre frames de captura de imagen |

```cpp
// Ubicación: src/main.cpp, líneas 72-73
const unsigned long SENSOR_INTERVAL = 250;        // Lee sensor cada 250ms
const unsigned long MQTT_PUBLISH_INTERVAL = 1000; // Publica cada 1 segundo
```

### Comportamiento del Sensor

1. **Lee sensor cada 250ms** (4 veces por segundo)
2. **Detecta fuego** → Incrementa contador `flameCounter`
3. **Publica alerta MQTT** solo cuando:
   - Detecta fuego y no había alerta activa
   - Deja de detectar fuego y había alerta activa

### Historial de Detecciones

```cpp
const int HISTORY_SIZE = 50;  // Guarda últimas 50 lecturas
```

Mantiene un buffer circular con las últimas 50 lecturas del sensor.

---

## 📡 Configuración MQTT

### Broker y Topics

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| **MQTT_BROKER** | localhost | Broker MQTT (Raspberry Pi) |
| **MQTT_PORT** | 1883 | Puerto estándar MQTT |
| **QoS** | 0 | Quality of Service (Fire & Forget) |

### Topics MQTT

```python
TOPIC_ALERT = "fire/alert"           # Alertas de fuego
TOPIC_CAPTURE_CMD = "fire/capture"   # Comando para capturar imagen
TOPIC_IMAGE = "fire/image"           # Chunks de imagen
TOPIC_IMAGE_META = "fire/image/meta" # Metadata de imagen
TOPIC_STATUS = "fire/status"         # Estado del dispositivo
```

---

## 📸 Captura y Transmisión de Imágenes

### Resoluciones Disponibles

```cpp
// ESP32-CAM soporta múltiples resoluciones
// Configuración actual: 320x240 (QVGA) o 800x600 (SVGA)
```

### Proceso de Transmisión

1. **Captura** → ESP32-CAM toma foto
2. **Codificación** → Convierte a Base64
3. **Fragmentación** → Divide en chunks de ~4000 caracteres
4. **Transmisión** → Envía chunks vía MQTT
5. **Reconstrucción** → Raspberry Pi une chunks
6. **Almacenamiento** → Guarda en `/home/pi/fire_images/`
7. **Notificación** → Envía a Telegram

### Tamaños Típicos

| Resolución | Tamaño Típico | Chunks |
|------------|---------------|--------|
| 320x240 | 3-15 KB | 2-5 |
| 800x600 | 20-30 KB | 7-10 |

---

## 📱 Configuración de Telegram

### Tiempos de Notificación

```python
# Ubicación: telegram_config.py
ALERT_COOLDOWN = 10  # Segundos entre notificaciones de texto
```

| Tipo de Notificación | Cooldown | Descripción |
|---------------------|----------|-------------|
| **Alerta de Texto** | 10 segundos | Notificación "🔥 ALERTA DE INCENDIO" |
| **Envío de Imagen** | Sin cooldown | Todas las imágenes se envían |
| **Despeje** | Sin cooldown | Notificación "✅ Alerta despejada" |

### Opciones Configurables

```python
TELEGRAM_ENABLED = True   # Activar/desactivar notificaciones
SEND_IMAGES = True        # Enviar imágenes capturadas
ALERT_COOLDOWN = 10       # Segundos entre alertas
```

---

## 🗄️ Almacenamiento de Datos

### Directorios

```python
IMAGES_DIR = "/home/pi/fire_images"                  # Imágenes capturadas
LATEST_IMAGE_PATH = "/home/pi/fire_monitor/public/latest.jpg"
DB_PATH = "/home/pi/fire_monitor/fire_monitor.db"   # Base de datos SQLite
```

### Base de Datos

| Tabla | Descripción | Retención |
|-------|-------------|-----------|
| **fire_detections** | Cada lectura del sensor | Ilimitada |
| **alerts** | Alertas agrupadas | Ilimitada |
| **captured_images** | Registro de imágenes | Ilimitada |
| **device_status** | Estado de dispositivos | Última actualización |
| **system_logs** | Logs del sistema | Ilimitada |
| **daily_statistics** | Estadísticas diarias | Ilimitada |

---

## 🔄 Flujo Completo de Detección

```
┌─────────────────────────────────────────────────────────────────┐
│                         ESP32-CAM                               │
└─────────────────────────────────────────────────────────────────┘
  │
  │ Lee sensor cada 250ms
  ├──► Fuego detectado → Incrementa contador
  │
  │ Publica MQTT cada 1s (si hay cambio)
  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MQTT Broker (Raspberry Pi)                 │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    fire_monitor.py (Python)                     │
└─────────────────────────────────────────────────────────────────┘
  │
  ├──► Recibe alerta → Clasifica severidad (LOW/MEDIUM/HIGH)
  │
  ├──► Guarda en base de datos
  │
  ├──► Envía notificación Telegram (con cooldown de 10s)
  │
  ├──► Solicita captura de imagen
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Telegram Bot                            │
└─────────────────────────────────────────────────────────────────┘
  │
  ├──► Usuario recibe alerta de texto
  │
  └──► Usuario recibe imagen (sin cooldown)
```

---

## ⚡ Tiempos de Respuesta

### Desde Detección hasta Notificación

| Etapa | Tiempo | Acumulado |
|-------|--------|-----------|
| **Sensor detecta fuego** | 0ms | 0ms |
| **ESP32 procesa** | ~50ms | ~50ms |
| **Publica MQTT** | ~100ms | ~150ms |
| **Raspberry recibe** | ~50ms | ~200ms |
| **Clasifica y guarda en BD** | ~50ms | ~250ms |
| **Envía a Telegram** | ~500-1000ms | ~750-1250ms |
| **Usuario recibe notificación** | ~500ms | **~1-2 segundos** |

### Captura y Envío de Imagen

| Etapa | Tiempo | Acumulado |
|-------|--------|-----------|
| **Solicitud de captura** | 0ms | 0ms |
| **ESP32 captura foto** | ~500ms | ~500ms |
| **Codifica Base64** | ~200ms | ~700ms |
| **Envía chunks MQTT** | ~1-3s | ~2-4s |
| **Raspberry reconstruye** | ~200ms | ~2.5-4.5s |
| **Envía a Telegram** | ~1-2s | **~4-7 segundos** |

---

## 🎛️ Configuraciones Recomendadas

### Para Máxima Velocidad

```python
# telegram_config.py
ALERT_COOLDOWN = 5  # 5 segundos
SEND_IMAGES = True
```

```cpp
// src/main.cpp
const unsigned long SENSOR_INTERVAL = 200;        // Lee cada 200ms
const unsigned long MQTT_PUBLISH_INTERVAL = 500;  // Publica cada 500ms
```

### Para Reducir Spam

```python
# telegram_config.py
ALERT_COOLDOWN = 30  # 30 segundos
SEND_IMAGES = False   # Solo texto
```

### Para Balance (Actual)

```python
# telegram_config.py
ALERT_COOLDOWN = 10  # 10 segundos ✅
SEND_IMAGES = True   # Envía imágenes ✅
```

```cpp
// src/main.cpp
const unsigned long SENSOR_INTERVAL = 250;        // 250ms ✅
const unsigned long MQTT_PUBLISH_INTERVAL = 1000; // 1 segundo ✅
```

---

## 📈 Mejoras Sugeridas

### Corto Plazo

1. **Severidad dinámica**: Basada en tiempo de persistencia del fuego
2. **Cooldown inteligente**: Más corto para HIGH, más largo para LOW
3. **Compresión de imágenes**: Reducir tamaño de transmisión

### Mediano Plazo

1. **Machine Learning**: Detección más precisa con CNN
2. **Múltiples sensores**: Temperatura, humo, gas
3. **Geolocalización**: GPS para localizar alertas

### Largo Plazo

1. **Red de sensores**: Múltiples ESP32 coordinados
2. **Dashboard web**: Monitoreo en tiempo real
3. **Integración con bomberos**: Alertas automáticas

---

## 🔧 Comandos Útiles

### Modificar Cooldown

```bash
# Editar configuración
nano /home/pi/fire_monitor/telegram_config.py

# Cambiar línea:
ALERT_COOLDOWN = 10  # Ajustar según necesidad

# Reiniciar sistema
sudo systemctl restart fire_monitor
```

### Verificar Base de Datos

```bash
# Conectar a SQLite
sqlite3 /home/pi/fire_monitor/fire_monitor.db

# Ver estadísticas
SELECT COUNT(*) FROM fire_detections;
SELECT severity, COUNT(*) FROM alerts GROUP BY severity;
```

### Monitorear Logs

```bash
# Ver logs en tiempo real
tail -f /home/pi/fire_monitor/logs/fire_monitor.log

# Ver últimas alertas
tail -n 50 /home/pi/fire_monitor/logs/fire_monitor.log | grep "ALERTA"
```

---

## 📊 Resumen de Parámetros Clave

| Parámetro | Valor Actual | Ubicación | Ajustable |
|-----------|--------------|-----------|-----------|
| **Lectura sensor** | 250ms | ESP32 main.cpp | ✅ |
| **Publicación MQTT** | 1s | ESP32 main.cpp | ✅ |
| **Cooldown alertas** | 10s | telegram_config.py | ✅ |
| **Envío de imágenes** | Sin cooldown | fire_monitor.py | ❌ |
| **Severidad LOW** | 1-2 detecciones | fire_monitor.py | ✅ |
| **Severidad MEDIUM** | 3-5 detecciones | fire_monitor.py | ✅ |
| **Severidad HIGH** | >5 detecciones | fire_monitor.py | ✅ |
| **Historial sensor** | 50 lecturas | ESP32 main.cpp | ✅ |
| **Chunk size** | ~4000 chars | ESP32 main.cpp | ✅ |

---

## ✅ Estado Actual del Sistema

- ✅ **Sensor**: Lectura cada 250ms
- ✅ **MQTT**: Publicación cada 1s
- ✅ **Severidad**: Clasificación automática
- ✅ **Telegram**: Cooldown 10s para texto, sin cooldown para imágenes
- ✅ **Base de datos**: Registro completo de eventos
- ✅ **Imágenes**: Captura y transmisión automática

---

**📅 Última actualización:** 2025-10-31  
**🔥 Fire Monitor System - QUYCA Project**
