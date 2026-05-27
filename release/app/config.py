"""
Configuration file for Pioneer Data Entry Automation
Central source of truth for all timeouts, selectors, credentials, and settings
"""
import base64
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BOT_ROOT = os.path.dirname(BASE_DIR)
ENV_FILE = os.path.join(DEFAULT_BOT_ROOT, "config", ".env")


def _load_env_file(path):
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def _get_bool(name, default):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


_load_env_file(ENV_FILE)

BOT_ROOT = os.environ.get("BOT_BASE_DIR", DEFAULT_BOT_ROOT)

# ============================================================================
# EXCEPTION TYPES
# ============================================================================

class BusinessRuleException(Exception):
    """Expected business errors (patient not found, drug not found, NON-MATCHED, etc.)"""
    pass

class SystemException(Exception):
    """Unexpected system errors (app crash, timeout, element not found, etc.)"""
    pass

# ============================================================================
# MACHINE / BOT IDENTIFICATION
# ============================================================================

MACHINE_NAME = os.environ.get("MACHINE_NAME_OVERRIDE", os.environ.get("COMPUTERNAME", "UNKNOWN")).upper()
BOT_NAME = os.environ.get("BOT_NAME", "Pioneer DE Bot")

# ============================================================================
# REPORT DEFAULTS
# ============================================================================

PHARMACY_NAME = os.environ.get("PHARMACY_NAME", "Cloudrx")
PRESCRIPTION_TYPE = os.environ.get("PRESCRIPTION_TYPE", "escript")

# ============================================================================
# PIONEER APPLICATION
# ============================================================================

PIONEER_SHORTCUT_PATH = os.environ.get("PIONEER_SHORTCUT_PATH", os.path.join(BASE_DIR, "application", "PioneerRx.lnk"))
PIONEER_USERNAME = os.environ.get("PIONEER_USERNAME", "")
PIONEER_PASSWORD = os.environ.get("PIONEER_PASSWORD", "")
PIONEER_PIN = os.environ.get("PIONEER_PIN", "")

# ============================================================================
# TIMEOUTS (seconds)
# ============================================================================

TIMEOUT_LOGIN_WINDOW = 60
TIMEOUT_MAIN_WINDOW = 30
TIMEOUT_FILE_SAVE = 30
TIMEOUT_SEARCH_WINDOW = 15
TIMEOUT_E1_LOOKUP = 15
TIMEOUT_NO_RECORDS = 10
BOT_STOP_HOUR = int(os.environ.get("BOT_STOP_HOUR", "23"))
BOT_STOP_MINUTE = int(os.environ.get("BOT_STOP_MINUTE", "59"))
TIMEOUT_ELEMENT_VISIBLE = 5
TIMEOUT_ELEMENT_EXISTS = 5
TIMEOUT_POPUP_CHECK = 1
TIMEOUT_AFTER_CLICK = 0.3
TIMEOUT_AFTER_TYPE = 0.2
TIMEOUT_AFTER_TAB = 0.3
TIMEOUT_AFTER_SEARCH = 3.0


# ============================================================================
# RETRY SETTINGS
# ============================================================================

MAX_SYSTEM_RETRIES = 3
MAX_API_RETRIES = 3
MAX_INSURANCE_LOOPS = 3

# ============================================================================
# WINDOW SELECTORS (regex patterns for pywinauto title_re)
# ============================================================================

SELECTOR_LOGIN = r".*Logon to PioneerRx.*"
SELECTOR_MAIN = r".*(MainForm|Fill Requests).*"
SELECTOR_FILL_REQUESTS = r".*(Fill Requests|Rx Profile|MainForm).*"
SELECTOR_EDIT_RX = r".*(Edit|Fill Rx).*"
# This selector should contains all possible windows that can appear when editing an rx
SELECTOR_EDIT_RX_FULL = r".*(Edit|Fill Rx|Fill Requests|Search For a Prescriber|Search for|Search For Compounds).*"
SELECTOR_SEARCH_PATIENT = r".*Search for Patients.*"
SELECTOR_SEARCH_PRESCRIBER = r".*Search For a Prescriber.*"
SELECTOR_SEARCH_DRUG = r".*Search for a Prescription Item.*"
SELECTOR_SEARCH_COMPOUND = r".*Search For Compounds.*"
SELECTOR_EDIT_PATIENT = r".*Edit Patient.*"
SELECTOR_EDIT_PRESCRIBER = r".*Edit Prescriber.*"
SELECTOR_ELIGIBILITY = r".*Patient Eligibility Check.*"

# ============================================================================
# API CONFIGURATION
# ============================================================================

API_BASE_URL = os.environ.get("API_BASE_URL", "https://portal.reuniterx.com/api/v1/webservice/endpoint/")
API_SIG_ENDPOINT = os.environ.get("API_SIG_ENDPOINT", API_BASE_URL + "rpa_sig_translations.php")
API_QUEUE_ENDPOINT = os.environ.get("API_QUEUE_ENDPOINT", API_BASE_URL + "rpa_prescription_queue.php")
API_TIMEOUT = int(os.environ.get("API_TIMEOUT", "30"))
PORTAL_USERNAME = os.environ.get("PORTAL_USERNAME", "")
PORTAL_PASSWORD = os.environ.get("PORTAL_PASSWORD", "")

# ============================================================================
# FILE PATHS
# ============================================================================

QUEUE_EXPORT_DIR = os.environ.get("QUEUE_EXPORT_DIR", os.path.join(BOT_ROOT, "queue_export_files"))
LOGS_DIR = os.environ.get("LOGS_DIR", os.path.join(BOT_ROOT, "logs"))
REPORTS_DIR = os.environ.get("REPORTS_DIR", os.path.join(BOT_ROOT, "reports"))
RETRY_FILE_PATH = os.environ.get("RETRY_FILE_PATH", os.path.join(BOT_ROOT, "runtime", "retry.txt"))

# ============================================================================
# API LOGGING
# ============================================================================

API_AUTH_HEADER = os.environ.get(
    "API_AUTH_HEADER",
    f"Basic {base64.b64encode(f'{PORTAL_USERNAME}:{PORTAL_PASSWORD}'.encode()).decode()}" if PORTAL_USERNAME or PORTAL_PASSWORD else "",
)
API_LOG_ENABLED = _get_bool("API_LOG_ENABLED", True)
API_LOG_ENDPOINT = os.environ.get("API_LOG_ENDPOINT", "https://devc.reuniterx.com/api/v1/webservice/endpoint/rpa_get_bot_status.php")
API_LOG_BATCH_SIZE = int(os.environ.get("API_LOG_BATCH_SIZE", "10"))
API_LOG_BATCH_INTERVAL = int(os.environ.get("API_LOG_BATCH_INTERVAL", "5"))

# ============================================================================
# SCREEN RECORDING
# ============================================================================

RECORDINGS_DIR = os.environ.get("RECORDINGS_DIR", os.path.join(BOT_ROOT, "recordings"))
RECORDING_FPS = int(os.environ.get("RECORDING_FPS", "5"))
RECORDING_QUALITY = os.environ.get("RECORDING_QUALITY", "medium")
RECORDING_MAX_SIZE_GB = int(os.environ.get("RECORDING_MAX_SIZE_GB", "2"))
