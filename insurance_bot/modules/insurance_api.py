"""
Insurance API Module
Fetches patient insurance data from the API.
Returns structured data with patient info, insurance details, and prescription list.

Expected API response format:
{
  "patient": {
    "patient_id": "P123",
    "first_name": "John",
    "last_name": "Doe",
    "dob": "1985-04-12"
  },
  "insurance": {
    "payer": "Aetna",
    "member_id": "AET12345",
    "group_number": "GRP100",
    "bin": "610502",
    "pcn": "AETNA"
  },
  "prescriptions": [
    {"rx_number": "RX1001", "status": "ACTIVE", "drug_name": "Metformin"},
    {"rx_number": "RX1002", "status": "ACTIVE", "drug_name": "Metformin2"}
  ]
}
"""
import base64
import requests
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print


def fetch_insurance_data():
    """
    Fetch next patient insurance record from the API queue.

    Returns:
        dict or None: Parsed API response with patient, insurance, prescriptions
                      None if no records available or request failed.
    """
    auth_string = base64.b64encode(
        f"{config.PORTAL_USERNAME}:{config.PORTAL_PASSWORD}".encode()
    ).decode()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {auth_string}"
    }
    payload = {
        "server_name": config.MACHINE_NAME,
        "bot_name": config.HEARTBEAT_BOT_NAME,
    }

    for attempt in range(config.MAX_API_RETRIES):
        try:
            resp = requests.post(
                config.INSURANCE_API_URL,
                json=payload,
                headers=headers,
                timeout=config.API_TIMEOUT,
            )
            if not resp.ok:
                log_print(f"[API] HTTP {resp.status_code} (attempt {attempt + 1})")
                continue

            data = resp.json()
            status = str(data.get("status", "")).upper()

            if status == "NO_RECORDS":
                log_print("[API] No records available")
                return None

            if status != "SUCCESS":
                log_print(f"[API] Unexpected status: {status}")
                return None

            record = data.get("data", data)
            if not record.get("patient") or not record.get("insurance"):
                log_print("[API] Missing patient or insurance data in response")
                return None

            prescriptions = record.get("prescriptions", [])
            rx_numbers = [p["rx_number"] for p in prescriptions if p.get("rx_number")]

            log_print(f"[API] Fetched: {record['patient']['first_name']} {record['patient']['last_name']} "
                      f"| Insurance: {record['insurance']['payer']} "
                      f"| Rx count: {len(rx_numbers)}")

            return record

        except requests.exceptions.Timeout:
            log_print(f"[API] Timeout (attempt {attempt + 1}/{config.MAX_API_RETRIES})")
        except requests.exceptions.RequestException as e:
            log_print(f"[API] Request failed: {e} (attempt {attempt + 1})")
        except Exception as e:
            log_print(f"[API] Unexpected error: {e}")
            return None

    log_print(f"[API] All {config.MAX_API_RETRIES} attempts failed")
    return None


def update_status(patient_id, status, remark=""):
    """
    Update the API with processing result for a patient.

    Args:
        patient_id: The patient ID from the API response
        status: "success", "skipped", or "failed"
        remark: Additional detail about the outcome
    """
    auth_string = base64.b64encode(
        f"{config.PORTAL_USERNAME}:{config.PORTAL_PASSWORD}".encode()
    ).decode()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {auth_string}"
    }
    payload = {
        "patient_id": patient_id,
        "status": status,
        "remark": remark[:500],
        "server_name": config.MACHINE_NAME,
        "bot_name": config.HEARTBEAT_BOT_NAME,
    }

    try:
        resp = requests.post(
            config.INSURANCE_API_URL,
            json=payload,
            headers=headers,
            timeout=config.API_TIMEOUT,
        )
        result = resp.json()
        log_print(f"[API UPDATE] {status.upper()} — {remark}")
        return True
    except Exception as e:
        log_print(f"[API UPDATE] Failed: {e}")
        return False
