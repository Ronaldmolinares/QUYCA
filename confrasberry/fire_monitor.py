"""
Fire Monitor - Raspberry Pi MQTT Handler with Database
Recibe alertas de ESP32-CAM y solicita capturas de imagen
"""

import paho.mqtt.client as mqtt
import json
import base64
import os
from datetime import datetime
from PIL import Image
import io
from database import FireMonitorDB
from telegram_notifier import TelegramNotifier

# ============================================
# CONFIGURACIÓN
# ============================================

MQTT_BROKER = "localhost"
MQTT_PORT = 1883

# Topics
TOPIC_ALERT = "fire/alert"
TOPIC_CAPTURE_CMD = "fire/capture"
TOPIC_IMAGE = "fire/image"
TOPIC_IMAGE_META = "fire/image/meta"
TOPIC_STATUS = "fire/status"

# Directorios
IMAGES_DIR = "/home/pi/fire_images"
LATEST_IMAGE_PATH = "/home/pi/fire_monitor/public/latest.jpg"

# Estado global
image_chunks = {}
image_metadata = {}
last_alert_time = None
capture_requested = False
current_alert_id = None  # ID de la alerta activa actual

# Inicializar base de datos
db = FireMonitorDB()

# Inicializar notificador de Telegram
telegram = TelegramNotifier()

# ============================================
# FUNCIONES DE UTILIDAD
# ============================================

def ensure_directories():
    """Crear directorios necesarios"""
    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(LATEST_IMAGE_PATH), exist_ok=True)
    print(f"✓ Directorios verificados")
    db.log('INFO', 'PYTHON', 'Directorios verificados')

def save_image(image_data, filename=None, metadata=None):
    """Guardar imagen desde Base64"""
    global current_alert_id
    
    try:
        # Decodificar Base64
        image_bytes = base64.b64decode(image_data)
        
        # Generar nombre si no se proporciona
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"fire_capture_{timestamp}.jpg"
        
        # Guardar en directorio de imágenes
        filepath = os.path.join(IMAGES_DIR, filename)
        with open(filepath, 'wb') as f:
            f.write(image_bytes)
        
        # Guardar como última imagen para la web
        with open(LATEST_IMAGE_PATH, 'wb') as f:
            f.write(image_bytes)
        
        # Obtener información de la imagen
        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size
        
        print(f"✅ Imagen guardada: {filename} ({width}x{height}, {len(image_bytes)} bytes)")
        
        # Guardar en base de datos
        if current_alert_id:
            chunks_total = metadata.get('chunks', 1) if metadata else 1
            db.save_image_record(
                alert_id=current_alert_id,
                file_path=filepath,
                file_name=filename,
                image_size=len(image_bytes),
                width=width,
                height=height,
                chunks_total=chunks_total,
                trigger='AUTO' if capture_requested else 'MANUAL'
            )
        
        return filepath
        
    except Exception as e:
        print(f"❌ Error guardando imagen: {e}")
        db.log('ERROR', 'PYTHON', f'Error guardando imagen: {e}')
        return None

def request_capture():
    """Solicitar captura a ESP32"""
    global capture_requested
    if not capture_requested:
        client.publish(TOPIC_CAPTURE_CMD, "CAPTURE")
        capture_requested = True
        print("📸 Solicitando captura a ESP32...")
        db.log('INFO', 'PYTHON', 'Captura solicitada a ESP32')

# ============================================
# CALLBACKS MQTT
# ============================================

def on_connect(client, userdata, flags, rc):
    """Callback cuando se conecta al broker"""
    if rc == 0:
        print("✓ Conectado al broker MQTT")
        db.log('INFO', 'MQTT', 'Conectado al broker MQTT')
        
        # Suscribirse a todos los topics
        client.subscribe(TOPIC_ALERT)
        client.subscribe(TOPIC_IMAGE)
        client.subscribe(TOPIC_IMAGE_META)
        client.subscribe(TOPIC_STATUS)
        
        print(f"✓ Suscrito a topics:")
        print(f"  - {TOPIC_ALERT}")
        print(f"  - {TOPIC_IMAGE}")
        print(f"  - {TOPIC_IMAGE_META}")
        print(f"  - {TOPIC_STATUS}")
        
    else:
        print(f"❌ Error de conexión MQTT: {rc}")
        db.log('ERROR', 'MQTT', f'Error de conexión MQTT: {rc}')

