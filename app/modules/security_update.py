"""
Pioneer Security Update Handler
Types password and clicks Log In if the security update screen appears after login.
"""
import time
from pywinauto.application import Application
from pywinauto.keyboard import send_keys
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print


def handle_security_update():
    """
    Check for Security Updates Required window after login.
    If found, type the Pioneer password and click Log In.
    Returns True always (popup is optional).
    """
    try:
        app = Application(backend="uia").connect(
            title_re= config.SELECTOR_LOGIN,
            timeout=3
        )
        sec_win = app.window(title_re= config.SELECTOR_LOGIN)
        sec_win.wait("visible", timeout=3)
        log_print("Security Update screen detected")

        pwd_field = sec_win.child_window(auto_id="password", control_type="Edit")
        pwd_field.click_input()
        time.sleep(0.3)
        send_keys(config.PIONEER_PASSWORD, with_spaces=True)
        time.sleep(0.3)

        login_btn = sec_win.child_window(auto_id="kc-login", control_type="Button")
        login_btn.click_input()
        log_print("Security Update — Log In clicked")
        time.sleep(5)

    except Exception:
        pass

    return True


if __name__ == "__main__":
    handle_security_update()
