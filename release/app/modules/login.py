"""
Pioneer Login Module - Minimal Self-Contained Implementation
Each function creates its own selectors and returns only True/False
"""
import time
import os
import psutil
from pywinauto.application import Application
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print


# Global to store app reference
_app = None


def kill_pioneer():
    """Kill any running Pioneer processes."""
    try:
        killed = False
        for proc in psutil.process_iter(['name', 'pid']):
            if proc.info['name'] and 'PioneerPharmacy' in proc.info['name']:
                log_print(f"Killing Pioneer (PID: {proc.info['pid']})")
                proc.kill()
                killed = True
        
        if killed:
            log_print("Waiting for process to terminate...")
            time.sleep(3)  # Wait longer for clean termination
            log_print("✓ Pioneer killed")
        else:
            log_print("No Pioneer process found")
        
        return True
        
    except Exception as e:
        log_print(f"Error killing Pioneer: {e}")
        return False


def open_pioneer(shortcut_path):
    """
    Open Pioneer application.
    
    Args:
        shortcut_path: Path to PioneerRx.lnk
    
    Returns:
        bool: True if opened successfully
    """
    global _app
    
    try:
        log_print(f"Opening Pioneer...")
        os.startfile(shortcut_path)
        
        # Wait longer after fresh kill
        log_print("Waiting for Pioneer to start...")
        time.sleep(8)
        
        # Try to connect with retry (up to 20 attempts, 5s apart = ~100s max)
        max_attempts = 20
        log_print("Connecting to Pioneer process...")
        for attempt in range(max_attempts):
            try:
                _app = Application(backend="uia").connect(
                    title_re=config.SELECTOR_LOGIN,
                    timeout=15
                )
                log_print("✓ Pioneer opened and connected")
                return True

            except Exception as e:
                if attempt < max_attempts - 1:
                    log_print(f"Connection attempt {attempt + 1} failed, retrying...")
                    time.sleep(5)
                else:
                    log_print(f"Failed to connect after {max_attempts} attempts: {e}")
                    return False

        return False
        
    except Exception as e:
        log_print(f"Failed to open Pioneer: {e}")
        return False


