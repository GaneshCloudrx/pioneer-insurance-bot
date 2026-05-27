"""
Init State - Login to Pioneer, open Fill Requests, handle startup popups
Raises SystemException on failure
"""
import sys
import os
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from modules.helper import log_print, set_screen_resolution, get_and_log_screen_resolution
from modules import login, reminder, noactiveitem_


def run():
    """
    Initialize Pioneer application.
    1. Ensure correct screen resolution
    2. Kill & reopen Pioneer
    3. Login with credentials
    4. Open Fill Requests
    5. Handle startup popups (reminder, no active item)

    Raises:
        config.SystemException: If any init step fails
    """
    log_print("=" * 60)
    log_print("[INIT] Starting Pioneer initialization")
    log_print("=" * 60)

    now = datetime.now()
    if (now.hour, now.minute) >= (config.BOT_STOP_HOUR, config.BOT_STOP_MINUTE):
        log_print(f"[INIT] Stop time reached ({config.BOT_STOP_HOUR}:{config.BOT_STOP_MINUTE:02d}) — ending session")
        raise config.SystemException("Stop time reached")

    os.makedirs(os.path.dirname(config.RETRY_FILE_PATH), exist_ok=True)
    with open(config.RETRY_FILE_PATH, 'w') as f:
        f.write("")

    set_screen_resolution(1920, 1080)
    get_and_log_screen_resolution("after init")

    if not login.login_pioneer(
        config.PIONEER_SHORTCUT_PATH,
        config.PIONEER_USERNAME,
        config.PIONEER_PASSWORD
    ):
        raise config.SystemException("Failed to login to Pioneer")

    log_print("[INIT] Pioneer ready")
