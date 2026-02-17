import logging
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)

LOGGER = logging.getLogger()

KST = ZoneInfo("Asia/Seoul")

def get_latest_open_date():
    """Return the latest market opening date."""
    today = datetime.now(KST).date()
    weekday = today.weekday()

    # Monday → Friday
    if weekday == 0:          
        d = today - timedelta(days=3)
    # Weekend → Thursday
    elif weekday >= 5:       
        d = today - timedelta(days=(weekday - 3))
    # Normal weekday → Yesterday
    else:                     
        d = today - timedelta(days=1)

    return d.strftime('%Y%m%d')