"""
Fire Monitor - Telegram Notifications
Maneja envío de notificaciones y alertas via Telegram
"""

import requests
import time
from datetime import datetime, timedelta
from typing import Optional
import os

try:
    from telegram_config import (
        TELEGRAM_BOT_TOKEN,
        TELEGRAM_CHAT_ID,
        TELEGRAM_ENABLED,
        SEND_IMAGES,
        ALERT_COOLDOWN,
        MESSAGES
    )
except ImportError:
    print("⚠️ telegram_config.py no encontrado, usando valores por defecto")
    TELEGRAM_BOT_TOKEN = ""
    TELEGRAM_CHAT_ID = ""
    TELEGRAM_ENABLED = False
    SEND_IMAGES = True
    ALERT_COOLDOWN = 300
    MESSAGES = {}

class TelegramNotifier:
    def __init__(self, bot_token: str = None, chat_id: str = None):
        """
        Inicializar notificador de Telegram
        
        Args:
            bot_token: Token del bot de Telegram
            chat_id: ID del chat para enviar mensajes
        """
        self.bot_token = bot_token or TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or TELEGRAM_CHAT_ID
        self.enabled = TELEGRAM_ENABLED and self.bot_token and self.chat_id
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        # Control de rate limiting
        self.last_alert_time = None
        self.alert_cooldown = ALERT_COOLDOWN
        
        if self.enabled:
            print("✓ Notificador de Telegram inicializado")
            self.verify_connection()
        else:
            print("⚠️ Notificaciones de Telegram deshabilitadas")
    
    def verify_connection(self) -> bool:
        """Verificar que el bot está configurado correctamente"""
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    bot_info = data.get('result', {})
                    bot_name = bot_info.get('username', 'Unknown')
                    print(f"✓ Bot conectado: @{bot_name}")
                    return True
                    
            print("❌ Error verificando bot de Telegram")
            return False
            
        except Exception as e:
            print(f"❌ Error conectando con Telegram: {e}")
            return False
    
    def send_message(self, text: str, parse_mode: str = 'HTML') -> bool:
        """
        Enviar mensaje de texto
        
        Args:
            text: Mensaje a enviar
            parse_mode: Formato del mensaje ('HTML', 'Markdown', o None)
            
        Returns:
            True si se envió correctamente
        """
        if not self.enabled:
            return False
        
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                return True
            else:
                print(f"❌ Error enviando mensaje: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error enviando mensaje a Telegram: {e}")
            return False
    
    def send_photo(self, image_path: str, caption: str = None) -> bool:
        """
        Enviar foto con caption opcional
        
        Args:
            image_path: Ruta a la imagen a enviar
            caption: Texto que acompaña la imagen
            
        Returns:
            True si se envió correctamente
        """
        if not self.enabled or not SEND_IMAGES:
            return False
        
        if not os.path.exists(image_path):
            print(f"❌ Imagen no encontrada: {image_path}")
            return False
        
        try:
            url = f"{self.base_url}/sendPhoto"
            
            with open(image_path, 'rb') as photo:
                files = {'photo': photo}
                data = {'chat_id': self.chat_id}
                
                if caption:
                    data['caption'] = caption
                    data['parse_mode'] = 'HTML'
                
                response = requests.post(url, files=files, data=data, timeout=30)
                
                if response.status_code == 200:
                    print(f"✓ Foto enviada: {os.path.basename(image_path)}")
                    return True
                else:
                    print(f"❌ Error enviando foto: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error enviando foto a Telegram: {e}")
            return False
    
    def can_send_alert(self) -> bool:
        """Verificar si se puede enviar una alerta (rate limiting)"""
        if not self.last_alert_time:
            return True
        
        elapsed = (datetime.now() - self.last_alert_time).total_seconds()
        return elapsed >= self.alert_cooldown
    
    def send_fire_alert(self, detections: int = 0, timestamp: datetime = None, 
                       severity: str = 'MEDIUM', image_path: str = None) -> bool:
        """
        Enviar alerta de incendio detectado
        
        Args:
            detections: Número de detecciones acumuladas
            timestamp: Fecha/hora de la detección
            severity: Severidad de la alerta (LOW, MEDIUM, HIGH)
            image_path: Ruta a imagen capturada (opcional)
            
        Returns:
            True si se envió correctamente
        """
        if not self.enabled:
            return False
        
        # Rate limiting
        if not self.can_send_alert():
            remaining = self.alert_cooldown - (datetime.now() - self.last_alert_time).total_seconds()
            print(f"⏳ Alerta bloqueada por cooldown ({int(remaining)}s restantes)")
            return False
        
        # Preparar mensaje
        timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S') if timestamp else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Emojis según severidad
        severity_emoji = {
            'LOW': '🟡',
            'MEDIUM': '🟠',
            'HIGH': '🔴'
        }
        
        message = f"""
{MESSAGES.get('fire_detected', '🔥 ¡ALERTA DE INCENDIO!')}

{severity_emoji.get(severity, '🔥')} <b>Severidad:</b> {severity}
📊 <b>Detecciones:</b> {detections}
🕐 <b>Fecha/Hora:</b> {timestamp_str}

⚠️ <i>Verificar situación inmediatamente</i>
"""
        
        # Enviar mensaje de texto
        success = self.send_message(message.strip())
        
        # Enviar imagen si está disponible
        if success and image_path and os.path.exists(image_path):
            caption = f"📸 Captura de detección - {timestamp_str}"
            self.send_photo(image_path, caption)
        
        if success:
            self.last_alert_time = datetime.now()
            print(f"📱 Alerta de incendio enviada a Telegram")
        
        return success
    
    def send_clear_alert(self, duration: int = None) -> bool:
        """
        Enviar notificación de alerta despejada
        
        Args:
            duration: Duración de la alerta en segundos (opcional)
            
        Returns:
            True si se envió correctamente
        """
        if not self.enabled:
            return False
        
        message = MESSAGES.get('fire_cleared', '✅ Alerta despejada')
        
        if duration:
            minutes = duration // 60
            seconds = duration % 60
            message += f"\n\n⏱ Duración: {minutes}m {seconds}s"
        
        message += "\n\n✓ <i>Situación normalizada</i>"
        
        success = self.send_message(message)
        
        if success:
            print("📱 Notificación de despeje enviada a Telegram")
        
        return success
    
    def send_system_status(self, status: str, details: str = None) -> bool:
        """
        Enviar estado del sistema
        
        Args:
            status: 'online' o 'offline'
            details: Información adicional (opcional)
            
        Returns:
            True si se envió correctamente
        """
        if not self.enabled:
            return False
        
        if status == 'online':
            message = MESSAGES.get('system_online', '🟢 Sistema iniciado')
        else:
            message = MESSAGES.get('system_offline', '🔴 Sistema detenido')
        
        if details:
            message += f"\n\n{details}"
        
        return self.send_message(message)
    
    def send_capture_notification(self, image_path: str, success: bool = True) -> bool:
        """
        Notificar sobre captura de imagen
        
        Args:
            image_path: Ruta a la imagen capturada
            success: Si la captura fue exitosa
            
        Returns:
            True si se envió correctamente
        """
        if not self.enabled:
            return False
        
        if success and os.path.exists(image_path):
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            caption = f"📸 Captura manual\n🕐 {timestamp}"
            return self.send_photo(image_path, caption)
        else:
            message = MESSAGES.get('capture_failed', '⚠️ Error en captura')
            return self.send_message(message)
    
    def send_stats_report(self, stats: dict) -> bool:
        """
        Enviar reporte de estadísticas diarias
        
        Args:
            stats: Diccionario con estadísticas
            
        Returns:
            True si se envió correctamente
        """
        if not self.enabled:
            return False
        
        message = f"""
📊 <b>Reporte Diario - Fire Monitor</b>

🔥 Detecciones: {stats.get('detections_today', 0)}
⚠️ Alertas: {stats.get('alerts_today', 0)}
📸 Imágenes: {stats.get('images_today', 0)}
🕐 Fecha: {datetime.now().strftime('%Y-%m-%d')}

✓ <i>Sistema operativo</i>
"""
        
        return self.send_message(message.strip())

# ============================================
# FUNCIONES DE UTILIDAD
# ============================================

def test_telegram_connection():
    """Función de prueba para verificar configuración"""
    notifier = TelegramNotifier()
    
    if not notifier.enabled:
        print("❌ Telegram no está habilitado o configurado correctamente")
        print("\n📝 Para configurar:")
        print("1. Edita telegram_config.py")
        print("2. Agrega tu BOT_TOKEN y CHAT_ID")
        print("3. Configura TELEGRAM_ENABLED = True")
        return False
    
    print("\n🧪 Enviando mensaje de prueba...")
    success = notifier.send_message("🔥 Test de Fire Monitor - Sistema configurado correctamente!")
    
    if success:
        print("✅ ¡Mensaje de prueba enviado!")
        print("✓ Verifica tu Telegram para confirmar")
    else:
        print("❌ Error enviando mensaje de prueba")
    
    return success

if __name__ == "__main__":
    # Ejecutar prueba si se ejecuta directamente
    test_telegram_connection()