def on_message(client, userdata, msg):
    """Callback cuando llega un mensaje"""
    global last_alert_time, image_chunks, image_metadata, capture_requested, current_alert_id
    
    topic = msg.topic
    
    try:
        # ===== ALERTA DE FUEGO =====
        if topic == TOPIC_ALERT:
            data = json.loads(msg.payload.decode())
            alert_type = data.get('alert')
            timestamp = data.get('timestamp')
            detections = data.get('detections', 0)
            
            if alert_type == "FIRE_DETECTED":
                print(f"\n🔥 ¡ALERTA DE FUEGO!")
                print(f"   Timestamp: {timestamp}")
                print(f"   Detecciones totales: {detections}")
                
                last_alert_time = datetime.now()
                
                # Registrar detección en DB
                detection_id = db.insert_detection(
                    detected=True,
                    esp32_millis=timestamp,
                    confidence=100
                )
                
                # Verificar si ya hay una alerta activa
                active_alert = db.get_active_alert()
                
                if active_alert:
                    # Actualizar contador de detecciones
                    current_alert_id = active_alert['id']
                    db.update_alert_detections(current_alert_id, detections)
                    print(f"   📊 Alerta existente actualizada (ID: {current_alert_id})")
                else:
                    # Crear nueva alerta
                    severity = 'HIGH' if detections > 5 else 'MEDIUM' if detections > 2 else 'LOW'
                    current_alert_id = db.create_alert(
                        detection_id=detection_id,
                        alert_type='FIRE_DETECTED',
                        severity=severity,
                        detections_count=detections
                    )
                    print(f"   🆕 Nueva alerta creada (ID: {current_alert_id}, Severidad: {severity})")
                    
                    # 🔔 ENVIAR NOTIFICACIÓN DE TELEGRAM (solo para nuevas alertas)
                    telegram.send_fire_alert(
                        detections=detections,
                        timestamp=last_alert_time,
                        severity=severity
                    )
                
                # Solicitar captura automáticamente
                request_capture()
                
            elif alert_type == "CLEAR":
                print(f"✓ Alerta despejada")
                
                # Registrar detección negativa
                db.insert_detection(
                    detected=False,
                    esp32_millis=timestamp,
                    confidence=100
                )
                
                # Resolver alerta activa si existe
                if current_alert_id:
                    # Calcular duración de la alerta
                    alert_data = db.get_alert_by_id(current_alert_id)
                    if alert_data:
                        start_time = datetime.fromisoformat(alert_data['created_at'])
                        duration = int((datetime.now() - start_time).total_seconds())
                        
                        # Enviar notificación de despeje
                        telegram.send_clear_alert(duration=duration)
                    
                    db.resolve_alert(current_alert_id, status='RESOLVED')
                    print(f"   ✓ Alerta {current_alert_id} resuelta")
                    current_alert_id = None
                
                capture_requested = False
        
        # ===== METADATA DE IMAGEN =====
        elif topic == TOPIC_IMAGE_META:
            data = json.loads(msg.payload.decode())
            image_metadata = data
            image_chunks.clear()
            
            print(f"\n📦 Metadata de imagen recibida:")
            print(f"   Tamaño: {data.get('size')} bytes")
            print(f"   Resolución: {data.get('width')}x{data.get('height')}")
            print(f"   Chunks esperados: {data.get('chunks')}")
            
            db.log('INFO', 'CAMERA', f"Metadata recibida: {data.get('width')}x{data.get('height')}, {data.get('chunks')} chunks")
        
        # ===== CHUNKS DE IMAGEN =====
        elif topic == TOPIC_IMAGE:
            data = json.loads(msg.payload.decode())
            chunk_num = data.get('chunk')
            total_chunks = data.get('total')
            chunk_data = data.get('data')
            
            # Validar que chunk_data no sea None
            if chunk_data is None:
                print(f"⚠️ Chunk {chunk_num + 1}/{total_chunks} está vacío (None)")
                db.log('WARNING', 'CAMERA', f'Chunk {chunk_num + 1}/{total_chunks} vacío')
                return
            
            image_chunks[chunk_num] = chunk_data
            
            print(f"📥 Chunk {chunk_num + 1}/{total_chunks} recibido ({len(chunk_data)} chars)")
            
            # Si recibimos todos los chunks, reconstruir imagen
            if len(image_chunks) == total_chunks:
                print("🔄 Reconstruyendo imagen...")
                
                # Verificar que todos los chunks estén presentes
                missing_chunks = []
                for i in range(total_chunks):
                    if i not in image_chunks:
                        missing_chunks.append(i)
                
                if missing_chunks:
                    print(f"❌ Faltan chunks: {missing_chunks}")
                    db.log('ERROR', 'CAMERA', f'Faltan chunks: {missing_chunks}')
                    image_chunks.clear()
                    return
                
                # Ordenar y concatenar chunks
                full_image_b64 = ""
                for i in range(total_chunks):
                    chunk = image_chunks[i]
                    if chunk is None:
                        print(f"❌ Chunk {i} es None, abortando reconstrucción")
                        db.log('ERROR', 'CAMERA', f'Chunk {i} es None')
                        image_chunks.clear()
                        return
                    full_image_b64 += chunk
                
                print(f"📊 Imagen completa: {len(full_image_b64)} caracteres Base64")
                
                # Guardar imagen
                if save_image(full_image_b64, metadata=image_metadata):
                    print("✅ Imagen procesada correctamente")
                    
                    # 🔔 ENVIAR IMAGEN POR TELEGRAM si hay alerta activa
                    if current_alert_id:
                        # Obtener ruta de la última imagen guardada
                        import glob
                        images = glob.glob(os.path.join(IMAGES_DIR, "fire_capture_*.jpg"))
                        if images:
                            latest_image = max(images, key=os.path.getctime)
                            
                            # Obtener datos de la alerta para contexto
                            alert_data = db.get_alert_by_id(current_alert_id)
                            if alert_data:
                                # Crear caption con información de la alerta
                                timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                severity = alert_data.get('severity', 'MEDIUM')
                                detections = alert_data.get('detections_count', 0)
                                
                                caption = f"""
📸 <b>Imagen de Alerta #{current_alert_id}</b>

🔴 Severidad: {severity}
📊 Detecciones: {detections}
🕐 Captura: {timestamp_str}
"""
                                # Enviar solo la foto con caption (sin cooldown)
                                telegram.send_photo(latest_image, caption=caption.strip())
                
                # Limpiar chunks
                image_chunks.clear()
                image_metadata.clear()
                capture_requested = False
        
        # ===== ESTADO DEL DISPOSITIVO =====
        elif topic == TOPIC_STATUS:
            data = json.loads(msg.payload.decode())
            status = data.get('status')
            device = data.get('device', 'ESP32-CAM')
            ip = data.get('ip')
            
            # Actualizar en base de datos
            db.update_device_status(
                device_id=device,
                status=status,
                ip_address=ip
            )
            
            if status == "online":
                print(f"✓ {device} conectado (IP: {ip})")
    
    except json.JSONDecodeError:
        print(f"❌ Error decodificando JSON del topic {topic}")
        db.log('ERROR', 'MQTT', f'Error decodificando JSON del topic {topic}')
    except Exception as e:
        print(f"❌ Error procesando mensaje: {e}")
        db.log('ERROR', 'MQTT', f'Error procesando mensaje: {e}')
        import traceback
        traceback.print_exc()

