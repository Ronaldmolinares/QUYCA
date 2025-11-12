#!/usr/bin/env python3
"""
Fire Monitor - Database Handler
Maneja todas las operaciones de base de datos SQLite
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import os

class FireMonitorDB:
    def __init__(self, db_path: str = "/home/pi/fire_monitor/fire_monitor.db"):
        """Inicializar conexión a la base de datos"""
        self.db_path = db_path
        self.ensure_directory()
        self.init_database()
    
    def ensure_directory(self):
        """Crear directorio de la base de datos si no existe"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def get_connection(self) -> sqlite3.Connection:
        """Obtener conexión a la base de datos"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Permite acceso por nombre de columna
        return conn
    
    def init_database(self):
        """Inicializar base de datos con el schema"""
        with open('/home/pi/fire_monitor/schema.sql', 'r') as f:
            schema = f.read()
        
        conn = self.get_connection()
        try:
            conn.executescript(schema)
            conn.commit()
            print("✓ Base de datos inicializada")
        except Exception as e:
            print(f"❌ Error inicializando base de datos: {e}")
        finally:
            conn.close()
    
    # ============================================
    # DETECCIONES
    # ============================================
    
    def insert_detection(self, detected: bool, sensor_type: str = 'KY-026', 
                        esp32_millis: int = None, confidence: int = 100) -> int:
        """Registrar una detección del sensor"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('''
                INSERT INTO fire_detections 
                (sensor_type, detected, confidence, esp32_millis)
                VALUES (?, ?, ?, ?)
            ''', (sensor_type, detected, confidence, esp32_millis))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    
    def get_recent_detections(self, limit: int = 100) -> List[Dict]:
        """Obtener detecciones recientes"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('''
                SELECT * FROM fire_detections 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def get_detections_by_date(self, date: str) -> List[Dict]:
        """Obtener detecciones de una fecha específica (YYYY-MM-DD)"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('''
                SELECT * FROM fire_detections 
                WHERE DATE(timestamp) = ?
                ORDER BY timestamp DESC
            ''', (date,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    # ============================================
    # ALERTAS
    # ============================================
    
    def create_alert(self, detection_id: int, alert_type: str, 
                    severity: str = 'MEDIUM', detections_count: int = 1) -> int:
        """Crear una nueva alerta"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('''
                INSERT INTO alerts 
                (detection_id, alert_type, severity, detections_count, status)
                VALUES (?, ?, ?, ?, 'ACTIVE')
            ''', (detection_id, alert_type, severity, detections_count))
            conn.commit()
            alert_id = cursor.lastrowid
            
            # Log
            self.log('INFO', 'ALERT', f'Alerta creada: {alert_type} (ID: {alert_id})')
            return alert_id
        finally:
            conn.close()
    
    def get_active_alert(self) -> Optional[Dict]:
        """Obtener la alerta activa actual (si existe)"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('''
                SELECT * FROM alerts 
                WHERE status = 'ACTIVE' 
                ORDER BY created_at DESC 
                LIMIT 1
            ''')
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    
    def get_alert_by_id(self, alert_id: int) -> Optional[Dict]:
        """Obtener una alerta específica por ID"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('''
                SELECT a.*, d.timestamp as detection_time
                FROM alerts a
                LEFT JOIN fire_detections d ON a.detection_id = d.id
                WHERE a.id = ?
            ''', (alert_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    
    def update_alert_detections(self, alert_id: int, detections_count: int):
        """Actualizar contador de detecciones de una alerta"""
        conn = self.get_connection()
        try:
            conn.execute('''
                UPDATE alerts 
                SET detections_count = ?
                WHERE id = ?
            ''', (detections_count, alert_id))
            conn.commit()
        finally:
            conn.close()
    
    def resolve_alert(self, alert_id: int, status: str = 'RESOLVED'):
        """Resolver una alerta activa"""
        conn = self.get_connection()
        try:
            conn.execute('''
                UPDATE alerts 
                SET status = ?, resolved_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, alert_id))
            conn.commit()
            
            # Log
            self.log('INFO', 'ALERT', f'Alerta {alert_id} resuelta: {status}')
        finally:
            conn.close()
    
    def get_alerts(self, status: str = None, limit: int = 50) -> List[Dict]:
        """Obtener alertas (filtradas por estado opcional)"""
        conn = self.get_connection()
        try:
            if status:
                cursor = conn.execute('''
                    SELECT * FROM alerts 
                    WHERE status = ?
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (status, limit))
            else:
                cursor = conn.execute('''
                    SELECT * FROM alerts 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    # ============================================
    # IMÁGENES
    # ============================================
    
    def save_image_record(self, alert_id: int, file_path: str, file_name: str,
                         image_size: int, width: int, height: int, 
                         chunks_total: int = 1, trigger: str = 'AUTO') -> int:
        """Guardar registro de imagen capturada"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('''
                INSERT INTO captured_images 
                (alert_id, file_path, file_name, image_size_bytes, 
                 width, height, chunks_total, capture_trigger)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (alert_id, file_path, file_name, image_size, 
                  width, height, chunks_total, trigger))
            conn.commit()
            
            # Log
            self.log('INFO', 'CAMERA', f'Imagen guardada: {file_name} ({image_size} bytes)')
            return cursor.lastrowid
        finally:
            conn.close()
    
    def get_images_by_alert(self, alert_id: int) -> List[Dict]:
        """Obtener todas las imágenes de una alerta"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('''
                SELECT * FROM captured_images 
                WHERE alert_id = ?
                ORDER BY capture_time DESC
            ''', (alert_id,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def get_recent_images(self, limit: int = 20) -> List[Dict]:
        """Obtener imágenes recientes"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('''
                SELECT ci.*, a.alert_type, a.severity 
                FROM captured_images ci
                LEFT JOIN alerts a ON ci.alert_id = a.id
                ORDER BY ci.capture_time DESC 
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def delete_old_images(self, days: int = 30) -> int:
        """Eliminar registros de imágenes antiguas"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('''
                DELETE FROM captured_images 
                WHERE capture_time < datetime('now', '-' || ? || ' days')
            ''', (days,))
            conn.commit()
            deleted = cursor.rowcount
            
            if deleted > 0:
                self.log('INFO', 'DATABASE', f'Eliminados {deleted} registros de imágenes antiguas')
            
            return deleted
        finally:
            conn.close()
    
    # ============================================
    # DISPOSITIVOS
    # ============================================
    
    def update_device_status(self, device_id: str, status: str, 
                            ip_address: str = None, uptime: int = None):
        """Actualizar estado de un dispositivo"""
        conn = self.get_connection()
        try:
            conn.execute('''
                INSERT INTO device_status 
                (device_id, status, ip_address, uptime_seconds)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(device_id) DO UPDATE SET
                    status = excluded.status,
                    ip_address = excluded.ip_address,
                    uptime_seconds = excluded.uptime_seconds,
                    last_seen = CURRENT_TIMESTAMP
            ''', (device_id, status, ip_address, uptime))
            conn.commit()
        finally:
            conn.close()
    
    def get_device_status(self, device_id: str) -> Optional[Dict]:
        """Obtener estado de un dispositivo"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('''
                SELECT * FROM device_status 
                WHERE device_id = ?
            ''', (device_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    
    # ============================================
    # LOGS
    # ============================================
    
    def log(self, level: str, component: str, message: str, details: Dict = None):
        """Registrar un log del sistema"""
        conn = self.get_connection()
        try:
            details_json = json.dumps(details) if details else None
            conn.execute('''
                INSERT INTO system_logs 
                (log_level, component, message, details)
                VALUES (?, ?, ?, ?)
            ''', (level, component, message, details_json))
            conn.commit()
        finally:
            conn.close()
    
    def get_logs(self, level: str = None, component: str = None, 
                 limit: int = 100) -> List[Dict]:
        """Obtener logs del sistema"""
        conn = self.get_connection()
        try:
            query = 'SELECT * FROM system_logs WHERE 1=1'
            params = []
            
            if level:
                query += ' AND log_level = ?'
                params.append(level)
            
            if component:
                query += ' AND component = ?'
                params.append(component)
            
            query += ' ORDER BY timestamp DESC LIMIT ?'
            params.append(limit)
            
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def delete_old_logs(self, days: int = 7) -> int:
        """Eliminar logs antiguos"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('''
                DELETE FROM system_logs 
                WHERE timestamp < datetime('now', '-' || ? || ' days')
            ''', (days,))
            conn.commit()
            deleted = cursor.rowcount
            
            if deleted > 0:
                self.log('INFO', 'DATABASE', f'Eliminados {deleted} logs antiguos')
            
            return deleted
        finally:
            conn.close()
    
    # ============================================
    # CONFIGURACIÓN
    # ============================================
    
    def get_config(self, key: str) -> Optional[str]:
        """Obtener valor de configuración"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('''
                SELECT value, value_type FROM system_config 
                WHERE key = ?
            ''', (key,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            value, value_type = row
            
            # Convertir según el tipo
            if value_type == 'integer':
                return int(value)
            elif value_type == 'boolean':
                return value.lower() == 'true'
            elif value_type == 'json':
                return json.loads(value)
            elif value_type == 'float':
                return float(value)
            else:
                return value
        finally:
            conn.close()
    
    def set_config(self, key: str, value, value_type: str = 'string', 
                   description: str = None):
        """Establecer valor de configuración"""
        conn = self.get_connection()
        try:
            # Convertir valor a string según tipo
            if value_type == 'json':
                value_str = json.dumps(value)
            elif value_type == 'boolean':
                value_str = 'true' if value else 'false'
            else:
                value_str = str(value)
            
            conn.execute('''
                INSERT INTO system_config (key, value, value_type, description)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = CURRENT_TIMESTAMP
            ''', (key, value_str, value_type, description))
            conn.commit()
        finally:
            conn.close()
    
    # ============================================
    # ESTADÍSTICAS
    # ============================================
    
    def get_today_stats(self) -> Dict:
        """Obtener estadísticas de hoy"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('SELECT * FROM today_statistics')
            row = cursor.fetchone()
            return dict(row) if row else {}
        finally:
            conn.close()
    
    def get_system_status(self) -> Dict:
        """Obtener estado general del sistema"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('SELECT * FROM system_status')
            row = cursor.fetchone()
            return dict(row) if row else {}
        finally:
            conn.close()
    
    def update_daily_statistics(self):
        """Actualizar estadísticas del día actual"""
        conn = self.get_connection()
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            cursor = conn.execute('''
                SELECT 
                    COUNT(DISTINCT CASE WHEN detected = 1 THEN id END) as detections,
                    (SELECT COUNT(*) FROM alerts WHERE DATE(created_at) = ?) as alerts,
                    (SELECT COUNT(*) FROM captured_images WHERE DATE(capture_time) = ?) as images
                FROM fire_detections
                WHERE DATE(timestamp) = ?
            ''', (today, today, today))
            
            row = cursor.fetchone()
            
            conn.execute('''
                INSERT INTO daily_statistics 
                (date, total_detections, total_alerts, images_captured)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(date) DO UPDATE SET
                    total_detections = excluded.total_detections,
                    total_alerts = excluded.total_alerts,
                    images_captured = excluded.images_captured
            ''', (today, row['detections'], row['alerts'], row['images']))
            conn.commit()
        finally:
            conn.close()
    
    def get_statistics_range(self, days: int = 7) -> List[Dict]:
        """Obtener estadísticas de los últimos N días"""
        conn = self.get_connection()
        try:
            cursor = conn.execute('''
                SELECT * FROM daily_statistics 
                WHERE date >= date('now', '-' || ? || ' days')
                ORDER BY date DESC
            ''', (days,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    # ============================================
    # UTILIDADES
    # ============================================
    
    def cleanup_database(self):
        """Limpieza de datos antiguos según configuración"""
        image_retention = self.get_config('image_retention_days') or 30
        log_retention = self.get_config('log_retention_days') or 7
        
        deleted_images = self.delete_old_images(image_retention)
        deleted_logs = self.delete_old_logs(log_retention)
        
        return {
            'images_deleted': deleted_images,
            'logs_deleted': deleted_logs
        }
    
    def vacuum(self):
        """Optimizar base de datos (VACUUM)"""
        conn = self.get_connection()
        try:
            conn.execute('VACUUM')
            self.log('INFO', 'DATABASE', 'Base de datos optimizada (VACUUM)')
        finally:
            conn.close()
    
    def get_database_size(self) -> int:
        """Obtener tamaño de la base de datos en bytes"""
        return os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
    
    def export_to_json(self, output_path: str, days: int = 7) -> bool:
        """Exportar datos a JSON"""
        try:
            data = {
                'export_date': datetime.now().isoformat(),
                'detections': self.get_recent_detections(limit=1000),
                'alerts': self.get_alerts(limit=100),
                'images': self.get_recent_images(limit=100),
                'statistics': self.get_statistics_range(days)
            }
            
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            self.log('INFO', 'DATABASE', f'Datos exportados a {output_path}')
            return True
        except Exception as e:
            self.log('ERROR', 'DATABASE', f'Error exportando datos: {e}')
            return False