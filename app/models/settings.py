import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime

from . import Base

class UserSetting(Base):
    """Single-row configuration for local app persistence."""
    __tablename__ = 'user_settings'
    
    id = Column(Integer, primary_key=True, default=1)
    
    # UI Preferences
    theme_mode = Column(String(20), default="Light")
    accent_color = Column(String(20), default="Indigo")
    
    # Data & Automation
    # Changed to 'export_path' to match your settings.py logic
    export_path = Column(String(255), nullable=True) 
    auto_export_enabled = Column(Boolean, default=False)
    export_frequency = Column(String(20), default="Weekly")
    
    # NEW: Added to support the Range Dropdown
    export_range = Column(String(30), default="Full History") 
    
    last_export_date = Column(DateTime, default=datetime.datetime.now)
    
    # Sharing & Communication
    quick_share_enabled = Column(Boolean, default=False) # Matches your default False logic
    notifications_enabled = Column(Boolean, default=True)