from kivy.clock import Clock
from kivymd.uix.screen import MDScreen
from kivymd.app import MDApp
from kivymd.uix.pickers.datepicker import MDModalDatePicker
from kivymd.uix.menu import MDDropdownMenu
from kivy.metrics import dp

from datetime import datetime

# Import the model
from app.models import FinancialRecord

from app.utils.ui import show_msg, update_nav_badges

class AddEntryScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = MDApp.get_running_app()
        self.current_record_id = None
        # Delay menu setup to ensure IDs are loaded
        self.type_menu = None
        self.method_menu = None

    def on_kv_post(self, base_widget):
        """Setup menus after the KV is loaded."""
        Clock.schedule_once(lambda dt: self.setup_menus(), 0)

    def on_enter(self):  
        if self.current_record_id:
            record = self.app.db.query(FinancialRecord).get(self.current_record_id)
            if record:
                self._loading = True 
                self.ids.app_bar_title.text = "Edit Transaction" # Direct ID reference
                
                # Fill fields
                self.ids.amount.text = str(abs(record.amount)) 
                self.ids.transaction_type.text = record.transaction_type
                self.ids.person_name.text = record.person_name
                self.ids.branch_name.text = record.branch_name
                self.ids.transaction_date.text = str(record.transaction_date)
                self.ids.transaction_method.text = record.transaction_method
                self.ids.received_by.text = record.received_by
                
                self._loading = False
                self.toggle_submit()

    def setup_menus(self):
        # Transaction Type Menu
        type_items = ["Credit", "Debit", "Receipt"]
        self.type_menu = MDDropdownMenu(
            caller=self.ids.transaction_type,
            items=[{
                "viewclass": "DropdownItem", # Use our new custom class
                "text": t,                   # This maps to 'root.text' in KV
                "on_release": lambda x=t: self.set_item("transaction_type", x),
            } for t in type_items],
            width=dp(200),
        )

        # Transaction Method Menu
        method_items = ["Cash", "Online", "GPay", "Cheque", "Other"]
        self.method_menu = MDDropdownMenu(
            caller=self.ids.transaction_method,
            items=[{
                "viewclass": "DropdownItem",
                "text": m,
                "on_release": lambda x=m: self.set_item("transaction_method", x),
            } for m in method_items],
            width=dp(200),
        )

    def set_item(self, field_id, text):
        field = self.ids[field_id]
        field.text = text

        field.error = False
        for child in field.children:
            if hasattr(child, "icon"):
                child.theme_text_color = "Primary"

        # Use safe dismissal
        if self.type_menu: self.type_menu.dismiss()
        if self.method_menu: self.method_menu.dismiss()
        # Ensure the submit button state is checked after selection
        self.toggle_submit()

    def show_date_picker(self):
        date_dialog = MDModalDatePicker()
        date_dialog.bind(on_ok=self.on_save, on_cancel=self.on_cancel)
        date_dialog.open()

    def on_save(self, instance_date_picker):
        # selected_dates is a list of datetime.date objects, e.g., [datetime.date(2026, 3, 21)]
        selected_dates = instance_date_picker.get_date()
        
        if selected_dates:
            date_obj = selected_dates[0]
            field = self.ids.transaction_date
            field.text = date_obj.strftime("%Y-%m-%d")
            
            # CLEAR THE ERROR: Valid date selected
            field.error = False
            for child in field.children:
                if hasattr(child, "icon"):
                    child.theme_text_color = "Primary"
            
        
        instance_date_picker.dismiss()
        # Trigger validation check
        self.toggle_submit()

    def on_cancel(self, instance_date_picker):
        instance_date_picker.dismiss()

    
    def check_empty_on_leave(self, instance, is_focused):
        if not is_focused:
            # Check if the text is empty
            is_empty = not instance.text.strip()
            
            instance.error = is_empty

            for child in instance.children:
                if hasattr(child, "icon"): # This finds MDTextFieldLeadingIcon
                    if is_empty:
                        child.theme_text_color = "Error" 
                    else:
                        child.theme_text_color = "Primary"

    def toggle_submit(self):
        if getattr(self, '_loading', False):
            return

        field_values = [child.text.strip() for child in self.ids.container.children if hasattr(child, 'text')]
        has_empty_fields = any(val == "" for val in field_values)

        if not self.current_record_id:
            self.ids.submit_btn.disabled = has_empty_fields
            return
        
        record = self.app.db.query(FinancialRecord).get(self.current_record_id)
        if not record:
            return

        is_changed = False
        
        for field_id, widget in self.ids.items():
            # Only check widgets that are inside our scrollable container
            if widget in self.ids.container.children:
                if hasattr(record, field_id):
                    ui_val = str(widget.text.strip())
                    db_raw = getattr(record, field_id)
                    db_val = str(db_raw) if db_raw is not None else ""
                    if field_id == "amount":
                        try:
                            clean_ui = ui_val.replace('₹', '').replace(',', '').strip()
                            if abs(float(clean_ui)) == abs(float(db_raw)):
                                continue
                        except: pass

                    if ui_val != db_val:
                        is_changed = True
                        break

        self.ids.submit_btn.disabled = not is_changed or has_empty_fields


    def submit_entry(self):
        # 1. Safe Amount Conversion
        self.ids.submit_btn.disabled = True
        try:
            raw_amt = self.ids.amount.text.strip().replace('₹', '').replace(',', '').replace('-', '')
            amount = float(raw_amt)
            if self.ids.transaction_type.text == 'Debit':
                amount = -amount
        except ValueError as e:
            print("Invalid amount format:", e)
            show_msg('Invalid Amount Format', status='error')
            self.ids.submit_btn.disabled = False
            return

        # 2. Update OR Create
        if self.current_record_id:
            record = self.app.db.query(FinancialRecord).get(self.current_record_id)
            if record:
                record.person_name = self.ids.person_name.text.strip()
                record.branch_name = self.ids.branch_name.text.strip()
                record.transaction_date = datetime.strptime(self.ids.transaction_date.text.strip(), "%Y-%m-%d").date()
                record.amount = amount
                record.transaction_type = self.ids.transaction_type.text
                record.transaction_method = self.ids.transaction_method.text
                record.received_by = self.ids.received_by.text.strip()
        else:
            new_record = FinancialRecord(
                person_name=self.ids.person_name.text.strip(),
                branch_name=self.ids.branch_name.text.strip(),
                transaction_date=datetime.strptime(self.ids.transaction_date.text.strip(), "%Y-%m-%d").date(),
                amount=amount,
                transaction_type=self.ids.transaction_type.text,
                transaction_method=self.ids.transaction_method.text,
                received_by=self.ids.received_by.text.strip()
            )
            self.app.db.add(new_record)

        # 3. Save and Navigate
        try:
            self.app.db.commit()
            # Important: Reset the ID so the next 'Add' doesn't think it's an 'Edit'
            self.current_record_id = None 
            self.clear_fields()
            
            # Navigate back to wherever we came from
            update_nav_badges(self.app)
            self.app.root.ids.screen_manager.current = self.app.last_screen
            
        except Exception as e:
            print(f"Error saving: {e}")
            show_msg('Error Saving Data', status='error')
            self.app.db.rollback()

    def clear_fields(self):
        # Reset text of M3 TextFields
        self.current_record_id = None
        fields = ["person_name", "branch_name", "transaction_date", "amount", 
                  "transaction_type", "transaction_method", "received_by"]
        for field in fields:
            self.ids[field].error = False
            self.ids[field].focus = False
        self.ids.app_bar_title.text = "New Transaction"
        Clock.schedule_once(lambda dt: self._do_text_clear(fields), 0.05)

    def _do_text_clear(self, fields):
        for field_id in fields:
            field = self.ids.get(field_id)
            if field:
                field.text = ""
                
        self.ids.app_bar_title.text = "New Transaction"
        self.ids.submit_btn.disabled = True
        
        # 3. Final Pulse: Re-enable logic
        Clock.schedule_once(self._finalize_ui_reset, 0.1)

    def _finalize_ui_reset(self, dt):
        self._loading = False