import sqlite3
from datetime import datetime
import os

class Database:
    def __init__(self, db_path="activity_tracker.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                session_type TEXT NOT NULL,
                duration_seconds INTEGER,
                category TEXT,
                notes TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS break_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                color TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_session_start 
            ON activity_sessions(start_time)
        ''')
        
        default_categories = [
            ('Café', '#8B4513'),
            ('Almoço', '#FF6347'),
            ('Banheiro', '#4169E1'),
            ('Lanche', '#FFA500'),
            ('Pausa para descanso', '#32CD32'),
            ('Outro', '#808080')
        ]
        
        for category, color in default_categories:
            cursor.execute('''
                INSERT OR IGNORE INTO break_categories (name, color)
                VALUES (?, ?)
            ''', (category, color))
        
        conn.commit()
        conn.close()
    
    def start_session(self, session_type='active'):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO activity_sessions (start_time, session_type)
            VALUES (?, ?)
        ''', (datetime.now(), session_type))
        
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return session_id
    
    def end_session(self, session_id, category=None, notes=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        end_time = datetime.now()
        
        cursor.execute('''
            SELECT start_time FROM activity_sessions WHERE id = ?
        ''', (session_id,))
        
        result = cursor.fetchone()
        if result:
            start_time = datetime.fromisoformat(result[0])
            duration = int((end_time - start_time).total_seconds())
            
            cursor.execute('''
                UPDATE activity_sessions 
                SET end_time = ?, duration_seconds = ?, category = ?, notes = ?
                WHERE id = ?
            ''', (end_time, duration, category, notes, session_id))
        
        conn.commit()
        conn.close()
    
    def update_session_category(self, session_id, category, notes=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE activity_sessions 
            SET category = ?, notes = ?
            WHERE id = ?
        ''', (category, notes, session_id))
        
        conn.commit()
        conn.close()
    
    def get_sessions(self, start_date=None, end_date=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = 'SELECT * FROM activity_sessions WHERE 1=1'
        params = []
        
        if start_date:
            query += ' AND start_time >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND start_time <= ?'
            params.append(end_date)
        
        query += ' ORDER BY start_time DESC'
        
        cursor.execute(query, params)
        sessions = cursor.fetchall()
        conn.close()
        return sessions
    
    def get_statistics(self, start_date=None, end_date=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT 
                session_type,
                category,
                SUM(duration_seconds) as total_seconds,
                COUNT(*) as count
            FROM activity_sessions 
            WHERE end_time IS NOT NULL
        '''
        params = []
        
        if start_date:
            query += ' AND start_time >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND start_time <= ?'
            params.append(end_date)
        
        query += ' GROUP BY session_type, category'
        
        cursor.execute(query, params)
        stats = cursor.fetchall()
        conn.close()
        return stats
    
    def get_break_categories(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT name, color FROM break_categories ORDER BY name')
        categories = cursor.fetchall()
        conn.close()
        return categories
    
    def get_uncategorized_breaks(self, limit=10):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, start_time, end_time, duration_seconds
            FROM activity_sessions
            WHERE session_type = 'idle' 
            AND category IS NULL
            AND end_time IS NOT NULL
            ORDER BY start_time DESC
            LIMIT ?
        ''', (limit,))
        
        breaks = cursor.fetchall()
        conn.close()
        return breaks
