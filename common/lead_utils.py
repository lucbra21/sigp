"""Utilities for lead operations such as history logging."""
from __future__ import annotations

import datetime
import uuid
from flask_login import current_user
from typing import Optional
from sigp import db
from sigp.models import Base

def _model():
    """Return the lead_history model (cached per request)."""
    return getattr(Base.classes, "lead_history", None)


def log_lead_change(lead_id: str, state_id: int, observations: Optional[str] = None):
    """Insert a row into lead_history and commit immediately.

    Does nothing if model not available or user anonymous.
    """
    LeadHistory = _model()
    if LeadHistory is None:
        return
    user_id = getattr(current_user, "id", None)
    if not user_id:
        return

    lh = LeadHistory(
        lead_id=lead_id,
        state_id=state_id,
        changed_by=user_id,
        observations=observations or None,
        changed_at=datetime.datetime.utcnow(),
    )
    db.session.add(lh)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
