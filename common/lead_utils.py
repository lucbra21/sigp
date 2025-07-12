"""Utilities for lead operations such as history logging."""
from __future__ import annotations

import datetime
import uuid
from flask_login import current_user
from sigp import db
from sigp.models import Base

LeadHistory = getattr(Base.classes, "lead_history", None)


def log_lead_change(lead_id: str, state_id: int, observations: str | None = None):
    """Insert a row into lead_history.

    If the table is not present or the user is anonymous, do nothing.
    """
    if LeadHistory is None:
        return
    user_id = getattr(current_user, "id", None)
    if not user_id:
        return

    lh = LeadHistory(
        # id is AUTO_INCREMENT -> omit if so; if uuid char, provide id
        lead_id=lead_id,
        state_id=state_id,
        changed_by=user_id,
        observations=observations or None,
        changed_at=datetime.datetime.utcnow(),
    )
    db.session.add(lh)
    # Note: caller should commit to persist
