"""
Pioneer Queue Download Module
Clicks first step in queue using coordinates
"""
import time
import os
from datetime import datetime
from pywinauto.application import Application
from pywinauto import mouse
from pywinauto.keyboard import send_keys
import pyperclip
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules import login
import config
from modules.helper import log_print


# Global app reference
_app = None
_toolbar_click_coords = None


def connect_to_pioneer():
    """Connect to running Pioneer and cache toolbar click position."""
    global _app, _toolbar_click_coords
    
    try:
        if _app is None:
            _app = Application(backend="uia").connect(
                title_re=config.SELECTOR_FILL_REQUESTS,
                timeout=config.TIMEOUT_ELEMENT_VISIBLE
            )
        
        if _toolbar_click_coords is None:
            window = _app.window(title_re=config.SELECTOR_FILL_REQUESTS)
            toolbar = window.child_window(
                auto_id="moreHeaderToolStrip1", control_type="ToolBar"
            ) 
            toolbar.wait('visible', timeout=config.TIMEOUT_ELEMENT_EXISTS)
            rect = toolbar.rectangle()
            _toolbar_click_coords = (rect.right - 20, (rect.top + rect.bottom) // 2)
            log_print(f"Toolbar position cached: {_toolbar_click_coords}")
        
        return True
    except Exception as e:
        log_print(f"Failed to connect: {e}")
        return False


def click_priority_fill_request():
    """
    Click the Fill Request toolbar to refresh the Fill Requests pane.
    Uses the queue window's own app reference since the parent window
    changes after login.
    
    UI Hierarchy (PioneerPharmacy):
      Window (MainForm) > cntWorkAreaPanel > FillRequestQueueWorkArea >
      pnlBackground > uxFillRequestQueueControl > cntQueue >
      uxRxQueueGrid > pnlTableLayoutPanel > ToolBar (moreHeaderToolStrip1)
    
    Click: MiddleRight, OffsetX=-130, OffsetY=0
    Retry: 3 attempts, 5s wait between retries.
    
    Returns:
        bool: True if clicked successfully
    """
    global _app

    try:
        log_print("Clicking Priority Fill Request...")
        
        # Screen Selector: Main window
        #main_window = _app.window(title_re=config.SELECTOR_FILL_REQUESTS)
        
        # Target Selector: Side pane (uxToDoExplorer)
        #side_pane = main_window.child_window(auto_id="uxToDoExplorer", control_type="Pane")
        #side_pane.wait('visible', timeout=config.TIMEOUT_ELEMENT_EXISTS)
        
        # Click at coordinates (1796, 231) - double click
        from pywinauto import mouse
        mouse.double_click(coords=(1796, 225))
        time.sleep(1)
        
        log_print("✓ Priority Fill Request clicked")
        return True
        
    except Exception as e:
        log_print(f"Failed to click Priority Fill Request: {e}")
        return False


def click_first_step():
    """
    Click the toolbar menu button using cached absolute screen coordinates.
    Position is resolved once during connect_to_pioneer() and reused.
    
    Returns:
        bool: True if successful
    """
    try:
        if _toolbar_click_coords is None:
            log_print("Toolbar position not cached")
            return False

        mouse.click(coords=_toolbar_click_coords)
        time.sleep(0.5)
        
        log_print("✓ First step clicked")
        return True
        
    except Exception as e:
        log_print(f"Failed to click: {e}")
        return False


def press_down_and_enter():
    """
    Press down arrow twice and then press Enter.
    
    Returns:
        bool: True if successful
    """
    try:
        log_print("Pressing down arrow twice...")
        send_keys("{DOWN}")
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        send_keys("{DOWN}")
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        
        log_print("Pressing Enter...")
        send_keys("{ENTER}")
        time.sleep(0.5)
        
        log_print("✓ Navigation complete")
        return True
        
    except Exception as e:
        log_print(f"Failed to navigate: {e}")
        return False


def connect_to_filesave_dialog():
    """Connect to file save dialog."""
    global _app_for_filesave
    
    try:
        if _app_for_filesave is None:
            log_print("Connecting to file save dialog...")
            _app_for_filesave = Application(backend="uia").connect(
                title_re=".*Export search results to Excel.*",
                timeout=config.TIMEOUT_ELEMENT_VISIBLE
            )
            log_print("✓ Connected to file save dialog")
        return True
    except Exception as e:
        log_print(f"Failed to connect to file save: {e}")
        return False


def type_filename():
    """
    Type filename in Save dialog using Ctrl+V.
    Uses config.QUEUE_EXPORT_DIR for the save directory.
    
    Returns:
        tuple: (success: bool, file_path: str or None)
    """
    global _app
    
    try:
        os.makedirs(config.QUEUE_EXPORT_DIR, exist_ok=True)
        current_datetime = datetime.now().strftime("%Y_%m_%dT%H_%M_%S")
        full_path = os.path.join(config.QUEUE_EXPORT_DIR, current_datetime)
        log_print(f"Saving as: {full_path}")
        
        # Copy to clipboard
        pyperclip.copy(full_path)
        time.sleep(1)
        
        # Paste with Ctrl+V
        send_keys("^v")
        time.sleep(0.5)
        
        log_print("Pressing Enter to save...")
        send_keys("{ENTER}")
        time.sleep(1)
        
        # Wait for file to exist (30 seconds)
        log_print("Waiting for file to be created...")
        file_path = full_path + ".xlsx"
        for i in range(30):
            if os.path.exists(file_path):
                log_print(f"✓ File saved: {file_path}")
                return True, file_path
            time.sleep(1)
        
        log_print(f"File not found after 30 seconds: {file_path}")
        return False, None
        
    except Exception as e:
        log_print(f"Failed to save file: {e}")
        return False


def download_queue():
    """
    Download queue workflow.
    Saves the exported file to config.QUEUE_EXPORT_DIR.
    
    Returns:
        tuple: (success: bool, file_path: str or None)
    
    Example:
        success, file_path = download_queue()
        if success:
            log_print(f"Downloaded to: {file_path}")
    """
    global _app, _toolbar_click_coords
    _app = None
    _toolbar_click_coords = None

    if not connect_to_pioneer():
        return False, None

    if not click_priority_fill_request():
        return False, None

    if not click_first_step():
        return False, None
    
    if not press_down_and_enter():
        return False, None
    
    success, file_path = type_filename()
    if not success:
        return False, None
    
    return True, file_path

# Test
if __name__ == "__main__":
    success, file_path = download_queue()
    
    if success:
        log_print(f"\n✓ TEST PASSED - File: {file_path}")
        time.sleep(3)
    else:
        log_print("\n✗ TEST FAILED")