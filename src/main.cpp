#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>
#include <PubSubClient.h>
#include "base64.h"

// ==== PROTOTIPOS DE FUNCIONES ====
void callback(char* topic, byte* payload, unsigned int length);
void reconnectMQTT();
void publishStatus(const char* status);
void captureAndSendImage();
void readFlameSensor();
void publishFireAlert(bool detected);
void handle_sensor_data();
void handle_jpg_stream();
void handle_root();
void handle_jpg();
void startCameraServer();

// ==== CONFIGURA AQUÍ TU RED WiFi ====
const char* ssid = "net";
const char* password = "123456789";

// ==== MQTT Configuration ====
const char* mqtt_server = "192.168.137.72";  // IP de tu Raspberry
const int mqtt_port = 1883;
const char* mqtt_client_id = "ESP32-CAM-FireDetector";

// MQTT Topics
const char* TOPIC_ALERT = "fire/alert";
const char* TOPIC_CAPTURE_CMD = "fire/capture";
const char* TOPIC_IMAGE = "fire/image";
const char* TOPIC_STATUS = "fire/status";

// ==== Pin del sensor KY-026 ====
#define FLAME_SENSOR_PIN 13

// ==== Pines cámara OV2640 ====
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

WebServer server(80);
WiFiClient espClient;
PubSubClient mqtt(espClient);

// Variables del sensor de llama
bool flameDetected = false;
unsigned long lastFlameTime = 0;
int flameCounter = 0;
const int HISTORY_SIZE = 50;
int flameHistory[HISTORY_SIZE] = {0};
int historyIndex = 0;

// Control de tiempo
unsigned long lastSensorRead = 0;
unsigned long lastMqttPublish = 0;
const unsigned long SENSOR_INTERVAL = 250;
const unsigned long MQTT_PUBLISH_INTERVAL = 1000;

// Control de alertas (evitar spam)
bool lastAlertSent = false;

// ============================================
// FUNCIONES MQTT
// ============================================

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("📩 Mensaje recibido en [");
  Serial.print(topic);
  Serial.print("]: ");
  
  String message = "";
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.println(message);
  
  // Comando de captura desde Raspberry
  if (String(topic) == TOPIC_CAPTURE_CMD) {
    if (message == "CAPTURE") {
      Serial.println("📸 Comando de captura recibido");
      captureAndSendImage();
    }
  }
}

void reconnectMQTT() {
  while (!mqtt.connected()) {
    Serial.print("🔄 Conectando a MQTT...");
    
    if (mqtt.connect(mqtt_client_id)) {
      Serial.println(" ✓ Conectado");
      
      // Suscribirse al topic de comandos
      mqtt.subscribe(TOPIC_CAPTURE_CMD);
      Serial.println("✓ Suscrito a " + String(TOPIC_CAPTURE_CMD));
      
      // Publicar estado online
      publishStatus("online");
      
    } else {
      Serial.print(" ❌ Error: ");
      Serial.print(mqtt.state());
      Serial.println(" - Reintentando en 5s");
      delay(5000);
    }
  }
}

void publishStatus(const char* status) {
  StaticJsonDocument<128> doc;
  doc["device"] = "ESP32-CAM";
  doc["status"] = status;
  doc["ip"] = WiFi.localIP().toString();
  
  char buffer[128];
  serializeJson(doc, buffer);
  mqtt.publish(TOPIC_STATUS, buffer);
}

