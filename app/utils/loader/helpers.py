from datetime import datetime, timedelta
from app.models import UserSetting, FinancialRecord
from app.utils.files import download_report, check_export_range

def run_auto_export_check(app):
    """
    Determines if an auto-export is due and filters the data 
    based on the user's preferred 'Export Range'.
    """
    # Fetch current settings
    settings = app.db.query(UserSetting).first()
    if not settings or not settings.auto_export_enabled:
        return

    # Check Frequency (Is it time to export?)
    freq_map = {"Daily": 1, "Weekly": 7, "Monthly": 30, "Quarterly": 90, "Yearly": 365}
    days_needed = freq_map.get(settings.export_frequency, 7)
    
    now = datetime.now()
    
    # Handle first-run scenario
    if not settings.last_export_date:
        settings.last_export_date = now - timedelta(days=days_needed + 1)
        app.db.commit()

    delta = now - settings.last_export_date
    
    if delta.days >= days_needed:
        records = check_export_range(app)
        if records:
            # We pass the app and records to your handler
            # download_report should handle the UI/Notification side
            success = download_report(records, is_auto=True)
            if success:
                settings.last_export_date = now
                app.db.commit()
        else:
            # Update date even if empty to prevent constant checking of an empty DB
            settings.last_export_date = now
            app.db.commit()


def auto_delete_bin(app):
    """
    Permanently deletes records from the bin that are older than the retention period.
    """
    settings = app.db.query(UserSetting).first()
    # Default to 30 days if not specified in settings
    retention_days = getattr(settings, 'bin_retention', 30)
    
    threshold = datetime.now() - timedelta(days=retention_days)

    # Find records marked as deleted whose 'deleted_at' timestamp is past the threshold
    expired_records = app.db.query(FinancialRecord).filter(
        FinancialRecord.is_deleted == True,
        FinancialRecord.deleted_at <= threshold
    ).all()

    if expired_records:
        count = len(expired_records)
        for record in expired_records:
            app.db.delete(record)
        
        try:
            app.db.commit()
            print(f"[Finora] Auto-Purge: Permanently removed {count} records from bin.")
        except Exception as e:
            app.db.rollback()
            print(f"[Finora] Auto-Purge Error: {e}")