"""
Insurance API Module
Fetches patient insurance data from the API endpoint:
http://portal.reuniterx.com/api/v1/webservice/endpoint/rpa_get_pending_patient_insurance_to_sync.php

Expected API response format:
{
    "code": 200,
    "status": "SUCCESS",
    "message": "Successful",
    "data": {
        "cld_patient_id": 189458,
        "patient": {
            "patient_id": "1eccad7e-f901-4390-aca8-cadda64cca3d",
            "first_name": "Marlene",
            "last_name": "Leal",
            "dob": "1997-07-18"
        },
        "insurance": {
            "primary": {
                "payer": "Cigna",
                "card_holder_id": "111513983",
                "group_number": "CIGUG0000658718",
                "bin": "017010",
                "pcn": "0518GWH"
            }
        },
        "latest_rx_sent_date": "2026-01-16",
        "prescriptions": [
            {"rx_number": "1448269", "status": "", "drug_name": "Gonal-F Rff Redi-Ject 450 Unit Pen"},
            {"rx_number": "1445188", "status": "", "drug_name": "Pregnyl 10,000 Unit * Vial"}
        ]
    }
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
    Fetch next patient insurance record from the API.

    Returns:
        dict or None: The 'data' portion of the API response containing
                      cld_patient_id, patient, insurance, prescriptions.
                      None if no records available or request failed.
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": config.API_AUTH_HEADER,
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
            print(resp.text)
            if not resp.ok:
                log_print(f"[API] HTTP {resp.status_code} (attempt {attempt + 1})")
                continue

            response = resp.json()
            status = str(response.get("status", "")).upper()

            if status == "NO_RECORDS":
                log_print("[API] No records available")
                return None

            if status not in ("SUCCESS", ""):
                log_print(f"[API] Unexpected status: {status}")
                return None

            record = response.get("data", response)
            if not record.get("patient") or not record.get("insurance"):
                log_print("[API] Missing patient or insurance data in response")
                return None

            patient = record.get("patient", {})
            insurance_primary = record.get("insurance", {}).get("primary", {})
            prescriptions = record.get("prescriptions", [])
            rx_numbers = [p["rx_number"] for p in prescriptions if p.get("rx_number")]

            log_print(f"[API] Fetched: {patient.get('first_name', '')} {patient.get('last_name', '')} "
                      f"| Insurance: {insurance_primary.get('payer', '')} "
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


def update_status(cld_patient_id, status):
    """
    Update the API with processing result for a patient.
    Endpoint: rpa_update_pending_patient_insurance_sync_status.php

    Args:
        cld_patient_id: The cld_patient_id from the API response
        status: "pms_synced", "failed", or "skipped"
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": config.API_AUTH_HEADER,
    }
    payload = {
        "cld_patient_id": cld_patient_id,
        "status": status,
    }

    try:
        resp = requests.post(
            config.INSURANCE_UPDATE_API_URL,
            json=payload,
            headers=headers,
            timeout=config.API_TIMEOUT,
        )
        log_print(f"[API UPDATE] {status} — cld_patient_id={cld_patient_id}")
        return True
    except Exception as e:
        log_print(f"[API UPDATE] Failed: {e}")
        return False

#test get api
fetch_insurance_data()