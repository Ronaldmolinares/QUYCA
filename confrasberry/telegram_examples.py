#!/usr/bin/env python3
"""
Ejemplos de uso avanzado del notificador de Telegram
"""

from telegram_notifier import TelegramNotifier
from datetime import datetime
import time

def ejemplo_basico():
    """Ejemplo 1: Uso básico"""
    print("\n" + "="*50)
    print("📝 Ejemplo 1: Uso Básico")
    print("="*50)
    
    notifier = TelegramNotifier()
    
    # Mensaje simple
    notifier.send_message("Hola desde Fire Monitor!")
    print("✓ Mensaje simple enviado")
    
    time.sleep(1)
    
    # Mensaje con formato HTML
    notifier.send_message(
        "<b>Mensaje importante</b>\n<i>Con formato HTML</i>",
        parse_mode='HTML'
    )
    print("✓ Mensaje con formato enviado")

def ejemplo_alertas():
    """Ejemplo 2: Diferentes tipos de alertas"""
    print("\n" + "="*50)
    print("🔥 Ejemplo 2: Alertas de Fuego")
    print("="*50)
    
    notifier = TelegramNotifier()
    
    # Alerta de severidad baja
    print("\n1. Alerta de severidad BAJA:")
    notifier.send_fire_alert(
        detections=2,
        timestamp=datetime.now(),
        severity='LOW'
    )
    
    time.sleep(2)
    
    # Alerta de severidad media
    print("\n2. Alerta de severidad MEDIA:")
    notifier.send_fire_alert(
        detections=4,
        timestamp=datetime.now(),
        severity='MEDIUM'
    )
    
    time.sleep(2)
    
    # Alerta de severidad alta
    print("\n3. Alerta de severidad ALTA:")
    notifier.send_fire_alert(
        detections=8,
        timestamp=datetime.now(),
        severity='HIGH'
    )
    
    time.sleep(2)
    
    # Despeje de alerta
    print("\n4. Despeje de alerta:")
    notifier.send_clear_alert(duration=180)  # 3 minutos

def ejemplo_imagenes():
    """Ejemplo 3: Envío de imágenes"""
    print("\n" + "="*50)
    print("📸 Ejemplo 3: Envío de Imágenes")
    print("="*50)
    
    notifier = TelegramNotifier()
    
    # Verificar si existe una imagen de ejemplo
    import os
    
    # Buscar imagen más reciente
    image_dir = "c:/Users/Samir/fire_monitor/images"  # Ajustar según tu sistema
    
    if os.path.exists(image_dir):
        images = [f for f in os.listdir(image_dir) if f.endswith('.jpg')]
        if images:
            latest_image = os.path.join(image_dir, images[0])
            
            print(f"Enviando imagen: {latest_image}")
            notifier.send_photo(
                image_path=latest_image,
                caption="📸 Ejemplo de captura de incendio"
            )
            print("✓ Imagen enviada")
        else:
            print("⚠️ No hay imágenes disponibles en el directorio")
    else:
        print("⚠️ Directorio de imágenes no encontrado")
        print(f"   Ruta buscada: {image_dir}")

def ejemplo_estadisticas():
    """Ejemplo 4: Reportes de estadísticas"""
    print("\n" + "="*50)
    print("📊 Ejemplo 4: Reportes de Estadísticas")
    print("="*50)
    
    notifier = TelegramNotifier()
    
    # Estadísticas de ejemplo
    stats = {
        'detections_today': 15,
        'alerts_today': 4,
        'images_today': 6
    }
    
    notifier.send_stats_report(stats)
    print("✓ Reporte enviado")

def ejemplo_estado_sistema():
    """Ejemplo 5: Notificaciones de estado del sistema"""
    print("\n" + "="*50)
    print("🔧 Ejemplo 5: Estado del Sistema")
    print("="*50)
    
    notifier = TelegramNotifier()
    
    # Sistema iniciado
    print("\n1. Sistema iniciado:")
    notifier.send_system_status(
        'online',
        details='Broker: localhost:1883\nDispositivos: 1 ESP32-CAM'
    )
    
    time.sleep(2)
    
    # Sistema detenido
    print("\n2. Sistema detenido:")
    notifier.send_system_status(
        'offline',
        details='Sesión: 2 horas\nAlertas: 3\nImágenes: 5'
    )

def ejemplo_rate_limiting():
    """Ejemplo 6: Control de rate limiting"""
    print("\n" + "="*50)
    print("⏱️ Ejemplo 6: Rate Limiting")
    print("="*50)
    
    notifier = TelegramNotifier()
    
    # Primera alerta (debe enviarse)
    print("\n1. Primera alerta:")
    if notifier.can_send_alert():
        notifier.send_fire_alert(
            detections=3,
            timestamp=datetime.now(),
            severity='MEDIUM'
        )
        print("✓ Alerta enviada")
    
    time.sleep(1)
    
    # Segunda alerta (debe bloquearse por cooldown)
    print("\n2. Segunda alerta (debe bloquearse):")
    if notifier.can_send_alert():
        print("✓ Se puede enviar")
    else:
        print("❌ Bloqueada por cooldown")
        remaining = notifier.alert_cooldown - \
                   (datetime.now() - notifier.last_alert_time).total_seconds()
        print(f"   Tiempo restante: {int(remaining)} segundos")

