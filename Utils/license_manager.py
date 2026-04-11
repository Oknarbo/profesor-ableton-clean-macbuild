"""
Gumroad license validation for Profesor Abelton.
One-time activation: verifies once online, stores result locally.
Machine-bound token: activation token is tied to hardware so sharing
a config file does not bypass the license check.
"""

import hashlib
import os
import uuid

import requests

GUMROAD_PRODUCT_ID = "qal9nt0wnhOl93mcBKgf4g=="
GUMROAD_VERIFY_URL = "https://api.gumroad.com/v2/licenses/verify"


def is_dev_mode() -> bool:
    """Returns True if PROFESOR_DEV_MODE=1 is set in environment (developer bypass)."""
    return os.getenv("PROFESOR_DEV_MODE", "").strip() == "1"


def verify_license(license_key: str) -> dict:
    """
    Verify a Gumroad license key against the Profesor Abelton product.

    Returns:
        {"valid": bool, "message": str}

    Behaviour:
    - Developer bypass: always valid if PROFESOR_DEV_MODE=1
    - Empty key: invalid (no crash, just a message)
    - Network error: invalid with descriptive message (app still works)
    - Gumroad success: valid
    - Gumroad failure: invalid with Gumroad's message
    """
    if is_dev_mode():
        return {"valid": True, "message": "Developer mode — license check skipped."}

    if not license_key or not license_key.strip():
        return {"valid": False, "message": "No license key entered."}

    try:
        response = requests.post(
            GUMROAD_VERIFY_URL,
            data={
                "product_id": GUMROAD_PRODUCT_ID,
                "license_key": license_key.strip(),
                "increment_uses_count": "false",
            },
            timeout=10,
        )
        data = response.json()
        if data.get("success"):
            return {"valid": True, "message": "License verified ✅"}
        else:
            msg = data.get("message", "Invalid license key.")
            return {"valid": False, "message": msg}

    except requests.exceptions.Timeout:
        return {"valid": False, "message": "Verification timed out. Check your internet connection."}
    except requests.exceptions.ConnectionError:
        return {"valid": False, "message": "Could not connect to Gumroad. Check your internet connection."}
    except Exception as e:
        return {"valid": False, "message": f"Verification error: {e}"}


# ---------------------------------------------------------------------------
# Machine-bound activation token
# ---------------------------------------------------------------------------

def _get_machine_id() -> str:
    """
    Returns a stable machine identifier.
    Uses uuid.getnode() (based on MAC address) — not cryptographically strong
    but sufficient to prevent trivial config-file sharing.
    """
    return str(uuid.getnode())


def make_activation_token(license_key: str) -> str:
    """
    Create a machine-bound activation token from the license key.
    Token is a SHA-256 hex digest of 'key:machine_id'.
    """
    machine_id = _get_machine_id()
    payload = f"{license_key.strip()}:{machine_id}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def verify_activation_token(license_key: str, token: str) -> bool:
    """
    Returns True if the stored token matches this machine + key combination.
    A token from a different machine or a different key will not match.
    """
    if not token or not license_key:
        return False
    return make_activation_token(license_key) == token
