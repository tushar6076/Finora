from kivy.metrics import dp
from kivy.clock import Clock
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText

from app.models import FinancialRecord

colors = {
    'success': "#20D489",
    'warning': "#DBD837",
    'error': "#E96767",
}

def show_msg(text, status=None, size_x=0.95):
    """
    Displays a snackbar message. 
    :param text: Message to display
    :param color: Optional list/tuple for text color, e.g., (1, 0, 0, 1) for Red
    """
    # Define the text element first
    snackbar_text = MDSnackbarText(
        text=text,
        theme_text_color="Custom" if status else "Primary",
    )
    
    # Apply custom color only if provided
    if status:
        snackbar_text.text_color = colors[status]

    # Create and open the snackbar
    MDSnackbar(
        snackbar_text,
        y=dp(24),
        pos_hint={"center_x": 0.5},
        size_hint_x=size_x,
        # Optional: background_color=... if you want to change the bar itself
    ).open()


def update_nav_badges(app):
    try:
        # Access the drawer IDs via the app root
        nav = app.root.ids.content_drawer.ids
        q = app.db.query(FinancialRecord).filter_by(is_deleted=False)
        
        # 1. Main Badges
        nav.badge_all.text = str(q.count())
        nav.badge_bin.text = str(app.db.query(FinancialRecord).filter_by(is_deleted=True).count())
        
        # 2. Filter Badges (Credit, Debit, Receipt)
        nav.badge_credit.text = str(q.filter_by(transaction_type="Credit").count())
        nav.badge_debit.text = str(q.filter_by(transaction_type="Debit").count())
        nav.badge_receipt.text = str(q.filter_by(transaction_type="Receipt").count())
        
    except Exception as e:
        print(f"Error updating badges: {e}")


def sync_nav_state(app, screen_name):
    def perform_sync(dt):
        try:
            nav = app.root.ids.content_drawer.ids
            target = None

            if screen_name == "home":
                home_screen = app.root.ids.screen_manager.get_screen("home")
                current_cat = getattr(home_screen, 'current_category', "All")
                mapping = {
                    "All": nav.nav_all, "Credit": nav.nav_credit,
                    "Debit": nav.nav_debit, "Receipt": nav.nav_receipt
                }
                target = mapping.get(current_cat)
            elif screen_name == "bin":
                target = nav.nav_bin

            if target:
                # --- THE GUARD ---
                # We set a flag that the KV code will check
                target.is_syncing = True 
                
                # This triggers the M3 Menu selection logic (fixes Settings highlight)
                target.dispatch('on_release')
                
                # Reset the flag so the user can click it manually later
                Clock.schedule_once(lambda x: setattr(target, 'is_syncing', False), 0.1)

        except Exception as e:
            print(f"❌ Sync Error: {e}")

    Clock.schedule_once(perform_sync, 0.1)