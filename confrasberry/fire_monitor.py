#!/usr/bin/env python3
"""
Fire Monitor - Raspberry Pi MQTT Handler
Recibe alertas de ESP32-CAM y solicita capturas de imagen
"""

import paho.mqtt.client as mqtt
import json
import base64
import os
from datetime import datetime
from PIL import Image
import io
import traceback

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
image_chunks = {}  # Ahora guardamos BYTES, no strings
image_metadata = {}
last_alert_time = None
capture_requested = False

# ============================================
# FUNCIONES DE UTILIDAD
# ============================================

def ensure_directories():
    """Crear directorios necesarios"""
    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(LATEST_IMAGE_PATH), exist_ok=True)
    print(f"✓ Directorios verificados")
    print(f"  - Imágenes: {IMAGES_DIR}")
    print(f"  - Última imagen: {LATEST_IMAGE_PATH}")

def save_image_bytes(image_bytes, filename=None):
    """Guardar imagen desde bytes binarios"""
    try:
        # Validar que tenemos datos
        if not image_bytes or len(image_bytes) == 0:
            print("❌ Error: datos de imagen vacíos")
            return None
        
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
        
        # Validar que sea una imagen válida
        try:
            img = Image.open(io.BytesIO(image_bytes))
            width, height = img.size
            
            print(f"✅ Imagen guardada exitosamente:")
            print(f"   Archivo: {filename}")
            print(f"   Resolución: {width}x{height}")
            print(f"   Tamaño: {len(image_bytes)} bytes")
            print(f"   Ruta completa: {filepath}")
        except Exception as e:
            print(f"⚠️ Imagen guardada pero error al validar: {e}")
        
        return filepath
        
    except Exception as e:
        print(f"❌ Error guardando imagen: {e}")
        traceback.print_exc()
        return None

def request_capture():
    """Solicitar captura a ESP32"""
    global capture_requested
    if not capture_requested:
        client.publish(TOPIC_CAPTURE_CMD, "CAPTURE")
        capture_requested = True
        print("📸 Solicitando captura a ESP32...")

# ============================================
# CALLBACKS MQTT
# ============================================

def on_connect(client, userdata, flags, rc, properties=None):
    """Callback cuando se conecta al broker"""
    if rc == 0:
        print("✓ Conectado al broker MQTT")
        
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

def on_message(client, userdata, msg):
    """Callback cuando llega un mensaje"""
    global last_alert_time, image_chunks, image_metadata, capture_requested
    
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
                
                # Solicitar captura automáticamente
                request_capture()
                
            elif alert_type == "CLEAR":
                print(f"✓ Alerta despejada")
                capture_requested = False
        
        # ===== METADATA DE IMAGEN =====
        elif topic == TOPIC_IMAGE_META:
            data = json.loads(msg.payload.decode())
            image_metadata = data
            image_chunks.clear()  # Limpiar chunks anteriores
            
            print(f"\n📦 Metadata de imagen recibida:")
            print(f"   Tamaño: {data.get('size')} bytes")
            print(f"   Resolución: {data.get('width')}x{data.get('height')}")
            print(f"   Chunks esperados: {data.get('chunks')}")
        
        # ===== CHUNKS DE IMAGEN =====
        elif topic == TOPIC_IMAGE:
            data = json.loads(msg.payload.decode())
            chunk_num = data.get('chunk')
            total_chunks = data.get('total')
            chunk_data_b64 = data.get('data')
            
            # VALIDAR que el chunk tenga datos
            if chunk_data_b64 is None or chunk_data_b64 == "":
                print(f"⚠️ Chunk {chunk_num} sin datos, omitiendo...")
                return
            
            # DECODIFICAR CADA CHUNK DE BASE64 A BINARIO
            try:
                chunk_bytes = base64.b64decode(chunk_data_b64)
                image_chunks[chunk_num] = chunk_bytes
                
                print(f"📥 Chunk {chunk_num + 1}/{total_chunks} recibido ({len(chunk_bytes)} bytes binarios)")
            except Exception as e:
                print(f"❌ Error decodificando chunk {chunk_num}: {e}")
                return
            
            # Si recibimos todos los chunks, reconstruir imagen
            if len(image_chunks) == total_chunks:
                print(f"🔄 Reconstruyendo imagen desde {total_chunks} chunks...")
                
                # CONCATENAR LOS BYTES BINARIOS
                full_image_bytes = b""
                
                for i in range(total_chunks):
                    if i in image_chunks:
                        chunk = image_chunks[i]
                        if chunk is not None:
                            full_image_bytes += chunk
                            print(f"   ✓ Chunk {i} agregado ({len(chunk)} bytes)")
                        else:
                            print(f"   ⚠️ Chunk {i} es None")
                    else:
                        print(f"   ❌ Falta chunk {i}, imagen incompleta")
                        # Limpiar y esperar nueva imagen
                        image_chunks.clear()
                        image_metadata.clear()
                        return
                
                # Validar que tenemos datos completos
                if len(full_image_bytes) > 0:
                    print(f"📊 Total bytes concatenados: {len(full_image_bytes)}")
                    
                    # Guardar imagen BINARIA directamente
                    result = save_image_bytes(full_image_bytes)
                    
                    if result:
                        print(f"✅ Proceso completado exitosamente\n")
                    else:
                        print(f"❌ Error al guardar la imagen\n")
                else:
                    print(f"❌ Error: imagen binaria vacía después de concatenar")
                
                # Limpiar chunks y metadata
                image_chunks.clear()
                image_metadata.clear()
                capture_requested = False
        
        # ===== ESTADO DEL DISPOSITIVO =====
        elif topic == TOPIC_STATUS:
            data = json.loads(msg.payload.decode())
            status = data.get('status')
            device = data.get('device')
            ip = data.get('ip')
            
            if status == "online":
                print(f"✓ {device} conectado (IP: {ip})")
    
    except json.JSONDecodeError as e:
        print(f"❌ Error decodificando JSON del topic {topic}: {e}")
        print(f"   Payload recibido: {msg.payload[:100]}")  # Mostrar primeros 100 bytes
    except Exception as e:
        print(f"❌ Error procesando mensaje del topic {topic}: {e}")
        traceback.print_exc()

def on_disconnect(client, userdata, rc):
    """Callback cuando se desconecta del broker"""
    if rc != 0:
        print(f"⚠️ Desconexión inesperada del broker (código: {rc})")
        print("🔄 Intentando reconectar...")

# ============================================
# MAIN
# ============================================

def main():
    global client
    
    print("=" * 50)
    print("🔥 Fire Monitor - Raspberry Pi Handler")
    print("=" * 50)
    
    # Crear directorios
    ensure_directories()
    
    # Configurar cliente MQTT (usar VERSION2 para evitar deprecation)
    try:
        # Intentar con API version 2 (paho-mqtt 2.x)
        client = mqtt.Client(
            client_id="RaspberryPi-FireMonitor",
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2
        )
    except AttributeError:
        # Fallback para versiones antiguas de paho-mqtt
        client = mqtt.Client(client_id="RaspberryPi-FireMonitor")
    
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    # Conectar al broker
    try:
        print(f"\n🔌 Conectando a broker MQTT en {MQTT_BROKER}:{MQTT_PORT}...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        print("\n✅ Sistema iniciado correctamente")
        print("📡 Esperando alertas de fuego...")
        print("\nPresiona Ctrl+C para detener\n")
        
        # Loop infinito
        client.loop_forever()
        
    except KeyboardInterrupt:
        print("\n\n🛑 Deteniendo sistema...")
        client.disconnect()
        print("✓ Desconectado")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()