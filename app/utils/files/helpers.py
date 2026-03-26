import os
import shutil
from kivymd.app import MDApp
from app.models import UserSetting
from plyer import filechooser, notification

def win_file_chooser():
    def callback(selection):
        if not selection: 
            return
            
        folder_path = selection[0]
        app = MDApp.get_running_app()
        
        # Use a context manager if you're using SQLAlchemy directly 
        # or app.db if it's already initialized
        settings = app.db.query(UserSetting).first()
        
        if settings:
            settings.export_path = folder_path
            app.db.commit()

            temp_path = getattr(app, 'current_temp_file', "")
            filename = getattr(app, 'current_filename', "Finora_Report.xlsx")
            
            if temp_path and os.path.exists(temp_path):
                dest_path = os.path.join(folder_path, filename)
                shutil.copy(temp_path, dest_path)
                os.remove(temp_path)
                if settings.notifications_enabled:
                    notification.notify(
                        title="Finora: Report Saved",
                        message=f"Check your {os.path.basename(settings.export_path or 'storage')}",
                        app_name="Finora"
                    )
                    return True
        return False
    
    filechooser.choose_dir(title="Select Export Folder", on_selection=callback)