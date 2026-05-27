"""
Get Data State - Fetch next patient insurance record from API
Returns the full record or None if no records available.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print
from modules import insurance_api


def run():
    """
    Get next insurance record to process.

    Returns:
        dict or None: API record with patient, insurance, prescriptions data.
                      None if no records available.

    Raises:
        config.SystemException: If API call fails unexpectedly
    """
    log_print("=" * 60)
    log_print("[GET_DATA] Fetching next insurance record")
    log_print("=" * 60)

    record = insurance_api.fetch_insurance_data()

    if record is None:
        log_print("[GET_DATA] No records available")
        return None

    patient = record.get("patient", {})
    insurance = record.get("insurance", {})
    prescriptions = record.get("prescriptions", [])
    rx_numbers = [p["rx_number"] for p in prescriptions if p.get("rx_number")]

    log_print(f"[GET_DATA] Patient: {patient.get('first_name', '')} {patient.get('last_name', '')}")
    log_print(f"[GET_DATA] Insurance: {insurance.get('payer', '')} (BIN: {insurance.get('bin', '')})")
    log_print(f"[GET_DATA] Rx Numbers: {rx_numbers}")

    return record
