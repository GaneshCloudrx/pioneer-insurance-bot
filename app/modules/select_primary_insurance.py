"""
Select Primary Insurance Module
Ensures the Primary insurance combo on the Dispense tab matches the API plan.

The Primary field is a combo box (auto_id="1001") under the "Primary:" label.
Its displayed value has the format:

    "(P)PAYER_NAME - BIN - MEMBER_ID - PCN"

    e.g.  "(P)BCBS OF Michigan - 610011 - WYO919752481 - BCBSMAN"

Strategy:
  1. Read the current value. If the API cardholder id digits already appear
     anywhere inside it, leave the field alone — that's enough proof that
     the right plan is selected (cardholder ids are effectively unique per
     patient/plan in Pioneer, so a digits-substring match is sufficient and
     avoids brittle BIN/PCN parsing).
  2. Otherwise clear the field and type "(P)<first word of insurance name>"
     followed by Tab. Pioneer will auto-complete the matching primary plan
     from the patient's pay-methods list. Using the first word of the plan
     name (instead of bare "(P)") disambiguates when the patient has more
     than one Primary configured.
  3. **Verify** — re-read the combo value after Tab and confirm the
     cardholder digits are now present. This same verification runs for
     the first Rx and every upcoming Rx, so a mis-selection can never
     silently propagate across the patient's prescriptions.

The first word should come from the Display Name captured when the plan
was added/matched in Edit Patient — pass it via `insurance_name`.
"""
import time
from pywinauto.keyboard import send_keys
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print
from modules.app_cache import get_pioneer_app


def _digits_only(value):
    """Return only the numeric digits from `value`."""
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def get_primary_insurance_value():
    """
    Read the current value of the Primary insurance field in Dispense tab.

    Returns:
        str: Current value of the Primary field, or empty string on failure
    """
    try:
        app = get_pioneer_app()
        window = app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)

        primary_combo = window.child_window(title="Primary:", control_type="ComboBox")
        primary_edit = primary_combo.child_window(auto_id="1001", control_type="Edit")
        current_value = primary_edit.legacy_properties().get("Value", "")
        log_print(f"[PRIMARY] Current value: {current_value}")
        return current_value

    except Exception as e:
        log_print(f"[PRIMARY] Failed to read Primary field: {e}")
        return ""


def _first_word(value):
    """Return the first whitespace-separated token of `value`, or ""."""
    if not value:
        return ""
    tokens = str(value).strip().split()
    return tokens[0] if tokens else ""


def _primary_already_set(current_value, card_holder_id):
    """
    True when the API cardholder id digits already appear in the Primary
    combo's displayed value.

    Both sides are reduced to digits before comparison so letter prefixes
    (e.g. API "Wyo919752481" vs combo "WYO919752481") don't matter. Any
    substring hit counts — Pioneer prints the cardholder id verbatim inside
    the combo value so a match is enough proof the right plan is selected.
    """
    card_digits = _digits_only(card_holder_id)
    if not card_digits:
        return False
    current_digits = _digits_only(current_value)
    return card_digits in current_digits


def _verify_after_select(primary_edit, card_holder_id, attempts=3, wait_per_attempt=0.6):
    """
    Re-read the Primary combo after `(P)<word>` + Tab and confirm the API
    cardholder digits now appear in the displayed value. Pioneer's
    auto-populate can lag a beat, so this polls a few times before giving up.

    Returns:
        tuple(bool, str): (verified, final_value)
            * verified    - True if cardholder digits found in the combo.
            * final_value - The combo's last read value (for logging).
    """
    card_digits = _digits_only(card_holder_id)
    final_value = ""
    for attempt in range(1, attempts + 1):
        try:
            final_value = primary_edit.legacy_properties().get("Value", "") or ""
        except Exception as e:
            log_print(f"[PRIMARY] Verify attempt {attempt} read failed: {e}")
            final_value = ""

        if card_digits and card_digits in _digits_only(final_value):
            log_print(
                f"[PRIMARY] Verified on attempt {attempt}: cardholder digits "
                f"'{card_digits}' present in '{final_value}'"
            )
            return True, final_value

        if attempt < attempts:
            time.sleep(wait_per_attempt)

    log_print(
        f"[PRIMARY] VERIFY FAILED: cardholder digits '{card_digits}' not found "
        f"in Primary value '{final_value}' after {attempts} attempt(s)"
    )
    return False, final_value


