from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.app import MDApp

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDListItem

from kivy.graphics import Color, RoundedRectangle
from kivy.utils import get_color_from_hex

from kivymd.uix.selectioncontrol import MDSwitch

class NoRippleSwitch(MDSwitch):
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            # Toggle 'active' manually without triggering the Ripple/StateLayer logic
            self.active = not self.active
            return True
        return super().on_touch_down(touch)

class AboutDialogContent(MDBoxLayout):
    # This class matches the <AboutDialogContent> rule in your KV file
    pass

class DeleteContent(MDBoxLayout):
    """The content for the permanent delete confirmation dialog (defined in KV)."""
    pass

class PillBadge(MDLabel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.adaptive_size = True
        self.pos_hint = {"center_y": .5}
        self.padding = [dp(12), dp(6)]
        self.font_style = "Label"
        self.role = "small"
        self.bold = True
        self.halign = "center"
        
        with self.canvas.before:
            self.bg_color = Color(rgba=(0, 0, 0, 0)) 
            self.rect = RoundedRectangle()
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        min_width = dp(48)
        actual_width = max(self.width, min_width)
        offset_x = (actual_width - self.width)
        self.rect.pos = (self.x - offset_x, self.y)
        self.rect.size = (actual_width, self.height)
        self.rect.radius = [self.height / 2]

    def set_colors(self, bg_hex, text_hex="#FFFFFF"):
        self.theme_text_color = "Custom"
        self.bg_color.rgba = get_color_from_hex(bg_hex)
        self.text_color = get_color_from_hex(text_hex)

class CustomListItem(MDListItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.record_id = None
        self._long_press_event = None

    def on_touch_down(self, touch):
        # Only process if the touch is physically on this specific list item
        if self.collide_point(*touch.pos):
            # Schedule long press
            self._long_press_event = Clock.schedule_once(
                lambda dt: self.dispatch_long_press(), 0.5
            )
            # Pass the touch to super to allow ripple effect and normal clicks
            return super().on_touch_down(touch)
        
        # Explicitly return False if touch is outside to let other items breathe
        return False

    def on_touch_up(self, touch):
        # Always clean up the timer when the finger is lifted
        if self._long_press_event:
            Clock.unschedule(self._long_press_event)
            self._long_press_event = None
        return super().on_touch_up(touch)

    def dispatch_long_press(self):
        app = MDApp.get_running_app()
        # Use .get() to safely check for the screen manager
        sm = app.root.ids.get('screen_manager')
        
        if sm:
            current_screen = sm.get_screen(sm.current)
            if hasattr(current_screen, 'enter_selection_mode'):
                current_screen.enter_selection_mode(self)