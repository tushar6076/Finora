from android.permissions import check_permission, request_permissions, Permission
from . import PythonActivity, Intent, Uri, Settings
from app.models import UserSetting

def request_permissions_for_android(app, settings=False):
    """
    Handles modern Android permissions. Focuses on Notifications (API 33+)
    and redirects to settings only if permissions were previously denied.
    """
    # Internet is granted by default in manifest, but POST_NOTIFICATIONS 
    # must be requested at runtime on Android 13+
    perms = [Permission.POST_NOTIFICATIONS]
    
    def callback(permissions, grants):
        # This runs after the user clicks 'Allow' or 'Deny'
        settings = app.db.query(UserSetting).first()
        if settings and permissions:
            try:
                notif_idx = permissions.index(Permission.POST_NOTIFICATIONS)
                # Update DB based on user's choice
                settings.notifications_enabled = grants[notif_idx]
                app.db.commit()
            except ValueError:
                pass 

    # 1. Check if we already have the permissions
    if not all(check_permission(p) for p in perms):
        # 2. Request them if we don't
        request_permissions(perms, callback)
    else:
        # 3. If they are already granted, we don't bother the user.
        # NOTE: We only redirect to Settings if the user is manually 
        # trying to re-enable them after a previous hard 'Deny'.
        if settings: open_app_settings()

def open_app_settings():
    """
    Helper to send user to Android System Settings for Finora.
    Useful if they denied permissions and want to fix it later.
    """
    activity = PythonActivity.mActivity
    intent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS)
    uri = Uri.parse(f"package:{activity.getPackageName()}")
    intent.setData(uri)
    activity.startActivity(intent)