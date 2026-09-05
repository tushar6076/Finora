import os
from kivy.clock import Clock
from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.factory import Factory

from kivymd.uix.navigationdrawer import MDNavigationDrawerItemTrailingText

from kivy.properties import StringProperty

# Local Imports
from app.models import init_db
from app.services import ExcelGenerator, ReceiptService
from app.utils.loader import (
    ensure_app_directories, 
    initialize_user_settings, 
    apply_saved_theme, 
    run_auto_export_check,
    auto_delete_bin
)
from app.utils.files import download_report, share_report, check_export_range
from app.utils.ui import show_msg, sync_nav_state

from kivy.utils import platform

if platform == 'android':
    from app.utils.android import request_permissions_for_android, set_android_status_bar

# Register M3 specific components
Factory.register('MDNavigationDrawerItemTrailingText', cls=MDNavigationDrawerItemTrailingText)

class FinoraApp(MDApp):

    def __init__(self, config_class, **kwargs):
        super().__init__(**kwargs)
        self.config_obj = config_class
        # Initialize DB session
        self.db = init_db(self.config_obj.DATABASE_URI)

        self.last_screen = StringProperty("home")
        self.excel_gen = None 

    def build(self):
        # Initial Theme Setup
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Indigo" # Or "Teal" to match the Gmail look
        self.theme_cls.material_style = "M3"

        # 1. Load all individual UI pieces first
        self.load_all_kv_files()

        # 2. Load and return the ROOT (app.kv)
        # This file now contains the MDNavigationLayout and MDScreenManager
        # as we defined in the previous step.
        BASE_DIR = os.path.abspath(os.path.dirname(__file__))
        file_path = os.path.join(BASE_DIR, 'app.kv')
        return Builder.load_file(file_path)

    def load_all_kv_files(self):
        # Load your screen-specific KV files
        # Order matters: Load widgets/styles before the main screens
        Builder.load_file("app/widgets/sidenav.kv")
        Builder.load_file("app/widgets/dropdown.kv")
        Builder.load_file("app/widgets/custom_header.kv")
        Builder.load_file("app/widgets/empty_state.kv")
        Builder.load_file("app/widgets/info_modal.kv")
        Builder.load_file("app/widgets/delete_modal.kv")
        
        Builder.load_file("app/screens/home/home.kv")
        Builder.load_file("app/screens/registration/add_entry.kv")
        Builder.load_file("app/screens/views/view_entry.kv")
        Builder.load_file("app/screens/settings/settings.kv")
        Builder.load_file("app/screens/bin/bin.kv")

    def on_start(self):
        # 0. Set Keyboard Behavior first
        from kivy.core.window import Window
        Window.softinput_mode = 'below_target'

        ensure_app_directories(self)
        self.excel_gen = ExcelGenerator(os.path.join(self.config_obj.EXPORT_DIR, 'xlsx'))
        self.pdf_gen = ReceiptService(os.path.join(self.config_obj.EXPORT_DIR, 'pdf'))
        initialize_user_settings(self)
        
        # 1. First, bind the activity
        if platform == 'android':
            from android import activity
            activity.bind(on_activity_result=self.on_activity_result)

        # 2. Apply the theme first (so self.theme_cls.theme_style is correct)
        apply_saved_theme(self)

        # 3. Now update the status bar to match that theme
        if platform == 'android':
            request_permissions_for_android(self)
            Clock.schedule_once(lambda dt: set_android_status_bar(self), 0.2)

        run_auto_export_check(self)
        auto_delete_bin(self)


    def on_stop(self):
        import shutil
        """Clean the subfolders used by Excel and PDF services."""
        # List the specific sub-directories that hold your files
        subfolders = ['xlsx', 'pdf']
        
        for sub in subfolders:
            target_path = os.path.join(self.config_obj.EXPORT_DIR, sub)
            
            try:
                if os.path.exists(target_path) and os.path.isdir(target_path):
                    # We loop through files inside 'xlsx' and 'pdf'
                    for filename in os.listdir(target_path):
                        file_path = os.path.join(target_path, filename)
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path) # Direct kill for files
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path) # Kill sub-folders if any
            except Exception as e:
                print(f"Finora: Could not clean {sub}. Error: {e}")

        # Final DB Safety Close
        if hasattr(self, 'db') and self.db:
            self.db.close()

    def sync_ui_nav(self, screen_name): sync_nav_state(self, screen_name)

    def on_activity_result(self, request_code, result_code, intent):
        if platform == 'android':
            if intent is None:
                return
            from app.utils.android import handle_saf_result
            from app.utils.ui import show_msg
            
            success, message = handle_saf_result(self, request_code, result_code, intent)
            
            if success:
                # Update UI if settings is open
                if self.root.ids.screen_manager.current == "settings":
                    settings_screen = self.root.ids.screen_manager.get_screen("settings")
                    settings_screen.ids.export_path_item.secondary_text = message
                
                show_msg(text="Default export directory set!")

    # Placeholders for Export Logic
    def download_full_report(self):
        """Main entry point for the export button"""
        records = check_export_range(self)
        if not records: return show_msg("No data available to download.")
        download_report(self, records)     

    def share_full_report(self):
        records = check_export_range(self)
        if not records: return show_msg("No data available to share.")
        share_report(self, records)