# 🔥 Notificaciones de Telegram - Fire Monitor

## 📋 Descripción

Sistema de notificaciones en tiempo real via Telegram para alertas de incendios detectados por el sistema ESP32-CAM.

## 🚀 Características

✅ **Notificaciones instantáneas** cuando se detecta fuego
✅ **Envío de imágenes** capturadas por la cámara
✅ **Alertas de despeje** cuando la situación se normaliza
✅ **Niveles de severidad** (LOW, MEDIUM, HIGH)
✅ **Control de spam** (cooldown entre alertas)
✅ **Reportes diarios** de estadísticas
✅ **Notificaciones de estado** del sistema

---

## 🛠️ Instalación

### 1. Instalar dependencias de Python

```bash
pip install -r requirements.txt
```

O instalar manualmente:
```bash
pip install paho-mqtt Pillow requests
```

### 2. Crear un Bot de Telegram

1. Abre Telegram y busca **@BotFather**
2. Envía el comando `/newbot`
3. Sigue las instrucciones:
   - Elige un nombre para tu bot (ej: "Fire Alert Bot")
   - Elige un username que termine en "bot" (ej: "my_fire_alert_bot")
4. **Guarda el TOKEN** que te proporciona BotFather
   - Se verá algo como: `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`

### 3. Obtener tu Chat ID

**Opción A: Usando @userinfobot**
1. Busca **@userinfobot** en Telegram
2. Envíale `/start`
3. Te responderá con tu Chat ID (un número)

**Opción B: Manualmente**
1. Envía un mensaje a tu bot
2. Abre en el navegador: `https://api.telegram.org/bot<TU_TOKEN>/getUpdates`
3. Busca `"chat":{"id":` en la respuesta

### 4. Configurar credenciales

Edita el archivo `telegram_config.py`:

```python
# Token del bot (obtenido de @BotFather)
TELEGRAM_BOT_TOKEN = "123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ"

# Chat ID del destinatario
TELEGRAM_CHAT_ID = "987654321"

# Activar notificaciones
TELEGRAM_ENABLED = True
```

---

## ✅ Probar la configuración

Ejecuta el script de prueba:

```bash
python test_telegram.py
```

Deberías recibir mensajes de prueba en tu Telegram. Si no funciona, verifica:
- ✓ Token correcto (sin espacios extras)
- ✓ Chat ID correcto
- ✓ Bot iniciado (envíale /start)
- ✓ Conexión a internet

---

## 📱 Tipos de Notificaciones

### 🔥 Alerta de Incendio

Se envía cuando se detecta fuego por primera vez:

```
🔥 ¡ALERTA DE INCENDIO DETECTADO!

🔴 Severidad: HIGH
📊 Detecciones: 7
🕐 Fecha/Hora: 2025-10-29 14:35:22

⚠️ Verificar situación inmediatamente
```

Opcionalmente incluye la imagen capturada.

### ✅ Despeje de Alerta

Se envía cuando la situación se normaliza:

```
✅ Alerta despejada

⏱ Duración: 5m 23s

✓ Situación normalizada
```

### 🟢 Estado del Sistema

Al iniciar el sistema:

```
🟢 Sistema de monitoreo iniciado

Broker: localhost:1883
```

Al detener:

```
🔴 Sistema de monitoreo desconectado

Detecciones: 12 | Alertas: 3
```

### 📊 Reporte Diario

Estadísticas del día:

```
📊 Reporte Diario - Fire Monitor

🔥 Detecciones: 15
⚠️ Alertas: 4
📸 Imágenes: 6
🕐 Fecha: 2025-10-29

✓ Sistema operativo
```

---

## ⚙️ Configuración Avanzada

### Ajustar cooldown (evitar spam)

En `telegram_config.py`:

```python
# Segundos mínimos entre alertas (5 minutos por defecto)
ALERT_COOLDOWN = 300
```

### Deshabilitar envío de imágenes