def ejemplo_mensajes_personalizados():
    """Ejemplo 7: Mensajes totalmente personalizados"""
    print("\n" + "="*50)
    print("✨ Ejemplo 7: Mensajes Personalizados")
    print("="*50)
    
    notifier = TelegramNotifier()
    
    # Mensaje con emojis y formato
    mensaje = f"""
🔥 <b>REPORTE DE SEGURIDAD</b> 🔥

📅 Fecha: {datetime.now().strftime('%Y-%m-%d')}
🕐 Hora: {datetime.now().strftime('%H:%M:%S')}

<b>Estado actual:</b>
✅ Sistema operativo
✅ Cámara activa
✅ MQTT conectado

<b>Estadísticas:</b>
• Uptime: 2h 15m
• Alertas hoy: 3
• Detecciones: 12

<i>Todo funcionando correctamente</i> ✨
"""
    
    notifier.send_message(mensaje.strip(), parse_mode='HTML')
    print("✓ Mensaje personalizado enviado")

def ejemplo_multiples_alertas():
    """Ejemplo 8: Secuencia de alertas realista"""
    print("\n" + "="*50)
    print("🎬 Ejemplo 8: Secuencia Realista")
    print("="*50)
    
    notifier = TelegramNotifier()
    
    print("\nSimulando detección de incendio...")
    
    # 1. Sistema detecta fuego
    print("\n1. Fuego detectado:")
    notifier.send_fire_alert(
        detections=1,
        timestamp=datetime.now(),
        severity='LOW'
    )
    
    time.sleep(3)
    
    # 2. Aumento de detecciones
    print("\n2. Aumentando severidad:")
    mensaje = """
⚠️ <b>ACTUALIZACIÓN DE ALERTA</b>

🔥 Las detecciones han aumentado
📊 Contador: 5 detecciones
🔴 Severidad actualizada a ALTA

<i>Revisar inmediatamente</i>
"""
    notifier.send_message(mensaje.strip())
    
    time.sleep(3)
    
    # 3. Captura de imagen
    print("\n3. Imagen capturada:")
    notifier.send_message("📸 Captura en progreso...")
    
    time.sleep(2)
    
    # 4. Situación bajo control
    print("\n4. Situación controlada:")
    notifier.send_clear_alert(duration=240)
    
    time.sleep(2)
    
    # 5. Reporte final
    print("\n5. Reporte final:")
    notifier.send_message("""
📋 <b>REPORTE DE INCIDENTE</b>

• Inicio: 14:35:22
• Fin: 14:39:22
• Duración: 4 minutos
• Severidad máxima: ALTA
• Imágenes capturadas: 2

✅ <i>Incidente resuelto exitosamente</i>
""")

def menu_interactivo():
    """Menú para probar diferentes ejemplos"""
    print("\n" + "="*60)
    print("🔥 EJEMPLOS DE USO - TELEGRAM NOTIFIER")
    print("="*60)
    
    opciones = {
        '1': ('Uso básico', ejemplo_basico),
        '2': ('Alertas de fuego', ejemplo_alertas),
        '3': ('Envío de imágenes', ejemplo_imagenes),
        '4': ('Reportes de estadísticas', ejemplo_estadisticas),
        '5': ('Estado del sistema', ejemplo_estado_sistema),
        '6': ('Rate limiting', ejemplo_rate_limiting),
        '7': ('Mensajes personalizados', ejemplo_mensajes_personalizados),
        '8': ('Secuencia realista', ejemplo_multiples_alertas),
        '9': ('Ejecutar todos', None),
        '0': ('Salir', None)
    }
    
    while True:
        print("\n📋 Selecciona un ejemplo:\n")
        for key, (desc, _) in opciones.items():
            print(f"   {key}. {desc}")
        
        opcion = input("\n➤ Opción: ").strip()
        
        if opcion == '0':
            print("\n👋 ¡Hasta luego!")
            break
        
        elif opcion == '9':
            print("\n🚀 Ejecutando todos los ejemplos...\n")
            for key in ['1', '2', '4', '5', '7']:  # Omitir imágenes y rate limit
                _, funcion = opciones[key]
                if funcion:
                    funcion()
                    time.sleep(3)
            print("\n✅ Todos los ejemplos completados!")
        
        elif opcion in opciones:
            _, funcion = opciones[opcion]
            if funcion:
                funcion()
        
        else:
            print("\n❌ Opción inválida")
        
        input("\n⏸  Presiona Enter para continuar...")

def main():
    """Función principal"""
    
    # Verificar que Telegram esté configurado
    try:
        from telegram_config import TELEGRAM_ENABLED, TELEGRAM_BOT_TOKEN
        
        if not TELEGRAM_ENABLED or not TELEGRAM_BOT_TOKEN:
            print("\n❌ ERROR: Telegram no está configurado")
            print("\n📝 Para configurar:")
            print("   1. Ejecuta: python setup_telegram.py")
            print("   2. O edita manualmente: telegram_config.py")
            return
    
    except ImportError:
        print("\n❌ ERROR: telegram_config.py no encontrado")
        print("\n📝 Ejecuta: python setup_telegram.py")
        return
    
    # Mostrar menú
    menu_interactivo()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
