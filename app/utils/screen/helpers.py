from kivy.metrics import dp
from kivy.core.window import Window

from kivymd.uix.menu import MDDropdownMenu


# --- 1. SEARCH & SELECTION HANDLERS ---
def enter_search_mode(self):
    self.search_mode = True
    self.ids.entry_list.clear_widgets()
    self.ids.search_ui.ids.header_icon_btn.icon = "arrow-left"
    self.update_ui_state(state="search")
    self.toggle_empty_state(show=False)

def cancel_search(self):
    self.search_mode = False
    self.ids.search_ui.ids.search_field.text = ""
    self.ids.search_ui.ids.search_field.focus = False
    Window.release_all_keyboards()
    self.ids.search_ui.ids.header_icon_btn.icon = "menu"

    self.reset_filter_chips()
    self.load_entries(getattr(self, 'current_category', 'All'))
    self.update_ui_state(state="normal")

def enter_selection_mode(self, instance):
    if self.selection_mode: return
    self.selection_mode = True
    self.selected_ids = [instance.record_id]
    self.update_ui_state(state="selection")
    self.refresh_selection_bar()
    self.load_entries(getattr(self, 'current_category', 'All'))

def exit_selection_mode(self, *args):
    self.selection_mode = False
    self.selected_ids = []
    
    self.ids.header_container.clear_widgets()
    if self.search_header_cache:
        if self.search_header_cache.parent:
            self.search_header_cache.parent.remove_widget(self.search_header_cache)
        self.ids.header_container.add_widget(self.search_header_cache)
        self.search_header_cache.ids.search_field.text = ""
        self.search_header_cache.ids.header_icon_btn.icon = "menu"

    self.load_entries(getattr(self, 'current_category', 'All'))
    self.update_ui_state(state="normal")


# --- 2. SEARCH INPUT HANDLING ---
def on_search_focus(self, instance, value):
    """Triggers the UI shift when the search bar is tapped."""
    if value:
        enter_search_mode(self)

def on_header_button_release(self, *args):
    """Handles the top-left icon (Menu vs. Back vs. Close)."""
    if getattr(self, 'search_mode', False):
        cancel_search(self)
    elif getattr(self, 'selection_mode', False):
        exit_selection_mode(self)
    else:
        # Standard behavior: Open Navigation Drawer
        self.app.root.ids.nav_drawer.set_state("open")


# --- 3. FILTER & CHIP LOGIC ---
def open_filter_menu(self, caller, filter_type):
    """Generic menu builder for Type, Method, and Date filters."""
    current_screen = self.app.root.ids.screen_manager.current_screen

    if hasattr(current_screen, 'menu') and current_screen.menu:
        current_screen.menu.dismiss()

    opts = {
        "Type": ["All", "Credit", "Debit", "Receipt"],
        "Method": ["All", "Cash", "Online", "GPay", "Cheque", "Other"],
        "Date": ["Anytime", "Older than a week", "Month", "Six month", "Year"]
    }.get(filter_type, [])

    items = [{
        "viewclass": "DropdownItem",
        "text": o,
        "on_release": lambda x=o: apply_filter(current_screen, filter_type, x, caller)
    } for o in opts]

    current_screen.menu = MDDropdownMenu(
        caller=caller, items=items, width=dp(180),
        position="bottom", ver_growth="down", hor_growth="right"
    )
    current_screen.menu.open()

def apply_filter(self, filter_type, selection, caller):
    """Updates the filter state and triggers a re-search."""
    if hasattr(self, 'menu') and self.menu:
        self.menu.dismiss()
    
    # Update the screen's tracking dictionary
    self.active_filters[filter_type] = selection
    
    # Visual feedback for the Chip
    if selection in ["All", "Anytime"]:
        caller.text = filter_type
        caller.style = "outlined"
        caller.theme_bg_color = "Primary"
    else:
        caller.text = selection
        caller.style = "filled"
        caller.theme_bg_color = "Custom"
        caller.md_bg_color = self.app.theme_cls.primaryColor

    # Trigger search logic
    search_field = self.ids.search_ui.ids.search_field
    self.search(search_field.text if search_field.text else "")

def reset_filter_chips(self):
    """Returns all chips to their default state."""
    self.ids.empty_search_box.show_button = False
    self.active_filters = {"Method": "All", "Type": "All", "Date": "Anytime"}
    
    # Iterate through the container in search_ui.kv
    for chip in self.ids.search_ui.ids.filter_container.children:
        if hasattr(chip, 'filter_key'):
            chip.text = chip.filter_key
            chip.style = "outlined"
            chip.theme_bg_color = "Primary"


# --- 4. ITEM INTERACTION ---
def handle_item_click(self, instance):
    """Determines whether to 'Select' or 'View' an item."""
    if self.selection_mode:
        if instance.record_id in self.selected_ids: 
            self.selected_ids.remove(instance.record_id)
        else: 
            self.selected_ids.append(instance.record_id)
        
        if not self.selected_ids: 
            exit_selection_mode(self)
        else:
            self.refresh_selection_bar()
            self.load_entries(getattr(self, 'current_category', 'All'))
    else: 
        self.go_to_view(instance)

def select_all_items(self, button_instance):
    """Bulk selection logic."""
    all_ids = self._get_visible_ids()
    self.selected_ids = [] if len(self.selected_ids) == len(all_ids) else all_ids
    
    self.refresh_selection_bar()
    self.load_entries(getattr(self, 'current_category', 'All'))

def go_to_view(self, instance):
    self.app.root.ids.screen_manager.get_screen("view_entry").current_record_id = instance.record_id
    self.app.last_screen = self.app.root.ids.screen_manager.current
    self.app.root.ids.screen_manager.current = "view_entry"