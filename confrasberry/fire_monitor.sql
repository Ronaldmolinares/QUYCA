-- ============================================
-- Fire Monitor Database Schema
-- SQLite Database for Raspberry Pi
-- ============================================

-- Tabla de detecciones de fuego (sensor data)
CREATE TABLE IF NOT EXISTS fire_detections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_type TEXT NOT NULL DEFAULT 'KY-026',
    detected BOOLEAN NOT NULL,
    confidence INTEGER DEFAULT 100,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    esp32_millis INTEGER,
    sensor_pin INTEGER DEFAULT 13,
    CONSTRAINT chk_confidence CHECK (confidence >= 0 AND confidence <= 100)
);

-- Índice para consultas por fecha
CREATE INDEX IF NOT EXISTS idx_fire_detections_timestamp ON fire_detections(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_fire_detections_detected ON fire_detections(detected, timestamp);

-- Tabla de alertas (eventos de fuego agrupados)
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    detection_id INTEGER,
    alert_type TEXT NOT NULL,  -- 'FIRE_DETECTED', 'CLEAR', 'FALSE_ALARM'
    severity TEXT DEFAULT 'MEDIUM', -- 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    status TEXT DEFAULT 'ACTIVE', -- 'ACTIVE', 'RESOLVED', 'ACKNOWLEDGED'
    detections_count INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME,
    duration_seconds INTEGER,
    notification_sent BOOLEAN DEFAULT 0,
    notification_sent_at DATETIME,
    notes TEXT,
    FOREIGN KEY (detection_id) REFERENCES fire_detections(id) ON DELETE SET NULL,
    CONSTRAINT chk_alert_type CHECK (alert_type IN ('FIRE_DETECTED', 'CLEAR', 'FALSE_ALARM')),
    CONSTRAINT chk_severity CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    CONSTRAINT chk_status CHECK (status IN ('ACTIVE', 'RESOLVED', 'ACKNOWLEDGED', 'FALSE_ALARM'))
);

-- Índices para alertas
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts(created_at DESC);

-- Tabla de imágenes capturadas
CREATE TABLE IF NOT EXISTS captured_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id INTEGER,
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    capture_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    image_size_bytes INTEGER,
    width INTEGER,
    height INTEGER,
    chunks_total INTEGER DEFAULT 1,
    capture_trigger TEXT DEFAULT 'AUTO', -- 'AUTO', 'MANUAL', 'SCHEDULED'
    processed BOOLEAN DEFAULT 0,
    FOREIGN KEY (alert_id) REFERENCES alerts(id) ON DELETE CASCADE,
    CONSTRAINT chk_capture_trigger CHECK (capture_trigger IN ('AUTO', 'MANUAL', 'SCHEDULED'))
);

-- Índices para imágenes
CREATE INDEX IF NOT EXISTS idx_images_alert ON captured_images(alert_id);
CREATE INDEX IF NOT EXISTS idx_images_capture_time ON captured_images(capture_time DESC);
CREATE INDEX IF NOT EXISTS idx_images_trigger ON captured_images(capture_trigger);

-- Tabla de estado de dispositivos
CREATE TABLE IF NOT EXISTS device_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT UNIQUE NOT NULL,
    device_type TEXT DEFAULT 'ESP32-CAM',
    status TEXT DEFAULT 'offline', -- 'online', 'offline', 'error'
    ip_address TEXT,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    uptime_seconds INTEGER DEFAULT 0,
    firmware_version TEXT,
    rssi INTEGER, -- WiFi signal strength
    free_heap INTEGER, -- Free memory
    CONSTRAINT chk_device_status CHECK (status IN ('online', 'offline', 'error', 'maintenance'))
);

-- Índice para dispositivos
CREATE UNIQUE INDEX IF NOT EXISTS idx_device_id ON device_status(device_id);

-- Tabla de logs del sistema
CREATE TABLE IF NOT EXISTS system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_level TEXT NOT NULL, -- 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    component TEXT NOT NULL, -- 'ESP32', 'MQTT', 'WEB', 'PYTHON', 'CAMERA'
    message TEXT NOT NULL,
    details TEXT, -- JSON string con información adicional
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_log_level CHECK (log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'))
);

-- Índices para logs
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON system_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_logs_level ON system_logs(log_level, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_logs_component ON system_logs(component, timestamp DESC);

-- Tabla de configuración del sistema
CREATE TABLE IF NOT EXISTS system_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    value_type TEXT DEFAULT 'string', -- 'string', 'integer', 'boolean', 'json'
    description TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_value_type CHECK (value_type IN ('string', 'integer', 'boolean', 'json', 'float'))
);

-- Índice para configuración
CREATE UNIQUE INDEX IF NOT EXISTS idx_config_key ON system_config(key);

-- Tabla de estadísticas diarias (para analytics)
CREATE TABLE IF NOT EXISTS daily_statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE UNIQUE NOT NULL,
    total_detections INTEGER DEFAULT 0,
    total_alerts INTEGER DEFAULT 0,
    false_alarms INTEGER DEFAULT 0,
    images_captured INTEGER DEFAULT 0,
    avg_response_time_ms INTEGER,
    system_uptime_seconds INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Índice para estadísticas
CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_statistics(date DESC);

-- ============================================
-- TRIGGERS para mantener integridad
-- ============================================

-- Trigger: Calcular duración cuando se resuelve una alerta
CREATE TRIGGER IF NOT EXISTS calculate_alert_duration
AFTER UPDATE OF resolved_at ON alerts
WHEN NEW.resolved_at IS NOT NULL AND OLD.resolved_at IS NULL
BEGIN
    UPDATE alerts 
    SET duration_seconds = (
        CAST((julianday(NEW.resolved_at) - julianday(NEW.created_at)) * 86400 AS INTEGER)
    )
    WHERE id = NEW.id;
END;

-- Trigger: Actualizar timestamp de device_status
CREATE TRIGGER IF NOT EXISTS update_device_last_seen
AFTER UPDATE ON device_status
FOR EACH ROW
BEGIN
    UPDATE device_status 
    SET last_seen = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

-- Trigger: Actualizar timestamp de system_config
CREATE TRIGGER IF NOT EXISTS update_config_timestamp
AFTER UPDATE ON system_config
FOR EACH ROW
BEGIN
    UPDATE system_config 
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

-- ============================================
-- VISTAS para consultas comunes
-- ============================================

-- Vista: Alertas activas con información de imágenes
CREATE VIEW IF NOT EXISTS active_alerts_with_images AS
SELECT 
    a.id,
    a.alert_type,
    a.severity,
    a.status,
    a.detections_count,
    a.created_at,
    a.resolved_at,
    a.duration_seconds,
    COUNT(ci.id) as images_count,
    MAX(ci.capture_time) as last_image_time,
    GROUP_CONCAT(ci.file_name) as image_files
FROM alerts a
LEFT JOIN captured_images ci ON a.id = ci.alert_id
WHERE a.status = 'ACTIVE'
GROUP BY a.id
ORDER BY a.created_at DESC;

-- Vista: Estadísticas de hoy
CREATE VIEW IF NOT EXISTS today_statistics AS
SELECT 
    DATE('now') as today,
    COUNT(DISTINCT CASE WHEN fd.detected = 1 THEN fd.id END) as detections_today,
    COUNT(DISTINCT a.id) as alerts_today,
    COUNT(DISTINCT ci.id) as images_today,
    MAX(fd.timestamp) as last_detection
FROM fire_detections fd
LEFT JOIN alerts a ON DATE(a.created_at) = DATE('now')
LEFT JOIN captured_images ci ON DATE(ci.capture_time) = DATE('now')
WHERE DATE(fd.timestamp) = DATE('now');

-- Vista: Estado del sistema
CREATE VIEW IF NOT EXISTS system_status AS
SELECT 
    (SELECT COUNT(*) FROM alerts WHERE status = 'ACTIVE') as active_alerts,
    (SELECT COUNT(*) FROM device_status WHERE status = 'online') as online_devices,
    (SELECT COUNT(*) FROM captured_images WHERE DATE(capture_time) = DATE('now')) as images_today,
    (SELECT COUNT(*) FROM fire_detections WHERE detected = 1 AND DATE(timestamp) = DATE('now')) as detections_today,
    (SELECT MAX(timestamp) FROM fire_detections) as last_activity;

-- ============================================
-- DATOS INICIALES
-- ============================================

-- Configuración inicial del sistema
INSERT OR IGNORE INTO system_config (key, value, value_type, description) VALUES
('alert_threshold', '3', 'integer', 'Número de detecciones consecutivas para generar alerta'),
('auto_capture_enabled', 'true', 'boolean', 'Captura automática al detectar fuego'),
('notification_email', '', 'string', 'Email para notificaciones'),
('notification_enabled', 'false', 'boolean', 'Activar notificaciones por email'),
('image_retention_days', '30', 'integer', 'Días para mantener imágenes antiguas'),
('log_retention_days', '7', 'integer', 'Días para mantener logs'),
('mqtt_broker', 'localhost:1883', 'string', 'Dirección del broker MQTT'),
('web_port', '3000', 'integer', 'Puerto del servidor web'),
('sensor_read_interval_ms', '100', 'integer', 'Intervalo de lectura del sensor (ms)'),
('camera_quality', '20', 'integer', 'Calidad JPEG de la cámara (0-63)');

-- Registrar dispositivo ESP32-CAM
INSERT OR IGNORE INTO device_status (device_id, device_type, status) VALUES
('ESP32-CAM', 'ESP32-CAM', 'offline');

-- Log inicial
INSERT INTO system_logs (log_level, component, message) VALUES
('INFO', 'DATABASE', 'Base de datos inicializada correctamente');

-- ============================================
-- ÍNDICES ADICIONALES PARA PERFORMANCE
-- ============================================

-- Índice compuesto para búsquedas complejas
CREATE INDEX IF NOT EXISTS idx_detections_datetime_detected 
ON fire_detections(DATE(timestamp), detected);

-- Índice para alertas activas con imágenes
CREATE INDEX IF NOT EXISTS idx_images_alert_time 
ON captured_images(alert_id, capture_time DESC);