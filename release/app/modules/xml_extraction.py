"""
Pioneer XML Extraction Module
Clicks Escript tab, Original Message Xml tab, and copies XML content
"""
import time
from pywinauto.application import Application
from pywinauto.keyboard import send_keys
import pyperclip
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print


# Global app reference
_app = None


def connect_to_pioneer():
    """Connect to running Pioneer."""
    global _app
    
    try:
        if _app is None:
            _app = Application(backend="uia").connect(
                title_re=".*(Edit|Fill Rx|Fill Requests).*",
                timeout=config.TIMEOUT_ELEMENT_VISIBLE
            )
        return True
    except Exception as e:
        log_print(f"Failed to connect: {e}")
        return False


def extract_xml():
    """
    Click Escript tab, Original Message Xml tab, and copy XML content.
    
    Returns:
        tuple: (success: bool, xml_string: str or None)
    """
    global _app
    
    if not connect_to_pioneer():
        return False, None
    
    try:
        # Screen Selector: Edit an Rx window
        edit_rx_window = _app.window(title_re=".*(Edit|Fill Rx|Fill Requests).*")
        edit_rx_window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        edit_rx_window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        
        # Target Selector: Escript tab item (name is dynamic e.g. "Escript [3]")
        escript_tab = edit_rx_window.child_window(title_re="Escript.*", control_type="TabItem")
        escript_tab.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        escript_tab.click_input()
        time.sleep(0.5)
        log_print("✓ Escript tab clicked")

        # Target Selector: Original Message Xml tab
        xml_tab = edit_rx_window.child_window(title="Original Message Xml", control_type="TabItem")
        xml_tab.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        xml_tab.click_input()
        time.sleep(0.5)
        log_print("✓ Original Message Xml tab clicked")

        # Target Selector: XML text box
        xml_textbox = edit_rx_window.child_window(auto_id="txtXml", control_type="Edit")
        xml_textbox.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        xml_textbox.click_input()
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        
        # Select all and copy
        send_keys("^a")
        time.sleep(config.TIMEOUT_AFTER_TYPE)
        send_keys("^c")
        time.sleep(config.TIMEOUT_AFTER_CLICK)
        
        xml_string = pyperclip.paste()
        log_print(f"✓ XML copied ({len(xml_string)} chars)")
        return True, xml_string
        
    except Exception as e:
        log_print(f"Failed to extract XML: {e}")
        return False, None


if __name__ == "__main__":
    #Need to call priority window handle popup
    from priority_window_handle_popup import click_cancel_priority
    success = click_cancel_priority()
    if success:
        log_print("\n✓ Priority window handle popup cancelled")
    else:
        log_print("\n✗ Priority window handle popup not cancelled")

    success, xml_string = extract_xml()
    if success:
        log_print(f"\nXML preview: {xml_string[:200]}...")
        log_print("\n✓ TEST PASSED")
    else:
        log_print("\n✗ TEST FAILED")
