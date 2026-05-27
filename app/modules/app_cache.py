"""
Shared Pioneer Application connection cache.
Avoids repeated Application(backend="uia").connect() calls across modules
during the fill-fields phase of a single transaction.
"""
from pywinauto.application import Application
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

_cached_app = None


def get_pioneer_app():
    """Return cached Pioneer Application connection, connecting if needed."""
    global _cached_app
    if _cached_app is not None:
        return _cached_app
    _cached_app = Application(backend="uia").connect(
        title_re=config.SELECTOR_EDIT_RX_FULL,
        timeout=config.TIMEOUT_ELEMENT_VISIBLE,
    )
    return _cached_app


def reset():
    """Clear cached connection. Call between transactions."""
    global _cached_app
    _cached_app = None
