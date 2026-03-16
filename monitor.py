import time
import threading
from idle_detector import IdleDetector
from database import Database
from datetime import datetime

class ActivityMonitor:
    def __init__(self, idle_threshold=60, callback=None):
        self.idle_detector = IdleDetector(idle_threshold)
        self.database = Database()
        self.current_session_id = None
        self.is_running = False
        self.is_idle_state = False
        self.monitor_thread = None
        self.callback = callback
        self.check_interval = 5
    
    def start_monitoring(self):
        if self.is_running:
            return
        
        self.is_running = True
        self.current_session_id = self.database.start_session('active')
        self.is_idle_state = False
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        if self.callback:
            self.callback('active', self.current_session_id)
    
    def stop_monitoring(self):
        self.is_running = False
        if self.current_session_id:
            self.database.end_session(self.current_session_id)
            self.current_session_id = None
    
    def _monitor_loop(self):
        while self.is_running:
            is_currently_idle = self.idle_detector.is_idle()
            
            if is_currently_idle and not self.is_idle_state:
                if self.current_session_id:
                    self.database.end_session(self.current_session_id)
                
                self.current_session_id = self.database.start_session('idle')
                self.is_idle_state = True
                
                if self.callback:
                    self.callback('idle', self.current_session_id)
            
            elif not is_currently_idle and self.is_idle_state:
                if self.current_session_id:
                    self.database.end_session(self.current_session_id)
                
                self.current_session_id = self.database.start_session('active')
                self.is_idle_state = False
                
                if self.callback:
                    self.callback('active', self.current_session_id)
            
            time.sleep(self.check_interval)
    
    def categorize_last_break(self, category, notes=None):
        uncategorized = self.database.get_uncategorized_breaks(limit=1)
        if uncategorized:
            session_id = uncategorized[0][0]
            self.database.update_session_category(session_id, category, notes)
            return True
        return False
    
    def categorize_break_by_id(self, session_id, category, notes=None):
        self.database.update_session_category(session_id, category, notes)
    
    def set_idle_threshold(self, seconds):
        self.idle_detector.set_threshold(seconds)
    
    def get_current_state(self):
        return 'idle' if self.is_idle_state else 'active'
    
    def get_idle_duration(self):
        return self.idle_detector.get_idle_duration()
