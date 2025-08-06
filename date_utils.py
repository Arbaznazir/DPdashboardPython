import datetime

def get_past_dates_only():
    """
    Get today's date and return True if a given date is in the past
    """
    today = datetime.datetime.now().date()
    return today

def is_past_date(date_str):
    """
    Check if a date string (YYYY-MM-DD) is in the past
    """
    if not date_str:
        return False
    
    try:
        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        today = datetime.datetime.now().date()
        return date_obj < today
    except Exception as e:
        print(f"Error checking if date is past: {e}")
        return False
