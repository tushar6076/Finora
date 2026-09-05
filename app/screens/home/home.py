from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
from kivymd.uix.button import MDIconButton

from app.models import FinancialRecord
from datetime import datetime

from app.utils.screen import ScreenBehaviorMixin
from app.utils.screen import (
    on_search_focus, on_header_button_release, open_filter_menu, apply_filter,
    reset_filter_chips, handle_item_click, select_all_items, go_to_view,
    enter_search_mode, cancel_search, enter_selection_mode, exit_selection_mode
)
from app.utils.files import share_report, download_report
from app.utils.ui import update_nav_badges, sync_nav_state

class HomeScreen(MDScreen, ScreenBehaviorMixin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = MDApp.get_running_app()
        
        # Core State Tracking
        self.selected_ids = []  
        self.current_category = "All"
        self.selection_mode = False
        self.search_mode = False
        self.active_filters = {"Method": "All", "Type": "All", "Date": "Anytime"}
        self.search_header_cache = None

    def on_kv_post(self, base_widget):
        """Capture the search bar from KV for selection mode swaps."""
        if 'search_ui' in self.ids:
            self.search_header_cache = self.ids['search_ui'].__self__

    def on_pre_enter(self):
        sync_nav_state(self.app, "home")

    def on_enter(self):
        # Safety check for Kivy's lazy loading
        if not self.ids or 'sub_ui' not in self.ids:
            Clock.schedule_once(lambda dt: self.on_enter(), 0.1)
            return
        
        # Using Mixin power to load data and set UI state
        self.load_entries(self.current_category)
        self.update_ui_state(state="normal")
        Clock.schedule_once(lambda dt: update_nav_badges(self.app), 0.2)

    # --- 1. IDENTITY HOOKS (The Mixin calls these) ---

    def get_selection_actions(self):
        """Home-specific buttons for the selection bar."""
        actions = [
            ("share-variant-outline", self.share_item),
            ("download-outline", self.download_item),
        ]
        
        # Edit only makes sense for a single item
        if len(self.selected_ids) == 1:
            actions.append(("pencil-outline", self.go_to_edit))
            
        # Delete action (Passes a red color hex as the 3rd element)
        actions.append(("trash-can-outline", self.delete_selected, "#C62828"))
        return actions

    def get_empty_state_config(self):
        """Home-specific text for empty states."""
        if self.search_mode:
            filters_active = any(v not in ["All", "Anytime"] for v in self.active_filters.values())
            return {
                "title": "No matches found",
                "desc": "Try a different keyword or reset your filters.",
                "btn_text": "Clear all filters",
                "show_btn": filters_active,
                "callback": self.reset_filter_chips
            }
        
        return {
            "title": "No transactions yet",
            "desc": "Tap below to add your first entry and start tracking.",
            "btn_text": "Add your first entry",
            "show_btn": True,
            "callback": self.go_to_add_entry
        }

    def _get_visible_ids(self):
        """Helper for the Mixin to handle 'Select All'."""
        query = self.app.db.query(FinancialRecord).filter_by(is_deleted=False)
        if self.current_category != "All":
            query = query.filter_by(transaction_type=self.current_category)
        return [r.id for r in query.all()]

    # --- HELPER MAPPING (The Full 12-Function Bridge) ---
    def on_search_focus(self, i, v): on_search_focus(self, i, v)
    def on_header_button_release(self, *a): on_header_button_release(self, *a)
    def open_filter_menu(self, c, f): open_filter_menu(self, c, f)
    def apply_filter(self, f, s, c): apply_filter(self, f, s, c) # Bridge 12
    def reset_filter_chips(self): reset_filter_chips(self)
    def handle_item_click(self, i): handle_item_click(self, i)
    def select_all_items(self, b): select_all_items(self, b)
    def go_to_view(self, i): go_to_view(self, i)
    def enter_search_mode(self): enter_search_mode(self)
    def cancel_search(self): cancel_search(self)
    def enter_selection_mode(self, i): enter_selection_mode(self, i)
    def exit_selection_mode(self, *a): exit_selection_mode(self, *a)


    # --- 3. HOME-SPECIFIC LOGIC ---
    def delete_selected(self, *args):       
        selected_ids = list(self.selected_ids)
        count = len(self.selected_ids)
        
        # Database Update
        records = self.app.db.query(FinancialRecord).filter(FinancialRecord.id.in_(selected_ids)).all()
        for r in records: 
            r.is_deleted = True
            r.deleted_at = datetime.now()
        self.app.db.commit()
        
        update_nav_badges(self.app)
        self.exit_selection_mode()
        
        # Show Snackbar with Undo
        MDSnackbar(
            MDSnackbarText(text=f"Moved {count} item{'s' if count > 1 else ''} to Bin"),
            MDIconButton(
                icon="undo", theme_icon_color="Custom", icon_color="#6366F1",
                on_release=lambda x: self.undo_delete(count, selected_ids)
            ),
            y=dp(24), orientation="horizontal", padding=[dp(12), dp(8)],
        ).open()

    def undo_delete(self, count, ids_to_restore):
        records = self.app.db.query(FinancialRecord).filter(FinancialRecord.id.in_(ids_to_restore)).all()
        for r in records:
            r.is_deleted = False
            r.deleted_at = None
        self.app.db.commit()
        self.load_entries(self.current_category)
        update_nav_badges(self.app)

    def go_to_add_entry(self): 
        self.app.last_screen = self.app.root.ids.screen_manager.current
        self.app.root.ids.screen_manager.current = "add_entry"

    def go_to_edit(self, *args): 
        self.app.root.ids.screen_manager.get_screen("add_entry").current_record_id = self.selected_ids[0]
        self.exit_selection_mode() 
        self.app.last_screen = self.app.root.ids.screen_manager.current
        self.app.root.ids.screen_manager.current = "add_entry"

    def share_item(self, *args):
        records = self.app.db.query(FinancialRecord).filter(FinancialRecord.id.in_(self.selected_ids)).all()
        share_report(self.app, records)
        self.exit_selection_mode()

    def download_item(self, *args):
        records = self.app.db.query(FinancialRecord).filter(FinancialRecord.id.in_(self.selected_ids)).all()
        download_report(self.app, records)
        self.exit_selection_mode()