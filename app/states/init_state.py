"""
Init State - Login to Pioneer, navigate to Rx Profile
Raises SystemException on failure.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print, set_screen_resolution, get_and_log_screen_resolution
from modules import login


def run():
    """
    Initialize Pioneer application for Insurance Bot.
    1. Set screen resolution to 1920x1080
    2. Kill & reopen Pioneer
    3. Login with credentials
    4. Navigate to Rx Profile view

    Raises:
        config.SystemException: If any init step fails
    """
    log_print("=" * 60)
    log_print("[INIT] Starting Pioneer Insurance Bot initialization")
    log_print("=" * 60)

    os.makedirs(os.path.dirname(config.RETRY_FILE_PATH), exist_ok=True)

    set_screen_resolution(1920, 1080)
    get_and_log_screen_resolution("after init")

    if not login.login_pioneer(
        config.PIONEER_SHORTCUT_PATH,
        config.PIONEER_USERNAME,
        config.PIONEER_PIN
    ):
        raise config.SystemException("Failed to login to Pioneer")

    log_print("[INIT] Pioneer ready for insurance processing")