void captureAndSendImage() {
  Serial.println("📸 Capturando imagen...");

  sensor_t * s = esp_camera_sensor_get();
  s->set_framesize(s, FRAMESIZE_QVGA);  // 320x240 reduce el tamaño
  s->set_quality(s, 20);                 // menor calidad, menos RAM

  camera_fb_t * fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("❌ Error capturando imagen");
    return;
  }

  Serial.printf("✓ Imagen capturada: %d bytes\n", fb->len);

  // CORRECCIÓN: Chunks más pequeños para evitar problemas de memoria
  const int chunkSize = 3000;  // Reducido de 4000 a 3000
  const int totalChunks = (fb->len + chunkSize - 1) / chunkSize;

  // Metadata
  StaticJsonDocument<256> metaDoc;
  metaDoc["device"] = "ESP32-CAM";
  metaDoc["timestamp"] = millis();
  metaDoc["size"] = fb->len;
  metaDoc["width"] = fb->width;
  metaDoc["height"] = fb->height;
  metaDoc["chunks"] = totalChunks;

  char metaBuffer[256];
  serializeJson(metaDoc, metaBuffer);
  mqtt.publish("fire/image/meta", metaBuffer);
  delay(100);

  Serial.printf("📤 Enviando imagen en %d chunks...\n", totalChunks);

  for (int i = 0; i < totalChunks; i++) {
    int start = i * chunkSize;
    int len = (i == totalChunks - 1) ? fb->len - start : chunkSize;
    
    // Codificar el chunk
    String chunkB64 = base64::encode(fb->buf + start, len);
    
    Serial.printf("  Chunk %d/%d: %d bytes → %d chars Base64\n", 
                  i + 1, totalChunks, len, chunkB64.length());

    // CORRECCIÓN: DynamicJsonDocument con tamaño calculado dinámicamente
    // Tamaño necesario = overhead JSON (~100) + tamaño del string Base64
    const size_t capacity = JSON_OBJECT_SIZE(3) + chunkB64.length() + 100;
    DynamicJsonDocument doc(capacity);
    
    doc["chunk"] = i;
    doc["total"] = totalChunks;
    doc["data"] = chunkB64;

    // Verificar si el JSON se serializó correctamente
    String jsonString;
    serializeJson(doc, jsonString);
    
    if (jsonString.length() > 0) {
      if (mqtt.publish("fire/image", jsonString.c_str())) {
        Serial.printf("  ✓ Chunk %d enviado (%d bytes JSON)\n", i + 1, jsonString.length());
      } else {
        Serial.printf("  ❌ Error enviando chunk %d\n", i + 1);
      }
    } else {
      Serial.printf("  ❌ Error serializando chunk %d\n", i + 1);
    }
    
    delay(250); // Delay entre chunks
    yield();    // Evita WDT reset
  }

  esp_camera_fb_return(fb);
  s->set_framesize(s, FRAMESIZE_SVGA);
  s->set_quality(s, 10);

  Serial.println("✅ Imagen enviada completamente");
}

// ============================================
// FUNCIONES DEL SENSOR
// ============================================

void readFlameSensor() {
  int sensorValue = digitalRead(FLAME_SENSOR_PIN);
  flameDetected = (sensorValue == HIGH);
  
  flameHistory[historyIndex] = flameDetected ? 1 : 0;
  historyIndex = (historyIndex + 1) % HISTORY_SIZE;
  
  if (flameDetected) {
    lastFlameTime = millis();
    flameCounter++;
    
    if (!lastAlertSent) {
      publishFireAlert(true);
      lastAlertSent = true;
    }
    
    Serial.println("🔥 ¡LLAMA DETECTADA!");
  } else {
    if (lastAlertSent) {
      publishFireAlert(false);
      lastAlertSent = false;
    }
  }
}

void publishFireAlert(bool detected) {
  StaticJsonDocument<256> doc;
  doc["device"] = "ESP32-CAM";
  doc["alert"] = detected ? "FIRE_DETECTED" : "CLEAR";
  doc["timestamp"] = millis();
  doc["detections"] = flameCounter;
  doc["sensor_pin"] = FLAME_SENSOR_PIN;
  
  char buffer[256];
  serializeJson(doc, buffer);
  
  if (mqtt.publish(TOPIC_ALERT, buffer)) {
    Serial.println("📡 Alerta MQTT enviada: " + String(detected ? "FUEGO" : "DESPEJADO"));
  }
}

// ============================================
// FUNCIONES WEB
// ============================================

void handle_sensor_data() {
  StaticJsonDocument<512> doc;
  
  doc["flameDetected"] = flameDetected;
  doc["lastDetection"] = lastFlameTime;
  doc["detectionCount"] = flameCounter;
  doc["timeSinceLastFlame"] = millis() - lastFlameTime;
  doc["sensorPin"] = FLAME_SENSOR_PIN;
  doc["mqttConnected"] = mqtt.connected();
  
  JsonArray history = doc.createNestedArray("history");
  for (int i = 0; i < HISTORY_SIZE; i++) {
    int idx = (historyIndex + i) % HISTORY_SIZE;
    history.add(flameHistory[idx]);
  }
  
  String response;
  serializeJson(doc, response);
  
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.send(200, "application/json", response);
}

void handle_jpg_stream() {
  WiFiClient client = server.client();
  
  String response = "HTTP/1.1 200 OK\r\n";
  response += "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n\r\n";
  server.sendContent(response);
  
  Serial.println("Cliente conectado al stream");
  
  unsigned long lastFrameTime = 0;
  const unsigned long FRAME_DELAY = 100;
  
  while (client.connected()) {
    unsigned long currentMillis = millis();
    
    if (currentMillis - lastSensorRead >= SENSOR_INTERVAL) {
      lastSensorRead = currentMillis;
      readFlameSensor();
    }
    
    if (currentMillis - lastFrameTime >= FRAME_DELAY) {
      lastFrameTime = currentMillis;
      
      camera_fb_t * fb = esp_camera_fb_get();
      if (!fb) {
        Serial.println("Error capturando frame");
        continue;
      }
      
      String header = "--frame\r\n";
      header += "Content-Type: image/jpeg\r\n";
      header += "Content-Length: " + String(fb->len) + "\r\n\r\n";
      
      server.sendContent(header);
      client.write(fb->buf, fb->len);
      server.sendContent("\r\n");
      
      esp_camera_fb_return(fb);
    }
    
    delay(1);
  }
  
  Serial.println("Cliente desconectado del stream");
}

