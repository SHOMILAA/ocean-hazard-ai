import sqlite3
from datetime import datetime
import os

DB_NAME = "alerts.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Create new table with all updated columns
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text_content TEXT,
            image_path TEXT,
            hazard_type TEXT,
            fake_or_real TEXT,
            confidence REAL,
            timestamp TEXT,
            location TEXT,
            lat TEXT,
            lng TEXT,
            severity TEXT
        )
    ''')
    
    # Simple migration hook to add missing columns to an existing database
    cursor.execute("PRAGMA table_info(alerts)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if "location" not in columns:
        cursor.execute("ALTER TABLE alerts ADD COLUMN location TEXT")
    if "lat" not in columns:
        cursor.execute("ALTER TABLE alerts ADD COLUMN lat TEXT")
    if "lng" not in columns:
        cursor.execute("ALTER TABLE alerts ADD COLUMN lng TEXT")
    if "severity" not in columns:
        cursor.execute("ALTER TABLE alerts ADD COLUMN severity TEXT")
        
    conn.commit()
    conn.close()

def insert_alert(text_content, image_path, hazard_type, fake_or_real, confidence, location, lat, lng, severity):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO alerts (text_content, image_path, hazard_type, fake_or_real, confidence, timestamp, location, lat, lng, severity)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (text_content, image_path, hazard_type, fake_or_real, confidence, timestamp, location, lat, lng, severity))
    conn.commit()
    conn.close()

def get_all_alerts():
    if not os.path.exists(DB_NAME):
        return []
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM alerts ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
