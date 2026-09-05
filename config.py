import os
from kivy.utils import platform

class Config:
    """Base Configuration for Finora"""
    APP_NAME = "Finora"
    DB_NAME = "finora.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Financial Report Constants
    REPORT_PREFIX = "Finora_Report"
    BACKUP_PREFIX = "Finora_Auto_Backup"

class DevelopmentConfig(Config):
    """Local Desktop Development (macOS/Windows/Linux)"""
    def __init__(self):
        self.DEBUG = True
        # Path to the root of your project
        self.BASE_DIR = os.path.abspath(os.path.dirname(__file__))
        
        # Database sits in the project root for easy access during dev
        self.DB_PATH = os.path.join(self.BASE_DIR, Config.DB_NAME)
        self.DATABASE_URI = f"sqlite:///{self.DB_PATH}"
        
        # Internal staging for exports inside the project
        self.EXPORT_DIR = os.path.join(self.BASE_DIR, "app", "exports")

class AndroidConfig(Config):
    """Android Production (Scoped Storage Compliant)"""
    def __init__(self):
        self.DEBUG = False
        
        # This is the trick: only import when running ON the device
        try:
            from android.storage import app_storage_path
            self.INTERNAL_DATA = app_storage_path()
        except (ImportError, ModuleNotFoundError):
            # Fallback for when you accidentally run AndroidConfig on Mac
            self.INTERNAL_DATA = os.path.join(os.path.expanduser("~"), "Finora_AppData")
        
        # Database & Staging
        self.DB_PATH = os.path.join(self.INTERNAL_DATA, Config.DB_NAME)
        self.DATABASE_URI = f"sqlite:///{self.DB_PATH}"
        self.EXPORT_DIR = os.path.join(self.INTERNAL_DATA, "cache")

class IOSConfig(Config):
    """iOS Production (Sandbox Compliant)"""
    def __init__(self):
        self.DEBUG = False
        # iOS Documents folder within the app sandbox
        self.DOC_DIR = os.path.expanduser('~/Documents')
        
        self.DB_PATH = os.path.join(self.DOC_DIR, Config.DB_NAME)
        self.DATABASE_URI = f"sqlite:///{self.DB_PATH}"
        
        # Staging for exports
        self.EXPORT_DIR = os.path.join(self.DOC_DIR, "Exports")

def get_config():
    """Returns an INSTANCE of the platform-specific config."""
    if platform == 'android':
        return AndroidConfig() # Note the parentheses ()
    elif platform == 'ios':
        # You'd implement IOSConfig similarly if needed
        return DevelopmentConfig() 
    else:
        return DevelopmentConfig()