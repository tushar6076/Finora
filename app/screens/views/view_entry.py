from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import StringProperty

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.appbar import MDActionTopAppBarButton
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
from kivymd.uix.dialog import MDDialog, MDDialogHeadlineText, MDDialogContentContainer

from datetime import datetime

from app.utils.screen import DeleteContent
from app.utils.files import share_report, download_report
from app.utils.ui import show_msg, update_nav_badges

# Services & Models
from app.models import FinancialRecord

class DetailItem(MDBoxLayout):
    icon = StringProperty("")
    label = StringProperty("")
    text = StringProperty("N/A")

class ViewEntryScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = MDApp.get_running_app()
        self.delete_dialog = None
        self.current_record_id = None

    def on_enter(self):
        if not self.current_record_id:
            return
        record = self.app.db.query(FinancialRecord).get(self.current_record_id)
        if record:
            self.ids.amount.text = f"₹ {record.amount}"
            self.ids.transaction_type.text = record.transaction_type.upper()
            self.ids.person_name.text = record.person_name
            self.ids.branch_name.text = record.branch_name
            self.ids.transaction_date.text = str(record.transaction_date)
            self.ids.transaction_method.text = record.transaction_method
            self.ids.received_by.text = record.received_by
        container = self.ids.trailing_container
        container.clear_widgets()

        # 2. Define which set of buttons to show
        if self.app.last_screen == 'bin':
            actions = [
                ("history", self.app.theme_cls.primaryColor, self.restore),
                ("delete-forever", self.app.theme_cls.errorColor, self.delete_forever)
            ]
        else:
            actions = [
                ("share-variant-outline", None, self.share_entry),
                ("download-outline", None, self.download_entry),
                ("pencil-outline", None, self.edit_entry),
                ("trash-can-outline", self.app.theme_cls.errorColor, self.delete_entry)
            ]

        # 3. Inject the buttons
        for icon, color, callback in actions:
            btn = MDActionTopAppBarButton(icon=icon)
            if color:
                btn.theme_icon_color = "Custom"
                btn.icon_color = color
            
            btn.bind(on_release=lambda x, cb=callback: cb())
            container.add_widget(btn)

    def delete_entry(self, *args):
        record = self.app.db.query(FinancialRecord).get(self.current_record_id)
        selected_ids = [self.current_record_id]
        count = len(selected_ids)
        if record:
            record.is_deleted = True
            record.deleted_at = datetime.utcnow()
            self.app.db.commit()
            
        self.app.root.ids.screen_manager.current = self.app.last_screen
        home_obj = self.app.root.ids.screen_manager.get_screen('home')

        home_obj.deleted_snackbar = MDSnackbar(
            MDSnackbarText(
                text=f"Moved {count} item{'s' if count > 1 else ''} to Bin",
            ),
            MDIconButton(
                icon="undo",
                theme_icon_color="Custom",
                icon_color="#6366F1",
                on_release=lambda x, count=count, ids=selected_ids: home_obj.undo_delete(count, ids)
            ),
            y=dp(24),
            orientation="horizontal",
            padding=[dp(12), dp(8), dp(12), dp(8)],
            spacing=dp(10),
        )
        home_obj.deleted_snackbar.open()


    def restore(self, *args):
        record = self.app.db.query(FinancialRecord).get(self.current_record_id)
        record.is_deleted = False
        record.deleted_at = None
        self.app.db.commit()
        
        # Update drawer badges after restoration
        update_nav_badges(self.app)
        self.app.root.ids.screen_manager.current = self.app.last_screen
        
        # SUCCESS SNACKBAR (Green)
        
        show_msg(text=f"Restored 1 item to your records", status='success')

    def delete_forever(self, *args):       
        # Store the dialog in self so dismiss_dialog() can find it
        self.dialog = MDDialog(
            MDDialogHeadlineText(text="Confirm Permanent Delete"),
            MDDialogContentContainer(DeleteContent()), # Using your KV class
        )
        self.dialog.open()

    def perform_delete(self):
        """Step 2: The Execution - Called by the 'DELETE' button in KV."""
        if hasattr(self, 'dialog'): self.dialog.dismiss()
        # 1. Database Logic
        record = self.app.db.query(FinancialRecord).get(self.current_record_id)
        
        self.app.db.delete(record)
        self.app.db.commit()
        
        # 2. UI Updates
        update_nav_badges(self.app)
        self.app.root.ids.screen_manager.current = self.app.last_screen
        
        # 3. Success Feedback
        show_msg(text="Permanently wiped 1 item.", status='error') # Soft Red text for deletion info

    def share_entry(self):
        record = self.app.db.query(FinancialRecord).get(self.current_record_id)
        share_report(self.app, [record])

    def download_entry(self):
        record = self.app.db.query(FinancialRecord).get(self.current_record_id)
        download_report(self.app, [record])

    def edit_entry(self):
        self.app.root.ids.screen_manager.get_screen("add_entry").current_record_id = self.current_record_id
        self.app.last_screen = self.app.root.ids.screen_manager.current
        self.app.root.ids.screen_manager.current = "add_entry"