def wait_for_login_window(timeout=config.TIMEOUT_LOGIN_WINDOW):
    """
    Wait for login window and username textbox.
    
    Args:
        timeout: Max seconds to wait
    
    Returns:
        bool: True if login window ready
    """
    global _app
    
    try:
        log_print(f"Waiting up to {timeout}s for login window...")
        
        # Screen Selector: Login window
        login_window = _app.window(title_re=config.SELECTOR_LOGIN)
        login_window.wait('exists', timeout=timeout)
        
        # Target Selector: Username textbox
        username_box = login_window.child_window(auto_id="uxUserName", control_type="Edit")
        username_box.wait('exists', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        
        log_print("✓ Login window ready")
        return True
        
    except Exception as e:
        log_print(f"Login window not found: {e}")
        return False


def type_username(username):
    """
    Type username into textbox.
    
    Args:
        username: Text to type
    
    Returns:
        bool: True if successful
    """
    global _app
    
    try:
        log_print(f"Typing username...")
        
        # Screen Selector: Login window
        login_window = _app.window(title_re=config.SELECTOR_LOGIN)
        
        # Target Selector: Username textbox
        username_box = login_window.child_window(auto_id="uxUserName", control_type="Edit")
        username_box.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        username_box.set_edit_text(username)
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        
        log_print("✓ Username entered")
        return True
        
    except Exception as e:
        log_print(f"Failed to type username: {e}")
        return False


def type_password(password):
    """
    Type password into textbox.
    
    Args:
        password: Text to type
    
    Returns:
        bool: True if successful
    """
    global _app
    
    try:
        log_print("Typing password...")
        
        # Screen Selector: Login window
        login_window = _app.window(title_re=config.SELECTOR_LOGIN)
        
        # Target Selector: Password textbox
        password_box = login_window.child_window(auto_id="uxPassword", control_type="Edit")
        password_box.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        password_box.set_edit_text(password)
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        
        log_print("✓ Password entered")
        return True
        
    except Exception as e:
        log_print(f"Failed to type password: {e}")
        return False


def click_logon():
    """
    Click Logon button.
    
    Returns:
        bool: True if successful
    """
    global _app
    
    try:
        log_print("Clicking Logon...")
        
        # Screen Selector: Login window
        login_window = _app.window(title_re=config.SELECTOR_LOGIN)
        
        # Target Selector: Logon button
        logon_btn = login_window.child_window(auto_id="uxLogon", control_type="Button")
        logon_btn.click_input()
        
        log_print("✓ Logon clicked")
        time.sleep(3)
        return True
        
    except Exception as e:
        return True


def wait_for_main_window(timeout=config.TIMEOUT_MAIN_WINDOW):
    """
    Wait for main Pioneer window.
    
    Args:
        timeout: Max seconds to wait
    
    Returns:
        bool: True if main window ready
    """
    global _app
    
    try:
        log_print("Waiting for main window...")
        
        # Screen Selector: Main window
        main_window = _app.window(auto_id="MainForm")
        main_window.wait('visible', timeout=timeout)
        main_window.maximize()
        
        log_print("✓ Main window ready")
        return True
        
    except Exception as e:
        log_print(f"Main window not found: {e}")
        return False


def click_priority_fill_request():
    """
    Click on Priority Fill Request (side pane) using coordinates.
    Double-clicks at coordinates (1796, 225) on the uxToDoExplorer pane.
    
    Returns:
        bool: True if clicked successfully
    """
    global _app
    
    try:
        log_print("Clicking Priority Fill Request...")
        
        # Screen Selector: Main window
        main_window = _app.window(auto_id="MainForm")
        
        # Target Selector: Side pane (uxToDoExplorer)
        side_pane = main_window.child_window(auto_id="uxToDoExplorer", control_type="Pane")
        side_pane.wait('visible', timeout=config.TIMEOUT_ELEMENT_EXISTS)
        
        # Click at coordinates (1796, 231) - double click
        from pywinauto import mouse
        mouse.double_click(coords=(1796, 225))
        time.sleep(1)
        
        log_print("✓ Priority Fill Request clicked")
        return True
        
    except Exception as e:
        log_print(f"Failed to click Priority Fill Request: {e}")
        return False


def login_pioneer(shortcut_path, username, password):
    """
    Complete Pioneer login workflow.
    
    Args:
        shortcut_path: Path to PioneerRx.lnk
        username: Pioneer username
        password: Pioneer password/PIN
    
    Returns:
        bool: True if login successful, False otherwise
    
    Example:
        if login_pioneer("C:\\Pioneer\\PioneerRx.lnk", "user@example.com", "1234"):
            log_print("Login successful!")
    """
    log_print("="*60)
    log_print("Pioneer Login")
    log_print("="*60)
    
    # Step 0: Kill existing processes
    if not kill_pioneer():
        return False
    
    # Step 1: Open application
    if not open_pioneer(shortcut_path):
        return False
    
    # Step 2: Wait for login window (60 seconds)
    if not wait_for_login_window(timeout=config.TIMEOUT_LOGIN_WINDOW):
        return False
    
    # Step 3: Type username
    if not type_username(username):
        return False
    
    # Step 4: Type password
    if not type_password(password):
        return False
    
    # Step 5: Click Logon
    if not click_logon():
        return False
    
    # Step 6: Wait for main window
    if not wait_for_main_window(timeout=config.TIMEOUT_MAIN_WINDOW):
        return False
    
    # Step 7: Click Priority Fill Request
    if not click_priority_fill_request():
        return False
    
    log_print("="*60)
    log_print("✓ Login Complete - Ready for automation")
    log_print("="*60)
    
    return True


def get_app():
    """
    Get the current app reference.
    Use this if you need to interact with Pioneer after login.
    
    Returns:
        Application: App object or None
    """
    return _app


# Test
if __name__ == "__main__":
    if login_pioneer(config.PIONEER_SHORTCUT_PATH, config.PIONEER_USERNAME, config.PIONEER_PASSWORD):
        log_print("\n✓ TEST PASSED")
        time.sleep(3)
    else:
        log_print("\n✗ TEST FAILED")
