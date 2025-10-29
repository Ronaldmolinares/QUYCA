#!/usr/bin/env python3
"""
Script de prueba para verificar configuración de Telegram
"""

import sys
import os

# Agregar directorio actual al path
sys.path.insert(0, os.path.dirname(__file__))

from telegram_notifier import TelegramNotifier, test_telegram_connection

def main():
    print("=" * 60)
    print("🧪 TEST DE NOTIFICACIONES DE TELEGRAM")
    print("=" * 60)
    
    # Probar conexión
    print("\n1️⃣ Verificando configuración...")
    
    if not test_telegram_connection():
        print("\n❌ Test fallido")
        print("\n📝 Pasos para configurar:")
        print("   1. Abre Telegram y busca @BotFather")
        print("   2. Crea un bot con /newbot")
        print("   3. Copia el TOKEN que te da")
        print("   4. Busca @userinfobot y obtén tu CHAT_ID")
        print("   5. Edita telegram_config.py con tus datos")
        return
    
    print("\n2️⃣ Probando diferentes tipos de notificaciones...")
    
    notifier = TelegramNotifier()
    
    # Test de alerta de fuego
    print("\n   📢 Enviando alerta de fuego de prueba...")
    from datetime import datetime
    notifier.send_fire_alert(
        detections=3,
        timestamp=datetime.now(),
        severity='MEDIUM'
    )
    
    input("\n   ⏸ Presiona Enter para enviar notificación de despeje...")
    
    # Test de despeje
    print("\n   ✅ Enviando notificación de despeje...")
    notifier.send_clear_alert(duration=120)
    
    input("\n   ⏸ Presiona Enter para enviar reporte de estadísticas...")
    
    # Test de estadísticas
    print("\n   📊 Enviando reporte de estadísticas...")
    notifier.send_stats_report({
        'detections_today': 5,
        'alerts_today': 2,
        'images_today': 3
    })
    
    print("\n✅ Tests completados!")
    print("📱 Verifica tu Telegram para confirmar que recibiste todos los mensajes")

if __name__ == "__main__":
    main()
