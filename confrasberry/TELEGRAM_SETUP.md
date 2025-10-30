# 📱 Notificaciones de Telegram - Resumen de Implementación

## ✅ Archivos Creados/Modificados

### 📄 Nuevos Archivos

1. **`telegram_config.py`** - Configuración de credenciales (EDITARLO)
2. **`telegram_notifier.py`** - Módulo principal de notificaciones
3. **`test_telegram.py`** - Script de prueba
4. **`setup_telegram.py`** - Configuración interactiva
5. **`telegram_config.py.example`** - Ejemplo de configuración
6. **`requirements.txt`** - Dependencias de Python
7. **`TELEGRAM_README.md`** - Documentación completa

### 🔧 Archivos Modificados

1. **`fire_monitor.py`** - Integración con Telegram
2. **`database.py`** - Agregado método `get_alert_by_id()`
3. **`.gitignore`** - Protección de credenciales

---

## 🚀 Guía de Inicio Rápido

### Opción 1: Setup Automático (Recomendado)

```bash
# 1. Ejecutar script de configuración
python setup_telegram.py

# El script te guiará paso a paso:
# - Instalará dependencias
# - Te pedirá token y chat ID
# - Probará la configuración
# - ¡Listo!
```

### Opción 2: Setup Manual

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Copiar y editar configuración
cp telegram_config.py.example telegram_config.py
# Editar telegram_config.py con tus credenciales

# 3. Probar
python test_telegram.py
```

---

## 📱 Cómo Obtener Credenciales

### 🤖 Token del Bot

1. Abre Telegram
2. Busca **@BotFather**
3. Envía `/newbot`
4. Sigue instrucciones:
   - Nombre: "Fire Alert Bot" (o el que quieras)
   - Username: "my_fire_alert_bot" (debe terminar en "bot")
5. **Copia el TOKEN** que te da

Ejemplo de token:
```
123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
```

### 💬 Chat ID

1. Busca **@userinfobot** en Telegram
2. Envía `/start`
3. **Copia el ID** que te da

Ejemplo de Chat ID:
```
987654321
```

Para grupos (opcional):
- Agrega el bot al grupo
- Hazlo admin
- El Chat ID será negativo: `-987654321`

---

## 🎯 Características Implementadas

### ✅ Lo que hace automáticamente:

1. **🔥 Alerta de Incendio**
   - Se envía cuando se detecta fuego por primera vez
   - Incluye: severidad, número de detecciones, timestamp
   - Opcionalmente envía la imagen capturada

2. **✅ Despeje de Alerta**
   - Se envía cuando la situación se normaliza
   - Muestra duración de la alerta

3. **🟢 Estado del Sistema**
   - Al iniciar: notifica que el sistema está online
   - Al detener: muestra estadísticas de la sesión

4. **📸 Imágenes**
   - Envía fotos capturadas junto con alertas
   - Calidad completa de la cámara ESP32-CAM

5. **⏱️ Control de Spam**
   - Cooldown de 5 minutos entre alertas (configurable)
   - Evita inundar tu Telegram con notificaciones

---

## 📊 Ejemplo de Notificaciones

### Alerta de Incendio
```
🔥 ¡ALERTA DE INCENDIO DETECTADO!

🔴 Severidad: HIGH
📊 Detecciones: 7
🕐 Fecha/Hora: 2025-10-29 14:35:22

⚠️ Verificar situación inmediatamente
```
*[Incluye imagen capturada]*

### Despeje
```
✅ Alerta despejada - Situación normalizada

⏱ Duración: 5m 23s

✓ Situación normalizada
```

### Sistema Iniciado
```
🟢 Sistema de monitoreo iniciado

Broker: localhost:1883
```

---

## ⚙️ Configuración Personalizada

### En `telegram_config.py`:

```python
# Activar/desactivar
TELEGRAM_ENABLED = True

# Enviar imágenes (consume más datos)
SEND_IMAGES = True

# Cooldown entre alertas (segundos)
ALERT_COOLDOWN = 300  # 5 minutos

# Personalizar mensajes
MESSAGES = {
    'fire_detected': '🚨 ¡INCENDIO! 🚨',
    'fire_cleared': '✓ Todo OK',
    # ...
}
```

---

## 🔐 Seguridad

### ⚠️ IMPORTANTE

- ✅ `telegram_config.py` está en `.gitignore`
- ✅ NO subas tus credenciales a GitHub
- ✅ Usa el archivo `.example` para compartir

### Si accidentalmente subes el token:

1. Ve a @BotFather
2. Envía `/revoke` para revocar el token
3. Genera uno nuevo con `/token`

---

## 🧪 Testing

### Test básico
```bash
python test_telegram.py
```

### Test desde Python
```python
from telegram_notifier import TelegramNotifier

notifier = TelegramNotifier()

# Enviar mensaje simple
notifier.send_message("Hola!")

# Enviar alerta
from datetime import datetime
notifier.send_fire_alert(
    detections=5,
    timestamp=datetime.now(),
    severity='HIGH'
)
```

---

## 🐛 Problemas Comunes

### ❌ "Bot token not found"
→ Verifica `telegram_config.py`, debe tener tu token

### ❌ "Chat not found"
→ Envía `/start` a tu bot primero

### ❌ "Telegram deshabilitado"
→ Cambia `TELEGRAM_ENABLED = True` en config

### ❌ No recibo mensajes
→ Ejecuta `python test_telegram.py` y revisa errores

---

## 📈 Mejoras Futuras (Opcional)

- [ ] Comandos interactivos (/status, /capture)
- [ ] Múltiples destinatarios
- [ ] Notificaciones por email
- [ ] Integración con Discord/Slack
- [ ] Dashboard web con WebSocket

---

## 🎓 Documentación Adicional

- **Completa**: `TELEGRAM_README.md`
- **API Telegram**: https://core.telegram.org/bots/api
- **Troubleshooting**: Ver sección en README

---

## ✅ Checklist de Implementación

Verifica que todo esté listo:

- [ ] ✅ Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] ✅ Bot creado en @BotFather
- [ ] ✅ Token obtenido
- [ ] ✅ Chat ID obtenido
- [ ] ✅ `telegram_config.py` editado
- [ ] ✅ Test ejecutado (`python test_telegram.py`)
- [ ] ✅ Mensaje de prueba recibido en Telegram
- [ ] ✅ Sistema principal funcionando (`python fire_monitor.py`)

---

## 🎉 ¡Todo Listo!

Tu sistema Fire Monitor ahora enviará notificaciones automáticas a Telegram cada vez que:

- 🔥 Se detecte un incendio
- ✅ La situación se normalice
- 🟢 El sistema se inicie/detenga
- 📸 Se capture una imagen

**¡Protección 24/7 con alertas instantáneas!**

---

*Fire Monitor - Sistema de detección de incendios con ESP32-CAM + Raspberry Pi*
