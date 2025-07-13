"""Utility functions for creating ledger movements related to prescriptor commissions."""
from __future__ import annotations

import uuid
import datetime as _dt
from typing import Optional

from sigp import db
from sigp.models import Base

Ledger = getattr(Base.classes, "ledger", None)
PrescComm = getattr(Base.classes, "prescriptor_commission", None)
StateLedger = getattr(Base.classes, "state_ledger", None)

# Default state ids
PENDING_ID = 1  # ensure DB has an entry id=1 named PENDIENTE


def _first_quota_date(start_month: str, start_year: int) -> _dt.date:
    """Return first quota due date based on edition start month/year."""
    if start_month == "03":
        return _dt.date(start_year, 5, 1)  # May
    # start_month == '10'
    return _dt.date(start_year, 12, 1)  # December


def create_commission_ledger(lead) -> None:  # noqa: C901
    """Generate ledger movements for a newly matriculated lead.

    Assumes the lead row is already committed with program_id, payment_fees,
    start_month, start_year and prescriptor_id.
    """

    if Ledger is None or PrescComm is None:
        return

    # skip test leads
    if getattr(lead, "is_test", False):
        return

    # avoid duplicates
    exists = db.session.query(Ledger).filter(Ledger.lead_id == lead.id).first()
    if exists:
        return

    # fetch commission row
    comm_row = (
        db.session.query(PrescComm)
        .filter(
            PrescComm.prescriptor_id == lead.prescriptor_id,
            PrescComm.program_id == lead.program_id,
        )
        .first()
    )
    if not comm_row:
        return

    # derive numbers
    total_comm = float(comm_row.commission_value)
    first_pct = float(comm_row.first_installment_pct)
    first_amount = round(total_comm * first_pct / 100, 2)

    import re
    num_quotas = 0
    if lead.payment_fees:
        m = re.search(r"\d+", str(lead.payment_fees))
        if m:
            num_quotas = int(m.group())

    remaining_amount = round(total_comm - first_amount, 2)

    # número y monto por cuota
    quota_amount = 0.0
    if num_quotas:
        quota_amount = round(remaining_amount / num_quotas, 2)

    # state pending id
    state_id = PENDING_ID
    if StateLedger is not None:
        st = db.session.query(StateLedger).get(PENDING_ID)
        if not st:
            # fallback to first state
            first = db.session.query(StateLedger).first()
            state_id = first.id if first else PENDING_ID

    movements = []

    def new_row(amount: float, concept: str, approve_month: str, approve_year: int):
        movements.append(
            Ledger(
                id=str(uuid.uuid4()),
                prescriptor_id=lead.prescriptor_id,
                lead_id=lead.id,
                doc_type="COMISION",
                concept=concept,
                amount=amount,
                sign=1,
                state_id=state_id,
                approve_due_month=approve_month,
                approve_due_year=approve_year,
                created_at=_dt.datetime.utcnow(),
            )
        )

    # comisión matrícula (anticipo) → aprobación mes siguiente al cambio de estado
    today = _dt.date.today()
    next_year = today.year + (1 if today.month == 12 else 0)
    next_month = 1 if today.month == 12 else today.month + 1
    new_row(first_amount, "Comisión matrícula", f"{next_month:02}", next_year)

    # remaining quotas
    if num_quotas and quota_amount:
        first_due = _first_quota_date(lead.start_month, int(lead.start_year))
        curr_due = first_due
        for n in range(1, num_quotas + 1):
            concept = f"Comisión cuota {n}/{num_quotas}"
            approve_month = f"{curr_due.month:02}"
            approve_year = curr_due.year
            new_row(quota_amount, concept, approve_month, approve_year)
            # advance one month
            year = curr_due.year + (1 if curr_due.month == 12 else 0)
            month = 1 if curr_due.month == 12 else curr_due.month + 1
            curr_due = _dt.date(year, month, 1)

    if movements:
        db.session.bulk_save_objects(movements)
        db.session.commit()
