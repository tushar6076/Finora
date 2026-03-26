from android.permissions import check_permission, Permission
from kivymd.app import MDApp
from . import (
    PythonActivity, Context, sdk_int,
    NotificationManager, NotificationBuilder, NotificationChannelObj
)

def android_notify(title, message):
    """
    Triggers a native Android notification that matches the Finora theme.
    Fixes the 'value too large to convert to jint' error by wrapping the color value.
    """
    if check_permission(Permission.POST_NOTIFICATIONS):
        try:
            activity = PythonActivity.mActivity
            notification_service = activity.getSystemService(Context.NOTIFICATION_SERVICE)

            # 1. Setup Notification Channel (API 26+)
            channel_id = "finora_channel_id"
            channel_name = "Finora Notifications"
            
            if sdk_int >= 26:
                # Importance level 3 is 'DEFAULT'
                importance = NotificationManager.IMPORTANCE_DEFAULT
                channel = NotificationChannelObj(channel_id, channel_name, importance)
                notification_service.createNotificationChannel(channel)
                builder = NotificationBuilder(activity, channel_id)
            else:
                builder = NotificationBuilder(activity)

            # 2. Apply Dynamic Theme Color (With Signed 32-bit Fix)
            app = MDApp.get_running_app()
            color = app.theme_cls.primaryColor
            
            # Calculate Unsigned ARGB
            unsigned_color = (
                (int(255) << 24) |            # Alpha
                (int(color[0] * 255) << 16) |  # Red
                (int(color[1] * 255) << 8) |   # Green
                (int(color[2] * 255))          # Blue
            )
            
            # CONVERSION FIX:
            # If the value exceeds the positive range of a signed 32-bit int,
            # subtract 2^32 to wrap it into the negative range Java expects.
            android_color = unsigned_color if unsigned_color < 2147483648 else unsigned_color - 4294967296
            
            builder.setColor(int(android_color))

            # 3. Configure Notification Content
            builder.setSmallIcon(activity.getApplicationInfo().icon)
            builder.setContentTitle(title)
            builder.setContentText(message)
            builder.setAutoCancel(True)

            # 4. Fire Notification
            notification = builder.build()
            # ID 1 overrides the previous notification; use a unique ID for stacking
            notification_service.notify(1, notification)
            
        except Exception as e:
            print(f"Native Notification Error: {e}")
            # Optional fallback to KivyMD Snackbar/Toast if JNI fails
            from app.utils.ui import show_msg
            show_msg(text=message)

    else:
        # Permission denied: Fallback to in-app UI message
        from app.utils.ui import show_msg
        show_msg(text=message)