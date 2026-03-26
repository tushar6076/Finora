from app.models import UserSetting, FinancialRecord

from datetime import timedelta, date


def check_export_range(app):
    settings = app.db.query(UserSetting).first()

    # Since transaction_date is now a DATE type, we compare with date objects
    query = app.db.query(FinancialRecord).filter(FinancialRecord.is_deleted == False)
    today = date.today()
    
    range_preference = getattr(settings, 'export_range', "Full History")

    if range_preference == "Current Month":
        start_date = today.replace(day=1)
        query = query.filter(FinancialRecord.transaction_date >= start_date)
        
    elif range_preference == "Last 3 Months":
        start_date = today - timedelta(days=90)
        query = query.filter(FinancialRecord.transaction_date >= start_date)
        
    elif range_preference == "Current Year":
        start_date = today.replace(month=1, day=1)
        query = query.filter(FinancialRecord.transaction_date >= start_date)
        
    records = query.all() 

    return records