import os
from kivy.utils import platform
from app.models import UserSetting

# Import the pre-initialized JNI classes from the parent __init__
from . import (
    PythonActivity, Intent, Uri, View, String, File, FileProvider,
    Color, WindowManager, DocumentsContract, ContentResolver
)
from .notification import android_notify
from android.runnable import run_on_ui_thread

def set_android_status_bar(app_instance):
    if platform != 'android': return

    @run_on_ui_thread
    def _set_status_bar_native():
        try:
            activity = PythonActivity.mActivity
            window = activity.getWindow()
            
            # Enable drawing on system bars
            window.addFlags(WindowManager.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS)
            
            # Ensure transparency flags are cleared for both top and bottom
            window.clearFlags(WindowManager.FLAG_TRANSLUCENT_STATUS)
            window.clearFlags(WindowManager.FLAG_TRANSLUCENT_NAVIGATION) # Added for Footer
            
            decor_view = window.getDecorView()
            
            if app_instance.theme_cls.theme_style == "Light":
                # STATUS BAR (Top): FLAG_LIGHT_STATUS_BAR
                # NAV BAR (Bottom): FLAG_LIGHT_NAVIGATION_BAR (Value: 16)
                # Combining both so both top and bottom icons are dark
                vis_flags = View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR | 16
                decor_view.setSystemUiVisibility(vis_flags)
                
                # Set white backgrounds for both
                window.setStatusBarColor(Color.WHITE) 
                window.setNavigationBarColor(Color.WHITE)
            else:
                # White icons for dark background
                decor_view.setSystemUiVisibility(0)
                
                # Match both to your dark theme color
                dark_color = Color.parseColor("#121212")
                window.setStatusBarColor(dark_color)
                window.setNavigationBarColor(dark_color)
                
        except Exception as e:
            print(f"System Bar JNI Error: {e}")

    _set_status_bar_native()

def handle_saf_result(app, request_code, result_code, intent):
    """Processes folder selection result and persists the URI for Finora exports."""
    if request_code == 4001 and result_code == -1: # -1 is RESULT_OK
        try:
            uri = intent.getData()
            uri_string = uri.toString()
            
            # Persist Permission (Vital for reboots)
            take_flags = intent.getFlags() & (
                Intent.FLAG_GRANT_READ_URI_PERMISSION | 
                Intent.FLAG_GRANT_WRITE_URI_PERMISSION
            )
            ContentResolver.takePersistableUriPermission(uri, take_flags)
            
            # Save to Database
            settings = app.db.query(UserSetting).first()
            if settings:
                settings.export_path = uri_string
                app.db.commit()
                
                # Perform delayed write if a task was waiting
                temp_path = getattr(app, 'current_temp_file', "")
                filename = getattr(app, 'current_filename', "")

                if temp_path and filename:
                    save_to_authorized_uri(settings, temp_path, uri_string, filename)
                    app.current_temp_file = ""
                    app.current_filename = ""
                
                return True, "Path Saved!"
        except Exception as e:
            print(f"SAF Result Processing Failed: {e}")
            
    return False, None

def open_file_chooser():
    """Opens the Android System Directory Picker."""
    try:
        intent = Intent(Intent.ACTION_OPEN_DOCUMENT_TREE)
        PythonActivity.mActivity.startActivityForResult(intent, 4001)
        return True
    except Exception as e:
        print(f"Android SAF Picker Failed: {e}")
        return False

def save_to_authorized_uri(settings, temp_file_path, tree_uri_string, filename):
    try:
        tree_uri = Uri.parse(tree_uri_string)
        doc_id = DocumentsContract.getTreeDocumentId(tree_uri)
        parent_uri = DocumentsContract.buildDocumentUriUsingTree(tree_uri, doc_id)

        mime_type = "application/pdf" if filename.endswith('.pdf') else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        
        new_file_uri = DocumentsContract.createDocument(
            ContentResolver, parent_uri, mime_type, filename
        )

        if new_file_uri is None: return False

        # Open with "wt" mode for API 34 compatibility
        out_stream = ContentResolver.openOutputStream(new_file_uri, "wt")
        with open(temp_file_path, 'rb') as f:
            out_stream.write(f.read())
        
        out_stream.flush()
        out_stream.close()

        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        if settings.notifications_enabled:
            android_notify(
                title="Finora: Report Saved",
                message=f"Check your {os.path.basename(settings.export_path or 'storage')}"
            )

        return True
    except Exception as e:
        print(f"SAF Write Error: {e}")
        return False

def share_file_android(filepath, title="Share Report"):
    try:    
        from jnius import cast
        import os

        # Ensure we have a clean absolute path
        abs_path = os.path.abspath(filepath)
        file_obj = File(abs_path)
        
        if not file_obj.exists():
            print(f"[Finora] File missing for share: {abs_path}")
            return

        activity = PythonActivity.mActivity
        # CRITICAL: This MUST match your buildozer.spec package name + .fileprovider
        authority = "org.test.finora.fileprovider"
        
        # 1. Generate URI
        # This is where the IllegalArgumentException usually triggers
        file_uri = FileProvider.getUriForFile(activity, authority, file_obj)
        
        # 2. Setup Intent
        share_intent = Intent(Intent.ACTION_SEND)
        mime = "application/pdf" if abs_path.endswith('.pdf') else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        
        share_intent.setType(mime)
        # Wrap the URI in a Parcelable cast for Java signature matching
        parcelable_uri = cast('android.os.Parcelable', file_uri)
        share_intent.putExtra(Intent.EXTRA_STREAM, parcelable_uri)
        
        # Add basic permission flags
        share_intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        share_intent.addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION)

        # 3. THE ACTUAL MAGIC FIX (Granting permissions to receivers)
        pm = activity.getPackageManager()
        # 65536 = MATCH_DEFAULT_ONLY
        res_info_list = pm.queryIntentActivities(share_intent, 65536) 
        
        for i in range(res_info_list.size()):
            res = res_info_list.get(i)
            pkg_name = res.activityInfo.packageName
            # We use the raw file_uri here to tell Android exactly which app gets access
            activity.grantUriPermission(pkg_name, file_uri, Intent.FLAG_GRANT_READ_URI_PERMISSION)
        
        # 4. Create Chooser
        j_title = cast('java.lang.CharSequence', String(title))
        chooser = Intent.createChooser(share_intent, j_title)
        
        # Important: The chooser itself needs the NEW_TASK flag when called from Kivy
        chooser.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK) 
        
        activity.startActivity(chooser)
        print(f"[Finora] Share Intent started for: {filepath}")

    except Exception as e:
        print(f"[Finora] Android Share Failed: {e}")


def send_support_email(recipient, subject, body):
    """Specific Android Intent to target ONLY email apps."""
    try:
        activity = PythonActivity.mActivity
        
        # Use mailto: to force email app selection
        uri_text = f"mailto:{recipient}?subject={Uri.encode(subject)}&body={Uri.encode(body)}"
        uri = Uri.parse(uri_text)
        
        intent = Intent(Intent.ACTION_SENDTO, uri)
        # This flag ensures that only apps capable of handling 'mailto' (emails) respond
        intent.setData(uri) 
        
        activity.startActivity(intent)
    except Exception as e:
        print(f"Android Email Intent Failed: {e}")
        # Fallback to the generic plyer method if JNI fails
        from plyer import email
        email.send(recipient=recipient, subject=subject, text=body)