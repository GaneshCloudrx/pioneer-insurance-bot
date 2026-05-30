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


def _escape_send_keys(text):
    """
    Escape characters that pywinauto's send_keys treats as modifiers/groupers.

    The characters `+ ^ % ~ ( ) { }` are special in pywinauto's
    `send_keys` syntax. To send them literally each must be wrapped in `{}`,
    e.g. `(` -> `{(}`. Everything else is passed through unchanged.

    This is why typing "(P)BCBS" via `send_keys("(P)BCBS")` used to land as
    just "BCBS" in Pioneer — the leading `()` was parsed as an empty group.
    """
    if not text:
        return ""
    specials = {
        "(": "{(}",
        ")": "{)}",
        "{": "{{}",
        "}": "{}}",
        "+": "{+}",
        "^": "{^}",
        "%": "{%}",
        "~": "{~}",
    }
    out = []
    for ch in str(text):
        out.append(specials.get(ch, ch))
    return "".join(out)


_PRIMARY_LABEL_NOISE = {"primary:", "primary", "secondary:", "secondary", ""}


def _read_combo_value(combo):
    """
    Read the displayed value of a Pioneer "Primary:" / "Secondary:" combo.

    Pioneer uses a Win32 dropdown-list style combo (`CBS_DROPDOWNLIST`). The
    inner `Edit` child (auto_id="1001") is permanently hidden and its
    `Value.Value` is always blank — UIA inspector confirms this. The text the
    user sees is rendered by the ComboBox itself, exposed through the UIA
    `Value` pattern on the combo and/or the currently selected ListItem
    child.

    Strategies tried, first-non-empty wins:
        1. `combo.iface_value.CurrentValue` — UIA ValuePattern direct.
        2. `combo.legacy_properties()["Value"]` — MSAA bridge value.
        3. The selected ListItem child's `window_text()` /
           `SelectionItemPattern`.
        4. `combo.window_text()` — only used if it isn't the field label
           ("Primary:" etc.).

    Returns:
        str: The combo's displayed value, or "" if nothing readable.
    """
    if combo is None:
        return ""

    try:
        v = combo.get_value() if hasattr(combo, "get_value") else ""
        if v:
            return v
    except Exception:
        pass

    try:
        iv = getattr(combo, "iface_value", None)
        if iv is not None:
            v = iv.CurrentValue or ""
            if v:
                return v
    except Exception:
        pass

    try:
        v = combo.legacy_properties().get("Value", "") or ""
        if v:
            return v
    except Exception:
        pass

    try:
        if hasattr(combo, "selected_text"):
            v = combo.selected_text() or ""
            if v:
                return v
    except Exception:
        pass

    try:
        for child in combo.children():
            try:
                is_sel = False
                if hasattr(child, "is_selected"):
                    try:
                        is_sel = bool(child.is_selected())
                    except Exception:
                        is_sel = False
                if not is_sel:
                    isel = getattr(child, "iface_selection_item", None)
                    if isel is not None:
                        try:
                            is_sel = bool(isel.CurrentIsSelected)
                        except Exception:
                            is_sel = False
                if is_sel:
                    name = (child.window_text() or "").strip()
                    if name:
                        return name
            except Exception:
                continue
    except Exception:
        pass

    try:
        v = (combo.window_text() or "").strip()
        if v and v.lower() not in _PRIMARY_LABEL_NOISE:
            return v
    except Exception:
        pass

    return ""


def _read_primary_value(window, attempts=5, wait_between=0.4):
    """
    Read the Primary insurance combo on the Dispense tab, with retries.

    Pioneer needs a beat to repaint Edit Rx after Edit Patient closes, and
    the displayed text lives on the combo (not its hidden Edit child) — so
    we re-resolve the combo on every attempt and read it with
    `_read_combo_value` rather than peeking at the inner Edit.

    Returns:
        str: The current displayed value, or "" if every attempt was blank.
    """
    last_err = None
    for attempt in range(1, attempts + 1):
        try:
            primary_combo = window.child_window(title="Primary:", control_type="ComboBox")
            val = _read_combo_value(primary_combo)
            if val:
                if attempt > 1:
                    log_print(f"[PRIMARY] Read on attempt {attempt}: '{val}'")
                return val
        except Exception as e:  # noqa: BLE001
            last_err = e

        if attempt < attempts:
            time.sleep(wait_between)

    if last_err is not None:
        log_print(f"[PRIMARY] All read attempts failed (last error: {last_err})")
    else:
        log_print(
            f"[PRIMARY] All {attempts} read attempts returned blank — "
            f"treating Primary as empty"
        )
    return ""


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


def _verify_after_select(primary_edit, card_holder_id, attempts=4, wait_per_attempt=0.6,
                         window=None):
    """
    Re-read the Primary combo after `(P)<word>` + Tab and confirm the API
    cardholder digits now appear in the displayed value. Pioneer's
    auto-populate can lag a beat, so this polls a few times before giving up.

    The `window` argument lets us re-resolve the edit child on every poll
    (avoiding a stale UIA element handle); without it we fall back to the
    initially-passed `primary_edit` element.

    Returns:
        tuple(bool, str): (verified, final_value)
    """
    card_digits = _digits_only(card_holder_id)
    final_value = ""

    def _read_once():
        # Prefer the re-resolving reader when we have the parent window.
        if window is not None:
            try:
                return _read_primary_value(window, attempts=1, wait_between=0)
            except Exception:
                pass
        try:
            return primary_edit.legacy_properties().get("Value", "") or ""
        except Exception:
            return ""

    for attempt in range(1, attempts + 1):
        try:
            final_value = _read_once()
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

        # Read the Primary combo value with retries — Pioneer needs a beat
        # to repaint Edit Rx after Edit Patient closes.
        current_value = _read_primary_value(window)
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

        # Re-resolve the edit child for typing (avoids any stale handle).
        primary_combo = window.child_window(title="Primary:", control_type="ComboBox")
        primary_edit = primary_combo.child_window(auto_id="1001", control_type="Edit")

        suffix = _first_word(insurance_name) or _first_word(payer_name)

        primary_edit.click_input()
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        send_keys("{END}+{HOME}{DELETE}")
        time.sleep(config.TIMEOUT_AFTER_TYPE)

        if suffix:
            typed_display = f"(P){suffix}"
        else:
            typed_display = "(P)"
            log_print("[PRIMARY] No insurance/payer name available — typing bare '(P)'")

        # Escape the parens (`+ ^ % ~ ( ) { }` are special in
        # pywinauto.keyboard, so each must be wrapped in `{}` to land
        # as a literal).
        send_keys(_escape_send_keys(typed_display), with_spaces=True)
        time.sleep(0.3)
        send_keys("{TAB}")
        time.sleep(config.TIMEOUT_AFTER_CLICK)

        log_print(f"[PRIMARY] Typed {typed_display}{{TAB}} — verifying selection")
        verified, _ = _verify_after_select(primary_edit, card_holder_id, window=window)
        return verified

    except Exception as e:
        log_print(f"[PRIMARY] Failed to select primary insurance: {e}")
        return False


if __name__ == "__main__":
    if select_primary_insurance(
        payer_name="Optum/Informed Rx",
        bin_number="610011",
        card_holder_id="48454249",  
        pcn="BCBSMAN",
        insurance_name="Optum/Informed Rx",
    ):
        log_print("\nTEST PASSED")
    else:
        log_print("\nTEST FAILED")
