"""
Pioneer Software Feedback Popup Handler
Clicks 'Prefer to not answer' if feedback popup appears after login
"""
import time
from pywinauto.application import Application
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print


def click_prefer_not_answer():
    """
    Click 'Prefer to not answer' on the Software Feedback popup if it appears.

    Returns:
        bool: True if clicked, False if popup not found
    """
    try:
        app = Application(backend="uia").connect(
            title_re=config.SELECTOR_LOGIN,
            timeout=config.TIMEOUT_POPUP_CHECK
        )
        login_window = app.window(title_re=config.SELECTOR_LOGIN)
        btn = login_window.child_window(auto_id="uxNotAnswered", control_type="Button")
        btn.wait('visible', timeout=config.TIMEOUT_POPUP_CHECK)
        btn.click_input()
        time.sleep(0.5)

        log_print("Feedback popup — clicked Prefer to not answer")
        return True

    except Exception:
        return False


if __name__ == "__main__":
    if click_prefer_not_answer():
        log_print("\nTEST PASSED")
    else:
        log_print("\nTEST FAILED")