void handle_root() {
  String html = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>🔥 ESP32-CAM Fire Monitor + MQTT</title>
    <style>
        body { font-family: Arial; background: #1a1a2e; color: white; padding: 20px; }
        .status { font-size: 24px; margin: 20px 0; }
        .mqtt-connected { color: #4ade80; }
        .mqtt-disconnected { color: #f87171; }
        img { max-width: 640px; border: 2px solid #667eea; }
    </style>
</head>
<body>
    <h1>🔥 Fire Detection System + MQTT</h1>
    <div class="status" id="status">Cargando...</div>
    <img src="/stream" id="stream">
    <script>
        setInterval(() => {
            fetch('/sensor')
                .then(r => r.json())
                .then(data => {
                    const status = document.getElementById('status');
                    const mqttStatus = data.mqttConnected ? 
                        '<span class="mqtt-connected">✓ MQTT Conectado</span>' :
                        '<span class="mqtt-disconnected">✗ MQTT Desconectado</span>';
                    
                    const fireStatus = data.flameDetected ? 
                        '🔥 FUEGO DETECTADO' : '✓ Sistema Seguro';
                    
                    status.innerHTML = `${fireStatus} | ${mqttStatus} | Detecciones: ${data.detectionCount}`;
                });
        }, 500);
    </script>
</body>
</html>
)rawliteral";
  
  server.send(200, "text/html", html);
}

void handle_jpg() {
  camera_fb_t * fb = esp_camera_fb_get();
  if (!fb) {
    server.send(500, "text/plain", "Error capturando imagen");
    return;
  }
  
  server.sendHeader("Content-Disposition", "inline; filename=capture.jpg");
  server.send_P(200, "image/jpeg", (const char *)fb->buf, fb->len);
  esp_camera_fb_return(fb);
}

void startCameraServer() {
  server.on("/", HTTP_GET, handle_root);
  server.on("/stream", HTTP_GET, handle_jpg_stream);
  server.on("/capture", HTTP_GET, handle_jpg);
  server.on("/sensor", HTTP_GET, handle_sensor_data);
  
  server.begin();
  Serial.println("Servidor web iniciado");
}

// ============================================
// SETUP
// ============================================

void setup() {
  Serial.begin(115200);
  Serial.println("\n\n🔥 Iniciando ESP32-CAM Fire Monitor + MQTT...");

  pinMode(FLAME_SENSOR_PIN, INPUT);
  Serial.println("✓ Sensor KY-026 configurado en GPIO13");

  // Configurar cámara
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.grab_mode = CAMERA_GRAB_LATEST;

  if(psramFound()){
    config.frame_size = FRAMESIZE_SVGA;
    config.jpeg_quality = 10;
    config.fb_count = 2;
    config.fb_location = CAMERA_FB_IN_PSRAM;
  } else {
    config.frame_size = FRAMESIZE_CIF;
    config.jpeg_quality = 12;
    config.fb_count = 1;
    config.fb_location = CAMERA_FB_IN_DRAM;
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("❌ Error inicializando cámara: 0x%x\n", err);
    ESP.restart();
  }
  Serial.println("✓ Cámara inicializada");

  // WiFi
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  Serial.print("Conectando a WiFi");
  
  int intentos = 0;
  while (WiFi.status() != WL_CONNECTED && intentos < 20) {
    delay(500);
    Serial.print(".");
    intentos++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✓ WiFi conectado");
    Serial.print("📡 IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n❌ Error conectando a WiFi");
    ESP.restart();
  }

  // Configurar MQTT con buffer más grande
  mqtt.setServer(mqtt_server, mqtt_port);
  mqtt.setCallback(callback);
  mqtt.setBufferSize(16000);  // Aumentado de 10000 a 16000
  
  startCameraServer();
  
  Serial.println("\n=================================");
  Serial.println("🔥 Fire Monitor + MQTT listo!");
  Serial.println("Web: http://" + WiFi.localIP().toString());
  Serial.println("MQTT Broker: " + String(mqtt_server));
  Serial.println("=================================\n");
}

// ============================================
// LOOP
// ============================================

void loop() {
  if (!mqtt.connected()) {
    reconnectMQTT();
  }
  mqtt.loop();
  
  unsigned long currentMillis = millis();
  if (currentMillis - lastSensorRead >= SENSOR_INTERVAL) {
    lastSensorRead = currentMillis;
    readFlameSensor();
  }
  
  server.handleClient();
}