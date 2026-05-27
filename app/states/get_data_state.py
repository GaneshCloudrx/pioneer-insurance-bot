"""
Get Data State - Fetch next patient insurance record from API.
Returns the full record or None if no records available.
"""
import sys, os
import time
import base64
import requests
from datetime import datetime
from pywinauto.keyboard import send_keys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print, stop_recording, start_recording, restart_server
from modules import insurance_api, login


def _heartbeat():
    """Send heartbeat to portal and return active status."""
    auth = base64.b64encode(f"{config.PORTAL_USERNAME}:{config.PORTAL_PASSWORD}".encode()).decode()
    body = {"server_name": config.MACHINE_NAME, "bot_name": config.HEARTBEAT_BOT_NAME}
    for attempt in range(3):
        try:
            resp = requests.post(
                config.HEARTBEAT_URL, json=body,
                headers={"Authorization": f"Basic {auth}"},
                timeout=config.API_TIMEOUT
            )
            if resp.ok:
                data = resp.json().get("data", {})
                if isinstance(data, list):
                    data = data[0] if data else {}
                active = data.get("active", "1") if isinstance(data, dict) else "1"
                log_print(f"[HEARTBEAT] active={active}")
                return str(active).strip()
        except Exception as e:
            log_print(f"[HEARTBEAT] Attempt {attempt + 1} failed: {e}")
    return "1"


def run():
    """
    Get next insurance record to process.

    Returns:
        dict or None: API record with patient, insurance, prescriptions data.
                      None if no records available.

    Raises:
        config.SystemException: If API call fails fatally
    """
    log_print("=" * 60)
    log_print("[GET_DATA] Fetching next insurance record")
    log_print("=" * 60)

    # Daily restart check
    now = datetime.now()
    if not config.DEV_MODE and config.get_last_restart_date() != now.date() and \
       (now.hour, now.minute) >= (config.BOT_RESTART_HOUR_ACTUAL, config.BOT_RESTART_MINUTE_ACTUAL):
        config.set_last_restart_date(now.date())
        log_print(f"[GET_DATA] Daily restart time reached ({config.BOT_RESTART_HOUR_ACTUAL}:{config.BOT_RESTART_MINUTE_ACTUAL:02d})")
        restart_server("Daily scheduled restart")

    # Clear any stale popups
    send_keys("{ESC}")
    time.sleep(0.5)
    send_keys("{ESC}")
    time.sleep(0.5)

    # Heartbeat check
    active = _heartbeat()
    if active == "0":
        log_print("[GET_DATA] Bot deactivated by portal — entering wait loop")
        stop_recording()
        login.kill_pioneer()
        while _heartbeat() == "0":
            log_print("[GET_DATA] Still inactive — sleeping 5 minutes")
            time.sleep(300)
        log_print("[GET_DATA] Bot reactivated — restarting from login")
        start_recording()
        raise config.SystemException("Bot reactivated after pause")

    # Fetch next record from API
    record = insurance_api.fetch_insurance_data()

    if record is None:
        log_print("[GET_DATA] No records available")
        return None

    patient = record.get("patient", {})
    insurance_primary = record.get("insurance", {}).get("primary", {})
    prescriptions = record.get("prescriptions", [])
    rx_numbers = [p["rx_number"] for p in prescriptions if p.get("rx_number")]

    log_print(f"[GET_DATA] Patient: {patient.get('first_name', '')} {patient.get('last_name', '')}")
    log_print(f"[GET_DATA] Insurance: {insurance_primary.get('payer', '')} (BIN: {insurance_primary.get('bin', '')})")
    log_print(f"[GET_DATA] Rx Numbers ({len(rx_numbers)}): {rx_numbers}")

    return record
