import ctypes
from ctypes import Structure, windll, c_uint, sizeof, byref

class LASTINPUTINFO(Structure):
    _fields_ = [
        ('cbSize', c_uint),
        ('dwTime', c_uint),
    ]

class IdleDetector:
    def __init__(self, idle_threshold_seconds=60):
        self.idle_threshold = idle_threshold_seconds * 1000
    
    def get_idle_duration(self):
        lastInputInfo = LASTINPUTINFO()
        lastInputInfo.cbSize = sizeof(lastInputInfo)
        windll.user32.GetLastInputInfo(byref(lastInputInfo))
        millis = windll.kernel32.GetTickCount() - lastInputInfo.dwTime
        return millis / 1000.0
    
    def is_idle(self):
        return self.get_idle_duration() >= (self.idle_threshold / 1000.0)
    
    def set_threshold(self, seconds):
        self.idle_threshold = seconds * 1000