def on_disconnect(client, userdata, rc):
    """Callback cuando se desconecta del broker"""
    if rc != 0:
        print(f"⚠️ Desconexión inesperada del broker (código: {rc})")
        db.log('WARNING', 'MQTT', f'Desconexión inesperada (código: {rc})')
        print("🔄 Intentando reconectar...")

# ============================================
# MAIN
# ============================================

def main():
    global client
    
    print("=" * 50)
    print("🔥 Fire Monitor - Raspberry Pi Handler + DB")
    print("=" * 50)
    
    # Crear directorios
    ensure_directories()
    
    # Mostrar estadísticas
    stats = db.get_today_stats()
    if stats:
        print(f"\n📊 Estadísticas de hoy:")
        print(f"   • Detecciones: {stats.get('detections_today', 0)}")
        print(f"   • Alertas: {stats.get('alerts_today', 0)}")
        print(f"   • Imágenes: {stats.get('images_today', 0)}")
    
    # Configurar cliente MQTT
    try:
        client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION1,
            client_id="RaspberryPi-FireMonitor"
        )
    except AttributeError:
        client = mqtt.Client(client_id="RaspberryPi-FireMonitor")
    
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    # Conectar al broker
    try:
        print(f"\n🔌 Conectando a broker MQTT en {MQTT_BROKER}:{MQTT_PORT}...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # Enviar notificación de sistema iniciado
        telegram.send_system_status('online', f'Broker: {MQTT_BROKER}:{MQTT_PORT}')
        
        print("\n✅ Sistema iniciado correctamente")
        print("📡 Esperando alertas de fuego...")
        print("\nPresiona Ctrl+C para detener\n")
        
        # Actualizar estadísticas cada hora
        import threading
        def update_stats():
            while True:
                import time
                time.sleep(3600)  # 1 hora
                db.update_daily_statistics()
                print("📊 Estadísticas actualizadas")
        
        stats_thread = threading.Thread(target=update_stats, daemon=True)
        stats_thread.start()
        
        # Loop infinito
        client.loop_forever()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Deteniendo sistema...")
        
        # Guardar estadísticas finales
        db.update_daily_statistics()
        
        # Enviar notificación de sistema detenido
        stats = db.get_today_stats()
        details = None
        if stats:
            details = f"Detecciones: {stats.get('detections_today', 0)} | Alertas: {stats.get('alerts_today', 0)}"
        telegram.send_system_status('offline', details)
        
        # Mostrar resumen
        print("\n📊 Resumen de la sesión:")
        if stats:
            print(f"   • Detecciones: {stats.get('detections_today', 0)}")
            print(f"   • Alertas: {stats.get('alerts_today', 0)}")
            print(f"   • Imágenes capturadas: {stats.get('images_today', 0)}")
        
        client.disconnect()
        print("✓ Desconectado")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.log('CRITICAL', 'PYTHON', f'Error fatal: {e}')

if __name__ == "__main__":
    main()