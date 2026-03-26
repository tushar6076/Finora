import os
import shutil
import datetime
from kivy.utils import platform
from app.models import UserSetting

from app.utils.files.helpers import win_file_chooser
from app.utils.ui import show_msg

from plyer import notification

if platform == 'android':
    from app.utils.android.notification import android_notify
    from app.utils.android.helpers import save_to_authorized_uri, open_file_chooser
    from app.utils.android import share_file_android


def download_report(app, records, is_auto=False):
    """
    Unified Export Logic: Saves to the directory in settings.
    Automatically switches between PDF (Single) and XLSX (Bulk).
    """
    try:
        if not records:
            show_msg("No records found to export.", status='error')
            return

        # 1. Generate the File
        if len(records) == 1:
            # FIX: Pass records[0] (the object), not records (the list)
            temp_path = app.pdf_gen.generate_receipt(records[0])
        else:
            # XLSX generator usually handles lists, so this is fine
            temp_path = app.excel_gen.generate_report(records)

        filename = os.path.basename(temp_path)
        settings = app.db.query(UserSetting).first()

        # 2. Android Storage Logic
        if platform == 'android':
            if settings.export_path:
                # Save silently to the authorized URI
                save_to_authorized_uri(temp_path, settings.export_path, filename)
            else:
                # Trigger SAF Picker and save path for next time
                app.current_temp_file = temp_path
                app.current_filename = filename
                open_file_chooser()
        else:
            if settings.export_path:
                shutil.copy(temp_path, settings.export_path)
                os.remove(temp_path)
            else:
                app.current_temp_file = temp_path
                app.current_filename = filename
                win_file_chooser()

        # 3. Metadata & Feedback
        settings.last_export_date = datetime.datetime.now()
        app.db.commit()

        if not is_auto:
            # Using your hex code for success (light green)
            show_msg(text=f"Exported: {filename}", status='success')

        if settings.notifications_enabled:
            if platform == 'android':
                android_notify(
                    title="Finora: Report Saved",
                    message=f"Check your {os.path.basename(settings.export_path or 'storage')}"
                )
            else:
                notification.notify(
                    title="Finora: Report Saved",
                    message=f"Check your {os.path.basename(settings.export_path or 'storage')}",
                    app_name="Finora"
                )

    except Exception as e:
        print(f"Unified Export Error: {e}")
        show_msg(text=f"Export Error: {str(e)}", status='error')

def share_report(app, records):
    """Generates the file and opens the native Android share sheet."""
    if not records: 
        return
    
    # Generate the file
    if len(records) == 1:
        temp_path = app.pdf_gen.generate_receipt(records[0])
    else:
        temp_path = app.excel_gen.generate_report(records)
    
    if not temp_path or not os.path.exists(temp_path):
        return

    if platform == 'android':
        # Use our native helper instead of plyer
        share_file_android(temp_path, title="Share Transaction Report")
    else:
        # Desktop behavior
        if os.name == 'nt':
            os.startfile(temp_path)
        else:
            os.system(f'open "{temp_path}"')