def select_primary_insurance(
    payer_name="",
    bin_number="",
    card_holder_id="",
    pcn="",
    insurance_name="",
):
    """
    Ensure the Primary insurance combo on the Dispense tab is the target plan.

    Verify-first, then re-select:
      * If the API cardholder digits already appear inside the current combo
        value, leave the field alone.
      * Otherwise clear the combo and type "(P)<first word>" + Tab so
        Pioneer auto-populates the matching plan. The "first word" is taken
        from `insurance_name` (preferred — captured from Edit Patient) and
        falls back to `payer_name`.

    Args:
        payer_name: Insurance payer name from the API. Used as fallback
            for the "(P)<word>" shortcut and for logging.
        bin_number: API BIN. Accepted for signature compatibility and
            logging; not used for matching (cardholder id is enough).
        card_holder_id: API cardholder id. Its digits drive the match.
        pcn: PCN. Accepted for signature compatibility; informational only.
        insurance_name: Display name captured from Edit Patient (existing
            row) or the Pay Method window (newly-added row). Its first word
            drives the "(P)<word>" shortcut.

    Returns:
        bool: True if, at the end of the call, the Primary combo's displayed
              value contains the API cardholder digits (the field is on the
              target plan). False on hard UI failure OR when the post-Tab
              verification cannot confirm the target plan was selected.
    """
    try:
        app = get_pioneer_app()
        window = app.window(title_re=config.SELECTOR_EDIT_RX_FULL)
        window.wait('visible', timeout=config.TIMEOUT_ELEMENT_VISIBLE)
        window.set_focus()
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        primary_combo = window.child_window(title="Primary:", control_type="ComboBox")
        primary_edit = primary_combo.child_window(auto_id="1001", control_type="Edit")

        current_value = primary_edit.legacy_properties().get("Value", "") or ""
        target_digits = _digits_only(card_holder_id)
        log_print(
            f"[PRIMARY] Current: '{current_value}' | "
            f"Target cardholder digits='{target_digits}' | "
            f"insurance_name='{insurance_name}'"
        )

        if _primary_already_set(current_value, card_holder_id):
            log_print(
                f"[PRIMARY] Already on target insurance "
                f"(cardholder digits '{target_digits}' present)"
            )
            return True

        suffix = _first_word(insurance_name) or _first_word(payer_name)

        primary_edit.click_input()
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        send_keys("{END}+{HOME}{DELETE}")
        time.sleep(config.TIMEOUT_AFTER_TYPE)

        if suffix:
            typed = f"(P){suffix}"
        else:
            typed = "(P)"
            log_print("[PRIMARY] No insurance/payer name available — typing bare '(P)'")

        send_keys(typed, with_spaces=True)
        time.sleep(0.3)
        send_keys("{TAB}")
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        log_print(f"[PRIMARY] Typed {typed}{{TAB}} — verifying selection")
        verified, _ = _verify_after_select(primary_edit, card_holder_id)
        return verified

    except Exception as e:
        log_print(f"[PRIMARY] Failed to select primary insurance: {e}")
        return False


if __name__ == "__main__":
    if select_primary_insurance(
        payer_name="Bc/Bs Minnesota",
        bin_number="610011",
        card_holder_id="919752481001",
        pcn="BCBSMAN",
        insurance_name="BCBS OF Michigan",
    ):
        log_print("\nTEST PASSED")
    else:
        log_print("\nTEST FAILED")
