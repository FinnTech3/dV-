"""Optional Companies House integration.

The Companies House REST API needs an API key issued to a user-created account,
so it is an OPTIONAL enhancement and is disabled unless an authorised key is
already present in the environment (COMPANIES_HOUSE_API_KEY). The pipeline never
creates an account or asks for a key as a prerequisite.

Even when enabled, an officer record supports previous UK EMPLOYMENT/appointment
only. A service or correspondence address is never evidence of residence.
"""
from __future__ import annotations

import os


def available() -> bool:
    return bool(os.environ.get("COMPANIES_HOUSE_API_KEY"))


def status() -> dict:
    return {"available": available(),
            "note": "enabled" if available() else "no authorised credential configured; optional enhancement, not used"}
