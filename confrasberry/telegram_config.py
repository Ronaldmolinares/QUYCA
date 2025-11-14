"""
Configuración de Telegram para notificaciones de incendios
Reemplaza los valores con tus credenciales reales
"""

# ============================================
# CONFIGURACIÓN DE TELEGRAM
# ============================================

# Token del bot (obtenido de @BotFather)
TELEGRAM_BOT_TOKEN = "8464661115:AAEV1zr4qMAij_1Dz3tv3RUehJ95mgFcvBw"

# Chat ID del destinatario (obtenido de @userinfobot)
# Puede ser un chat individual o un grupo
TELEGRAM_CHAT_ID = "1562216334"

# Opciones de notificación
TELEGRAM_ENABLED = True  # Activar/desactivar notificaciones
SEND_IMAGES = True  # Enviar imágenes capturadas
ALERT_COOLDOWN = 10  # Segundos mínimos entre alertas (10 segundos - para emergencias)

# Mensajes personalizados
MESSAGES = {
    'fire_detected': '🔥 ¡ALERTA DE INCENDIO DETECTADO!',
    'fire_cleared': '✅ Alerta despejada - Situación normalizada',
    'system_online': '🟢 Sistema de monitoreo iniciado',
    'system_offline': '🔴 Sistema de monitoreo desconectado',
    'capture_failed': '⚠️ Error al capturar imagen'
}
