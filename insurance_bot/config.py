"""
Configuration for Pioneer Insurance Bot
Checks if insurance exists on patient profile and adds it if missing.
"""
import os
import hashlib
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOT_ROOT = BASE_DIR
ENV_FILE = os.path.join(os.path.dirname(BASE_DIR), "config", ".env")


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

_load_env_file(ENV_FILE)

# ============================================================================
# EXCEPTION TYPES
# ============================================================================

class BusinessRuleException(Exception):
    pass

class SystemException(Exception):
    pass

# ============================================================================
# MACHINE / BOT IDENTIFICATION
# ============================================================================

MACHINE_NAME = os.environ.get("COMPUTERNAME", "UNKNOWN").upper()
BOT_NAME = "Pioneer Insurance Bot"

# ============================================================================
# PIONEER APPLICATION
# ============================================================================

PIONEER_SHORTCUT_PATH = os.path.join(os.path.dirname(BASE_DIR), "app", "application", "PioneerRx.lnk")
PIONEER_USERNAME = os.environ.get("PIONEER_USERNAME", "")
PIONEER_PASSWORD = os.environ.get("PIONEER_PASSWORD", "")
PIONEER_PIN = os.environ.get("PIONEER_PIN", "")
PIONEER_ID_NAME = os.environ.get("PIONEER_ID_NAME", "")

PHARMACY_NAME = os.environ.get("PHARMACY_NAME", "Cloudrx")
DEV_MODE = os.environ.get("DEV_MODE", "").strip().lower() == "true"
LOGIN_SERVER = ""
if PHARMACY_NAME == "Metro":
    LOGIN_SERVER = "Metro Drugs - NY"

# ============================================================================
# TIMEOUTS (seconds)
# ============================================================================

TIMEOUT_LOGIN_WINDOW = 60
TIMEOUT_MAIN_WINDOW = 30
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

# ============================================================================
# WINDOW SELECTORS
# ============================================================================

SELECTOR_LOGIN = r".*Logon to PioneerRx.*"
SELECTOR_MAIN = r".*(MainForm|Fill Requests).*"
SELECTOR_FILL_REQUESTS = r".*(Fill Requests|Rx Profile|MainForm).*"
SELECTOR_RX_PROFILE = r".*Rx Profile.*"
SELECTOR_EDIT_RX = r".*(Edit|Fill Rx).*"
SELECTOR_EDIT_RX_FULL = r".*(Edit|Fill Rx|Fill Requests|Search For a Prescriber|Search for|Search For Compounds|Alerts).*"
SELECTOR_EDIT_PATIENT = r".*Edit Patient.*"

# ============================================================================
# API CONFIGURATION
# ============================================================================

INSURANCE_API_URL = os.environ.get("INSURANCE_API_URL", "https://portal.reuniterx.com/api/v1/webservice/endpoint/rpa_insurance_queue.php")
API_TIMEOUT = 30

# Portal credentials (reuse from parent bot env)
PORTAL_USERNAME = os.environ.get("PORTAL_USERNAME", "cloud")
PORTAL_PASSWORD = os.environ.get("PORTAL_PASSWORD", "Cloud@20234")

API_AUTH_HEADER = "Basic Y2xvdWQ6Q2xvdWRAMjAyMzQ="

# ============================================================================
# API LOGGING
# ============================================================================

API_LOG_ENABLED = True
API_LOG_ENDPOINT = "https://devc.reuniterx.com/api/v1/webservice/endpoint/rpa_get_bot_status.php"
API_LOG_BATCH_SIZE = 10
API_LOG_BATCH_INTERVAL = 5

HEARTBEAT_URL = "https://portal.reuniterx.com/api/v1/webservice/endpoint/rpa_get_bot_status.php"
HEARTBEAT_BOT_NAME = "PioneerInsuranceBot"

# ============================================================================
# FILE PATHS
# ============================================================================

LOGS_DIR = os.path.join(BOT_ROOT, "logs")
REPORTS_DIR = os.path.join(BOT_ROOT, "reports")
RECORDINGS_DIR = os.path.join(BOT_ROOT, "recordings")
DATA_DIR = os.path.join(BOT_ROOT, "data")

RECORDING_FPS = 5
RECORDING_QUALITY = "medium"
RECORDING_MAX_SIZE_GB = 2
