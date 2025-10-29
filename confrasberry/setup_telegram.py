#!/usr/bin/env python3
"""
Script de configuración rápida para notificaciones de Telegram
"""

import os
import sys

def check_file_exists(filepath):
    """Verificar si un archivo existe"""
    return os.path.exists(filepath)

def create_config_file():
    """Crear archivo de configuración interactivamente"""
    print("\n" + "="*60)
    print("🔧 CONFIGURACIÓN DE TELEGRAM - FIRE MONITOR")
    print("="*60)
    
    # Verificar si ya existe
    if check_file_exists('telegram_config.py'):
        print("\n⚠️  Ya existe un archivo telegram_config.py")
        response = input("¿Deseas sobrescribirlo? (s/N): ").lower()
        if response != 's':
            print("✓ Manteniendo configuración existente")
            return False
    
    print("\n📝 Necesitas proporcionar:")
    print("   1. Token del bot (de @BotFather)")
    print("   2. Tu Chat ID (de @userinfobot)")
    print("\n💡 Presiona Enter sin escribir nada para cancelar\n")
    
    # Solicitar token
    token = input("🤖 Token del bot: ").strip()
    if not token:
        print("❌ Cancelado")
        return False
    
    # Solicitar chat ID
    chat_id = input("💬 Chat ID: ").strip()
    if not chat_id:
        print("❌ Cancelado")
        return False
    
    # Opciones adicionales
    print("\n⚙️  Opciones adicionales:")
    
    send_images = input("📸 ¿Enviar imágenes con las alertas? (S/n): ").lower()
    send_images = send_images != 'n'
    
    cooldown = input("⏱️  Cooldown entre alertas en segundos [300]: ").strip()
    if not cooldown:
        cooldown = 300
    else:
        try:
            cooldown = int(cooldown)
        except ValueError:
            print("⚠️  Valor inválido, usando 300 segundos")
            cooldown = 300
    
    # Crear contenido del archivo
    config_content = f'''"""
Configuración de Telegram para notificaciones de incendios
Generado automáticamente por setup_telegram.py
"""

# ============================================
# CONFIGURACIÓN DE TELEGRAM
# ============================================

# Token del bot (obtenido de @BotFather)
TELEGRAM_BOT_TOKEN = "{token}"

# Chat ID del destinatario (obtenido de @userinfobot)
TELEGRAM_CHAT_ID = "{chat_id}"

# Opciones de notificación
TELEGRAM_ENABLED = True  # Activar/desactivar notificaciones
SEND_IMAGES = {send_images}  # Enviar imágenes capturadas
ALERT_COOLDOWN = {cooldown}  # Segundos mínimos entre alertas

# Mensajes personalizados
MESSAGES = {{
    'fire_detected': '🔥 ¡ALERTA DE INCENDIO DETECTADO!',
    'fire_cleared': '✅ Alerta despejada - Situación normalizada',
    'system_online': '🟢 Sistema de monitoreo iniciado',
    'system_offline': '🔴 Sistema de monitoreo desconectado',
    'capture_failed': '⚠️ Error al capturar imagen'
}}
'''
    
    # Escribir archivo
    try:
        with open('telegram_config.py', 'w', encoding='utf-8') as f:
            f.write(config_content)
        print("\n✅ Archivo telegram_config.py creado exitosamente!")
        return True
    except Exception as e:
        print(f"\n❌ Error creando archivo: {e}")
        return False

def install_dependencies():
    """Instalar dependencias necesarias"""
    print("\n" + "="*60)
    print("📦 INSTALACIÓN DE DEPENDENCIAS")
    print("="*60)
    
    # Verificar si pip está disponible
    try:
        import pip
    except ImportError:
        print("❌ pip no está instalado")
        return False
    
    print("\n¿Deseas instalar las dependencias necesarias?")
    print("   • paho-mqtt")
    print("   • Pillow")
    print("   • requests")
    
    response = input("\nInstalar ahora? (S/n): ").lower()
    if response == 'n':
        print("⏭️  Saltando instalación de dependencias")
        return False
    
    print("\n📥 Instalando dependencias...\n")
    
    import subprocess
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "paho-mqtt", "Pillow", "requests"
        ])
        print("\n✅ Dependencias instaladas correctamente!")
        return True
    except subprocess.CalledProcessError:
        print("\n❌ Error instalando dependencias")
        print("💡 Intenta manualmente: pip install paho-mqtt Pillow requests")
        return False

def run_test():
    """Ejecutar test de configuración"""
    print("\n" + "="*60)
    print("🧪 PRUEBA DE CONFIGURACIÓN")
    print("="*60)
    
    response = input("\n¿Deseas probar la configuración ahora? (S/n): ").lower()
    if response == 'n':
        print("⏭️  Test omitido")
        return
    
    print("\n🔄 Ejecutando test...\n")
    
    try:
        from telegram_notifier import test_telegram_connection
        test_telegram_connection()
    except Exception as e:
        print(f"\n❌ Error ejecutando test: {e}")
        print("💡 Puedes ejecutarlo manualmente: python test_telegram.py")

def show_next_steps():
    """Mostrar pasos siguientes"""
    print("\n" + "="*60)
    print("✅ CONFIGURACIÓN COMPLETADA")
    print("="*60)
    
    print("\n📋 Próximos pasos:")
    print("\n1. Verificar que recibiste el mensaje de prueba en Telegram")
    print("2. Ejecutar el sistema principal:")
    print("   python fire_monitor.py")
    print("\n3. El sistema ahora enviará notificaciones automáticamente cuando:")
    print("   • Se detecte un incendio")
    print("   • La situación se normalice")
    print("   • El sistema se inicie o detenga")
    
    print("\n📚 Documentación completa: TELEGRAM_README.md")
    print("\n🔧 Para reconfigurar, ejecuta este script de nuevo")
    print("="*60)

def main():
    """Función principal"""
    print("\n🔥 Fire Monitor - Setup de Telegram")
    
    # 1. Instalar dependencias
    install_dependencies()
    
    # 2. Crear configuración
    if not create_config_file():
        print("\n❌ Setup cancelado o fallido")
        return
    
    # 3. Ejecutar test
    run_test()
    
    # 4. Mostrar pasos siguientes
    show_next_steps()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrumpido por el usuario")
        sys.exit(0)
