import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any, List, Tuple

from sigp import db
from flask import current_app
from sigp.models import Base
from sqlalchemy.exc import SQLAlchemyError

CreditNote = getattr(Base.classes, "credit_notes", None)
DebitNote = getattr(Base.classes, "debit_notes", None)
Prescriptor = getattr(Base.classes, "prescriptor", None) or getattr(Base.classes, "prescriptors", None)

class AdjustmentError(RuntimeError):
    pass

def _insert_note(table_cls, prescriptor_id: str, amount: float, note_date: date, concept: str | None):
    if table_cls is None:
        raise AdjustmentError("Tabla no disponible")
    note = table_cls(
        id=str(uuid.uuid4()),
        prescriptor_id=prescriptor_id,
        amount=amount,
        note_date=note_date,
        concept=concept,
        created_at=datetime.utcnow(),
    )
    try:
        db.session.add(note)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.exception("Error guardando nota")
        raise AdjustmentError("No se pudo guardar la nota") from e
    return note

def create_credit_note(prescriptor_id: str, amount: float, note_date: date, concept: str | None = None):
    return _insert_note(CreditNote, prescriptor_id, amount, note_date, concept)

def create_debit_note(prescriptor_id: str, amount: float, note_date: date, concept: str | None = None):
    return _insert_note(DebitNote, prescriptor_id, amount, note_date, concept)

def balance_for_prescriptor(prescriptor_id: str) -> Tuple[float, float, float]:
    """Devuelve (total_credit, total_debit, neto)."""
    credit_total = 0.0
    debit_total = 0.0
    if CreditNote is not None:
        credit_total = (
            db.session.query(db.func.coalesce(db.func.sum(CreditNote.amount), 0))
            .filter(CreditNote.prescriptor_id == prescriptor_id)
            .scalar()
            or 0.0
        )
    if DebitNote is not None:
        debit_total = (
            db.session.query(db.func.coalesce(db.func.sum(DebitNote.amount), 0))
            .filter(DebitNote.prescriptor_id == prescriptor_id)
            .scalar()
            or 0.0
        )
    return credit_total, debit_total, credit_total - debit_total
