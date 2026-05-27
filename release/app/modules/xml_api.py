"""
Pioneer XML API Module
Submits XML data to API with retry logic
"""
import base64
import time
import requests
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print


def submit_xml(row_id, xml_data, max_retries=config.MAX_API_RETRIES):
    """
    Submit XML data to API with retry logic.
    
    Args:
        row_id: API ID from unique_prescription
        xml_data: XML string to submit
        max_retries: Max retry attempts
    
    Returns:
        tuple: (success: bool, response_json: dict)
    """
    if not row_id or not xml_data:
        log_print("Missing row_id or xml_data")
        return False, None
    
    auth_string = base64.b64encode(f"{config.PORTAL_USERNAME}:{config.PORTAL_PASSWORD}".encode()).decode()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {auth_string}"
    }
    payload = {"id": row_id, "xml": xml_data}
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                delay = 2 * (2 ** (attempt - 1))
                log_print(f"Retry {attempt + 1}/{max_retries} after {delay}s...")
                time.sleep(delay)
            
            response = requests.post(config.API_SIG_ENDPOINT, json=payload, headers=headers, timeout=config.API_TIMEOUT)
            
            if response.status_code == 200:
                result = response.json()
                status = str(result.get("status", "")).upper()
                log_print(f"API Response: {result}")
                return status == "SUCCESS", result
            else:
                log_print(f"HTTP {response.status_code}: {response.text}")
                return False, None
                
        except requests.exceptions.Timeout:
            log_print(f"Timeout (attempt {attempt + 1}/{max_retries})")
        except requests.exceptions.RequestException as e:
            log_print(f"Request failed: {e} (attempt {attempt + 1}/{max_retries})")
    
    log_print(f"All {max_retries} attempts failed")
    return False, None


if __name__ == "__main__":
    # Test with hardcoded values (remove after testing)
    test_id = 7777
    with open("test/xml.txt", "r") as f:
        test_xml = f.read()
    
    success, response_json = submit_xml(test_id, test_xml)
    if success:
        log_print(f"\n✓ TEST PASSED | Response: {response_json}")
    else:
        log_print("\n✗ TEST FAILED")