Si solo quieres notificaciones de texto:

```python
SEND_IMAGES = False
```

### Personalizar mensajes

Edita los mensajes en `telegram_config.py`:

```python
MESSAGES = {
    'fire_detected': '🚨 ¡FUEGO DETECTADO! 🚨',
    'fire_cleared': '✓ Todo bajo control',
    # ... etc
}
```

### Enviar a múltiples destinatarios

Para enviar a un grupo:
1. Agrega el bot al grupo
2. Hazlo administrador (si es grupo privado)
3. Usa el Chat ID del grupo (será negativo, ej: `-987654321`)

---

## 🔧 Uso Programático

### Enviar notificación personalizada

```python
from telegram_notifier import TelegramNotifier

notifier = TelegramNotifier()

# Mensaje simple
notifier.send_message("Hola desde Fire Monitor!")

# Con formato HTML
notifier.send_message("<b>Alerta</b>: <i>Temperatura alta</i>", parse_mode='HTML')

# Enviar foto
notifier.send_photo(
    image_path="/ruta/a/imagen.jpg",
    caption="Foto de evidencia"
)
```

### Verificar si se puede enviar alerta

```python
if notifier.can_send_alert():
    notifier.send_fire_alert(...)
else:
    print("Cooldown activo, esperando...")
```

---

## 🐛 Solución de Problemas

### Error: "Bot token not found"
- Verifica que `TELEGRAM_BOT_TOKEN` esté configurado correctamente
- No debe tener espacios ni comillas extras

### Error: "Chat not found"
- Asegúrate de haber enviado `/start` a tu bot primero
- Verifica que el Chat ID sea correcto

### Error: "Forbidden: bot was blocked by the user"
- Desbloquea el bot en Telegram
- Envíale `/start` de nuevo

### No recibo notificaciones
1. Verifica que `TELEGRAM_ENABLED = True`
2. Ejecuta `python test_telegram.py`
3. Revisa los logs en consola
4. Verifica tu conexión a internet

### Las imágenes no se envían
- Verifica que `SEND_IMAGES = True`
- Comprueba que las rutas de imágenes existan
- Las imágenes muy grandes pueden tardar en enviarse

---

## 📊 Estadísticas de Uso

El sistema registra:
- ✓ Número de notificaciones enviadas
- ✓ Tasa de éxito/fallo
- ✓ Tiempo de respuesta
- ✓ Alertas bloqueadas por cooldown

---

## 🔐 Seguridad

### ⚠️ IMPORTANTE: Protege tus credenciales

1. **NO subas `telegram_config.py` a GitHub**
   
   Agrega a `.gitignore`:
   ```
   telegram_config.py
   ```

2. **Usa variables de entorno** (opcional)
   
   ```python
   import os
   TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'default_token')
   ```

3. **Limita permisos del bot**
   - Solo los necesarios para enviar mensajes

---

## 📝 API de Telegram

Documentación oficial: https://core.telegram.org/bots/api

### Límites de la API:
- ✓ 30 mensajes por segundo
- ✓ 1 mensaje por chat por segundo
- ✓ Imágenes hasta 10MB
- ✓ Captions hasta 1024 caracteres

---

## 🎯 Próximas Características

- [ ] Comandos interactivos (/status, /stats, /capture)
- [ ] Configuración via bot (sin editar archivos)
- [ ] Múltiples destinatarios
- [ ] Integración con otros servicios (Discord, Slack)
- [ ] Notificaciones por email
- [ ] Webhooks personalizados

---

## 📞 Soporte

Si tienes problemas:
1. Revisa los logs del sistema
2. Ejecuta `python test_telegram.py`
3. Verifica la documentación de Telegram
4. Abre un issue en el repositorio

---

## 📄 Licencia

MIT License - Fire Monitor Project

---

**🔥 Fire Monitor - Detección inteligente de incendios con ESP32-CAM**
