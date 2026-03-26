import os
from app.models import UserSetting

def ensure_app_directories(app):
    """Ensures the export folder exists on the device."""
    export_path = app.config_obj.EXPORT_DIR
    if not os.path.exists(export_path):
        os.makedirs(export_path, exist_ok=True)

def initialize_user_settings(app):
    """Creates a default settings row if the database is empty."""
    settings = app.db.query(UserSetting).first()
    if not settings:
        new_settings = UserSetting()
        app.db.add(new_settings)
        app.db.commit()

def apply_saved_theme(app):
    """Reads the DB and sets the app theme accordingly."""
    settings = app.db.query(UserSetting).first()
    if settings:
        app.theme_cls.theme_style = settings.theme_mode
        app.theme_cls.primary_palette = settings.accent_color