from kivy.clock import Clock
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.core.window import Window
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.list import (
    MDListItemLeadingIcon, MDListItemHeadlineText, 
    MDListItemSupportingText, MDListItemTertiaryText
)
from sqlalchemy import or_, cast, String
from datetime import datetime, timedelta

from app.models import FinancialRecord
from .classes import CustomListItem, PillBadge

class ScreenBehaviorMixin:
    """
    A Mixin class to provide shared UI logic for Home and Bin screens.
    Expects the inheriting class to have:
    - self.app (App instance)
    - self.ids (Widget IDs)
    - get_selection_actions() -> list
    - get_empty_state_config() -> dict
    """

    # --- 1. UI STATE CONTROLLER ---
    def update_ui_state(self, state="normal"):
        widgets = {
            "norm": self.ids.get('sub_ui'),
            "sel": self.ids.get('sub_ui_selection'),
            "note": self.ids.get('bin_notice'),
            "fab": self.ids.get('fab'),
            "filt": self.ids.search_ui.ids.get('filter_scroll')
        }

        configs = {
            "normal":   {"norm": (1, dp(40), False), "sel": (0, 0, True), 
                         "note": (1, None, False) if self.ids.entry_list.children else (0, 0, True), 
                         "fab": (1, dp(56), False) if self.ids.entry_list.children else (0, 0, True), 
                         "filt": (0, 0, True)},
            "selection":{"norm": (0, 0, True), "sel": (1, dp(48), False), "note": (0, 0, True), "fab": (0, 0, True), "filt": (0, 0, True)},
            "search":   {"norm": (0, 0, True), "sel": (0, 0, True), "note": (0, 0, True), "fab": (0, 0, True), "filt": (1, dp(44), False)},
            "hidden":   {"norm": (0, 0, True), "sel": (0, 0, True), "note": (0, 0, True), "fab": (0, 0, True), "filt": (0, 0, True)}
        }

        cfg = configs.get(state, configs["normal"])

        for key, (opacity, height, disabled) in cfg.items():
            w = widgets[key]
            if not w: continue
            
            w.disabled = disabled
            anim = Animation(opacity=opacity, duration=0)
            
            if height is not None:
                anim &= Animation(height=height, duration=0)
            elif opacity == 1 and hasattr(w, 'minimum_height'):
                anim &= Animation(height=w.minimum_height, duration=0.2)
            anim.start(w)

        if state == "selection" and widgets["sel"]:
            widgets["sel"].select_all_action = self.select_all_items


    # --- 2. DATA & SEARCH LOGIC ---
    def load_entries(self, category="All"):
        is_bin = getattr(self, 'name', '') == 'bin'
        self.current_category = category
        query = self.app.db.query(FinancialRecord).filter_by(is_deleted=is_bin)
        if category != "All":
            query = query.filter_by(transaction_type=category)
            name = str(category).upper()
        else: name = 'ALL TRANSACTIONS'
        
        rows = query.order_by(FinancialRecord.transaction_date.desc()).all()

        if sub_ui := self.ids.get('sub_ui'):
            sub_ui.label_text = name if not is_bin else 'RECYCLE BIN'
            total = sum(float(r.amount) for r in rows)
            sub_ui.amount_text = f"Total: ₹{total:,.2f}" if not is_bin else f"Items: {len(rows)}"

        self.update_list_widgets(rows)

    def search(self, text):  
        is_bin = getattr(self, 'name', '') == 'bin'
        query = self.app.db.query(FinancialRecord).filter_by(is_deleted=is_bin)
        
        # Apply Filters
        if self.active_filters.get("Type") != "All":
            query = query.filter_by(transaction_type=self.active_filters["Type"])
        if self.active_filters.get("Method") != "All":
            query = query.filter_by(transaction_method=self.active_filters["Method"])
        if self.active_filters.get("Date") != "Anytime":
            query = self.apply_date_filtering(query)
            
        if text.strip():
            search_query = f"%{text}%"
            query = query.filter(or_(
                FinancialRecord.person_name.ilike(search_query),
                FinancialRecord.branch_name.ilike(search_query),
                cast(FinancialRecord.amount, String).ilike(search_query),
                FinancialRecord.transaction_date.ilike(search_query)
            ))

        if list(self.active_filters.values()) == ['All', 'All', 'Anytime'] and not text.strip():
            results = None
        else:
            results = query.order_by(FinancialRecord.transaction_date.desc()).all()
        self.update_list_widgets(results)

    def apply_date_filtering(self, query):
        now = datetime.now()
        ds = self.active_filters.get("Date")
        def get_str(days): return (now - timedelta(days=days)).strftime('%Y-%m-%d')
        
        filters = {
            "Older than a week": FinancialRecord.transaction_date < get_str(7),
            "Month": FinancialRecord.transaction_date >= get_str(30),
            "Six month": FinancialRecord.transaction_date >= get_str(180),
            "Year": FinancialRecord.transaction_date >= get_str(365)
        }
        return query.filter(filters[ds]) if ds in filters else query

    # --- 3. UI ASSEMBLY ---
    def update_list_widgets(self, rows):
        self.ids.entry_list.clear_widgets()
        if not rows:
            self.toggle_empty_state(show=True)
            if not self.selection_mode and not self.search_mode: self.update_ui_state(state="normal")
            return
        self.toggle_empty_state(show=False)

        for record in rows:
            is_selected = record.id in self.selected_ids
            icon_cfg = {
                "Credit": ("arrow-up-bold-circle", (0, 0.6, 0.3, 1), "#E8F5E9", "#2E7D32"),
                "Debit": ("arrow-down-bold-circle", (0.9, 0.2, 0.2, 1), "#FFEBEE", "#C62828"),
                "Receipt": ("text-box", (0.3, 0.4, 0.9, 1), "#E3F2FD", "#1565C0")
            }
            icon_name, icon_col, bg_hex, txt_hex = icon_cfg.get(record.transaction_type, ("help", (0.5, 0.5, 0.5, 1), "#EEEEEE", "#757575"))

            item = CustomListItem(
                MDListItemLeadingIcon(icon="check-circle" if is_selected else icon_name, theme_icon_color="Custom", icon_color=(0.1, 0.4, 0.8, 1) if is_selected else icon_col),
                MDListItemHeadlineText(text=record.person_name),
                MDListItemSupportingText(text=f"₹{record.amount} • {record.transaction_method}"),
                MDListItemTertiaryText(text=str(record.transaction_date)),
            )

            if is_selected: item.md_bg_color = "#E1F5FE"
            badge = PillBadge(text=record.transaction_type)
            badge.set_colors(bg_hex, txt_hex)
            item.add_widget(badge)
            
            item.record_id = record.id
            item.bind(on_release=self.handle_item_click)
            self.ids.entry_list.add_widget(item)

    def refresh_selection_bar(self):
        visible_ids = self._get_visible_ids()
        is_all_selected = len(self.selected_ids) == len(visible_ids) and len(visible_ids) > 0
        
        if sel_sub := self.ids.get('sub_ui_selection'):
            if btn := sel_sub.ids.get('select_all_btn'):
                btn.icon = "checkbox-marked-outline" if is_all_selected else "checkbox-blank-outline"

        self.ids.header_container.clear_widgets()
        bar = MDBoxLayout(adaptive_height=True, padding=[dp(12), dp(8), dp(12), dp(8)], spacing=dp(4))
        bar.add_widget(MDIconButton(icon="close", on_release=self.exit_selection_mode))
        bar.add_widget(MDLabel(text=f"{len(self.selected_ids)}", font_style="Title", role="medium", pos_hint={"center_y": .5}))
        bar.add_widget(MDBoxLayout(size_hint_x=1)) 
        
        for icon, func, *color in self.get_selection_actions():
            btn = MDIconButton(icon=icon)
            if color: btn.theme_icon_color, btn.icon_color = "Custom", color[0]
            if not self.selected_ids: btn.disabled = True
            btn.bind(on_release=lambda x, f=func: f()) 
            bar.add_widget(btn)
        self.ids.header_container.add_widget(bar)

    def toggle_empty_state(self, show=False):
        box, scroll = self.ids.empty_search_box, self.ids.main_scroll
        note = self.ids.get('bin_notice')
        fab = self.ids.get('fab')
        if show:
            cfg = self.get_empty_state_config()
            box.title, box.description = cfg.get('title', ""), cfg.get('desc', "")
            box.button_text, box.show_button = cfg.get('btn_text', ""), cfg.get('show_btn', False)
            box.callback = cfg.get('callback', lambda: None)
            scroll.opacity, scroll.disabled, scroll.size_hint_y, scroll.height = 0, True, None, 0
            box.disabled = False
            Animation(opacity=1, duration=0.1).start(box)
        else:
            scroll.opacity, scroll.disabled, scroll.size_hint_y = 1, False, 1
            box.disabled = True
            Animation(opacity=0, duration=0.1).start(box)