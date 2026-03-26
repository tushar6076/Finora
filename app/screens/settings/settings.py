from kivy.utils import platform
from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import (
    MDDialog, MDDialogHeadlineText, MDDialogSupportingText, 
    MDDialogButtonContainer, MDDialogContentContainer
)
from kivymd.uix.button import MDButton, MDButtonText
from kivymd.uix.menu import MDDropdownMenu
from app.models import UserSetting

from plyer import email

from app.utils.screen import AboutDialogContent
from app.utils.files import win_file_chooser
from app.utils.ui import show_msg

class SettingsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = MDApp.get_running_app()
        self.info_dialog = None
        self.help_dialog = None
        self.freq_menu = None
        self.range_menu = None
        self._loading = False

    def on_pre_enter(self):
        """Syncs the UI with current database settings."""
        self._loading = True
        settings = self.app.db.query(UserSetting).first()
        
        if settings:
            # Theme UI
            self.ids.theme_switch.active = (self.app.theme_cls.theme_style == "Dark")
            
            # Export Logic UI
            self.ids.auto_export_switch.active = settings.auto_export_enabled
            self.ids.export_freq_item.secondary_text = f"Currently: {settings.export_frequency}"
            
            # Export Range UI
            current_range = getattr(settings, 'export_range', 'Full History')
            self.ids.export_range_item.secondary_text = f"Currently: {current_range}"
            
            # Quick Share UI
            is_share_enabled = getattr(settings, 'quick_share_enabled', False)
            self.ids.quick_share_switch.active = is_share_enabled

            # Folder Path UI
            if settings.export_path:
                self.ids.export_path_item.secondary_text = f"Path: {settings.export_path}"
            
        self._loading = False

    def toggle_theme(self, state):
        if self._loading: return
        new_style = "Dark" if state else "Light"
        self.app.theme_cls.theme_style = new_style
        
        if platform == 'android':
            from app.utils.android import set_android_status_bar
            set_android_status_bar(self.app)

        settings = self.app.db.query(UserSetting).first()
        if settings:
            settings.theme_mode = new_style
            self.app.db.commit()

    def toggle_auto_export(self, state):
        if self._loading: return
        settings = self.app.db.query(UserSetting).first()
        if settings:
            settings.auto_export_enabled = state
            self.app.db.commit()

    def toggle_quick_share(self, state):
        if self._loading: return
        settings = self.app.db.query(UserSetting).first()
        if settings:
            settings.quick_share_enabled = state
            self.app.db.commit()

    def show_frequency_menu(self):
        menu_items = ["Daily", "Weekly", "Monthly", "Quarterly", "Yearly"]
        items = [
            {
                "viewclass": "DropdownItem",
                "text": freq,
                "on_release": lambda x=freq: self.set_frequency(x),
            } for freq in menu_items
        ]
        
        if self.freq_menu:
            self.freq_menu.dismiss()
            
        self.freq_menu = MDDropdownMenu(caller=self.ids.export_freq_item, items=items, width=dp(160))
        self.freq_menu.open()

    def set_frequency(self, freq):
        settings = self.app.db.query(UserSetting).first()
        if settings:
            settings.export_frequency = freq
            self.app.db.commit()
            self.ids.export_freq_item.secondary_text = f"Currently: {freq}"
        if self.freq_menu:
            self.freq_menu.dismiss()

    def show_range_menu(self):
        range_options = ["Full History", "Current Month", "Last 3 Months", "Current Year"]
        items = [
            {
                "viewclass": "DropdownItem",
                "text": r_type,
                "on_release": lambda x=r_type: self.set_export_range(x),
            } for r_type in range_options
        ]
        
        if self.range_menu:
            self.range_menu.dismiss()
            
        self.range_menu = MDDropdownMenu(caller=self.ids.export_range_item, items=items, width=dp(180))
        self.range_menu.open()

    def set_export_range(self, r_type):
        settings = self.app.db.query(UserSetting).first()
        if settings:
            settings.export_range = r_type
            self.app.db.commit()
            self.ids.export_range_item.secondary_text = f"Currently: {r_type}"
        if self.range_menu:
            self.range_menu.dismiss()


    def show_help_dialog(self):
        help_text = (
            "Welcome to the Finora Support Hub. Here is a quick guide to common questions:\n\n"
            "• [b]Exporting:[/b] Use the side menu for manual reports or enable 'Auto-Export' in settings.\n\n"
            "• [b]Data Privacy:[/b] All records are stored offline. We never sync your data to the cloud.\n\n"
            "• [b]Navigation:[/b] Use the 'Bin' to recover deleted entries. Filter by type in the drawer.\n\n"
            "• [b]Still Confused?[/b] Click 'ENQUIRY' to send us a direct message."
        )
        
        self.help_dialog = MDDialog(
            MDDialogHeadlineText(text="Finora Help Center"),
            MDDialogSupportingText(text=help_text),
            MDDialogButtonContainer(
                # Button 1: Close
                MDButton(
                    MDButtonText(text="GOT IT"), 
                    style="text", 
                    on_release=lambda x: self.help_dialog.dismiss()
                ),
                # Button 2: Navigate to Email Draft
                MDButton(
                    MDButtonText(text="ENQUIRY"), 
                    style="filled", # Filled style makes it stand out as a call to action
                    on_release=self.contact_admin
                ),
                spacing="8dp",
            ),
        )
        self.help_dialog.open()

    def contact_admin(self, *args):
        """Drafts an email specifically targeting mail clients."""
        recipient = "admin@hacksmiths.dev"
        subject = "Finora App: Support & Enquiry"
        body = "Hi HackSmiths Team,\n\nI have a question regarding...\n\n"

        if platform == 'android':
            from app.utils.android import send_support_email
            send_support_email(recipient, subject, body)
        else:
            # Desktop fallback
            try:
                email.send(recipient=recipient, subject=subject, text=body)
            except Exception as e:
                print(f'Email error: {e}')
                show_msg(text="No email client found.")
        
        if self.help_dialog:
            self.help_dialog.dismiss()


    def show_info(self, *args):
        if not self.info_dialog:
            self.info_dialog = MDDialog(
                MDDialogHeadlineText(text="About the App"),
                MDDialogContentContainer(
                    AboutDialogContent(), # Instantiates the KV layout
                ),
                MDDialogButtonContainer(
                    MDButton(
                        MDButtonText(text="DISMISS"), 
                        style="text", 
                        on_release=lambda x: self.info_dialog.dismiss()
                    ),
                    spacing="8dp",
                ),
            )
        self.info_dialog.open()

    def load_permission(self):
        if platform == 'android':
            from app.utils.android import request_permissions_for_android
            request_permissions_for_android(self.app, True)
        
        else:
            show_msg('Permissions are only required on Mobile.')

    def pick_export_folder(self):
        if platform == 'android':
            from app.utils.android import open_file_chooser
            status = open_file_chooser()
        else:
            status = win_file_chooser()
        if status:
            settings = self.app.db.query(UserSetting).first()
            self.ids.export_path_item.secondary_text = f"Path: {settings.export_path}"
            show_msg(text="Export path updated!")