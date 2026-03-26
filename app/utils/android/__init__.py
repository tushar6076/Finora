from jnius import autoclass

# Core Activity
PythonActivity = autoclass('org.kivy.android.PythonActivity')
activity = PythonActivity.mActivity # Shortcut for internal use

# System Versions
Build_VERSION = autoclass('android.os.Build$VERSION')
sdk_int = Build_VERSION.SDK_INT

# Classes
Intent = autoclass('android.content.Intent')
Color = autoclass('android.graphics.Color')
Context = autoclass('android.content.Context')
String = autoclass('java.lang.String')
File = autoclass('java.io.File')
# Correct for modern Buildozer/AndroidX
FileProvider = autoclass('androidx.core.content.FileProvider') 

# Notifications
NotificationBuilder = autoclass('android.app.Notification$Builder')
NotificationManager = autoclass('android.app.NotificationManager')
NotificationChannelObj = autoclass('android.app.NotificationChannel')

# UI & Window
Uri = autoclass('android.net.Uri')
View = autoclass('android.view.View')
WindowManager = autoclass('android.view.WindowManager$LayoutParams')

# Storage & SAF
DocumentsContract = autoclass('android.provider.DocumentsContract')
# Best practice: access through activity
ContentResolver = activity.getContentResolver() 
Settings = autoclass('android.provider.Settings')

# 2. Expose high-level functions
from .permission import request_permissions_for_android
from .helpers import (
    set_android_status_bar, 
    open_file_chooser, 
    save_to_authorized_uri, 
    handle_saf_result, 
    share_file_android,
    send_support_email
)
from .notification import android_notify

__all__ = [
    'request_permissions_for_android', 
    'set_android_status_bar',
    'open_file_chooser', 
    'save_to_authorized_uri', 
    'android_notify',
    'handle_saf_result',
    'share_file_android',
    'send_support_email'
]