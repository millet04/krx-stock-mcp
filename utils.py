from zoneinfo import ZoneInfo
from datetime import datetime, timedelta

KST = ZoneInfo("Asia/Seoul")

def get_latest_open_date():
    """Return the latest market opening date"""
    d = datetime.now(KST).date() - timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    date = d.strftime('%Y%m%d')
    return date