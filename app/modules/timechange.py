"""
Pioneer Time Change Popup Handler
Clicks 'OK' if a time change window appears after login
"""
import time
from pywinauto.application import Application
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print


def handle_time_change():
    """
    Click 'OK' on the time change popup if it appears.
    Returns True always (popup is optional).
    """
    try:
        log_print("Checking for time change popup (waiting up to 5s)...")
        app = Application(backend="uia").connect(
            title_re=r".*PioneerRx.*",
            timeout=5
        )
        win = app.window(title_re=r".*PioneerRx.*")
        btn = win.child_window(title="OK", control_type="Button")
        btn.wait('visible', timeout=5)
        btn.click_input()
        time.sleep(0.5)

        log_print("Time change popup — clicked OK")

    except Exception:
        log_print("No time change window detected")

    return True


if __name__ == "__main__":
    handle_time_change()
