import uuid
import unicodedata
from datetime import datetime, timedelta

from sigp import db
from sigp.models import Base

"""Helpers relacionados con prescriptores."""

Prescriptor = getattr(Base.classes, "prescriptors", None)
Program = getattr(Base.classes, "programs", None)
PrescComm = getattr(Base.classes, "prescriptor_commission", None)


def _normalize(value) -> str:
    text = str(value or "").strip().lower()
    return "".join(
        c for c in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(c)
    )


def is_active_program(program) -> bool:
    return _normalize(getattr(program, "state", "Activo")) != "desactivado"


def default_commission_value_for_program(program) -> float:
    """Regla comercial vigente para comisión total por programa."""
    haystack = " ".join(
        _normalize(getattr(program, attr, ""))
        for attr in ("level", "name", "abbreviation")
    )
    if "diplomatura" in haystack or "diplomado" in haystack:
        return 80.0

    language = _normalize(getattr(program, "language", ""))
    if language in {"ingles", "english"}:
        return 250.0

    return 150.0


def apply_program_commission_policy(program) -> float:
    commission = default_commission_value_for_program(program)
    if hasattr(program, "commission_value"):
        program.commission_value = commission
    return commission


def commission_values_from_program(program) -> dict:
    return {
        "commission_value": default_commission_value_for_program(program),
        "first_installment_pct": getattr(program, "first_installment_pct", 0) or 0,
        "registration_value": getattr(program, "registration_value", 0) or 0,
        "value_quotas": getattr(program, "value_quotas", 0) or 0,
    }


def _ensure_models():
    if not (Prescriptor and Program and PrescComm):
        raise RuntimeError("Tablas necesarias no reflejadas")


def _assign_values(row, values: dict) -> bool:
    changed = False
    for attr, value in values.items():
        current = getattr(row, attr, None)
        if current != value:
            setattr(row, attr, value)
            changed = True
    return changed


def sync_commissions_for_prescriptor(presc_id: str, *, active_only: bool = True, update_existing: bool = False) -> dict:
    """Crea filas de comisión faltantes para un prescriptor."""
    _ensure_models()
    existing_rows = {
        row.program_id: row
        for row in db.session.query(PrescComm).filter_by(prescriptor_id=presc_id)
    }
    prog_rows = db.session.query(Program).all()
    new_objs = []
    updated = 0
    for prog in prog_rows:
        if active_only and not is_active_program(prog):
            continue
        values = commission_values_from_program(prog)
        existing = existing_rows.get(prog.id)
        if existing:
            if update_existing and _assign_values(existing, values):
                updated += 1
            continue
        new_objs.append(
            PrescComm(
                id=str(uuid.uuid4()),
                prescriptor_id=presc_id,
                program_id=prog.id,
                **values,
            )
        )
    if new_objs:
        db.session.add_all(new_objs)
    if new_objs or updated:
        db.session.commit()
    return {"created": len(new_objs), "updated": updated}


def sync_commissions_for_program(program_id: str, *, update_existing: bool = False) -> dict:
    """Crea filas para un programa nuevo en todos los prescriptores."""
    _ensure_models()
    prog = db.session.get(Program, program_id)
    if not prog or not is_active_program(prog):
        return {"created": 0, "updated": 0}

    existing_rows = {
        row.prescriptor_id: row
        for row in db.session.query(PrescComm).filter_by(program_id=program_id)
    }
    presc_rows = db.session.query(Prescriptor.id).all()
    values = commission_values_from_program(prog)
    new_objs = []
    updated = 0
    for (presc_id,) in presc_rows:
        existing = existing_rows.get(presc_id)
        if existing:
            if update_existing and _assign_values(existing, values):
                updated += 1
            continue
        new_objs.append(
            PrescComm(
                id=str(uuid.uuid4()),
                prescriptor_id=presc_id,
                program_id=program_id,
                **values,
            )
        )
    if new_objs:
        db.session.add_all(new_objs)
    if new_objs or updated:
        db.session.commit()
    return {"created": len(new_objs), "updated": updated}


def sync_recent_prescriptor_commissions(*, days: int = 5, apply: bool = False) -> dict:
    """Sincroniza programas activos para prescriptores recientes sin tocar históricos."""
    _ensure_models()
    cutoff = datetime.utcnow() - timedelta(days=days)
    recent_prescriptors = (
        db.session.query(Prescriptor)
        .filter(Prescriptor.created_at >= cutoff)
        .all()
    )
    active_programs = [p for p in db.session.query(Program).all() if is_active_program(p)]
    totals = {
        "cutoff": cutoff,
        "prescriptors": len(recent_prescriptors),
        "programs": len(active_programs),
        "created": 0,
        "updated": 0,
    }
    for presc in recent_prescriptors:
        existing_rows = {
            row.program_id: row
            for row in db.session.query(PrescComm).filter_by(prescriptor_id=presc.id)
        }
        for program in active_programs:
            values = commission_values_from_program(program)
            existing = existing_rows.get(program.id)
            if existing:
                changed = any(getattr(existing, attr, None) != value for attr, value in values.items())
                if changed:
                    totals["updated"] += 1
                    if apply:
                        _assign_values(existing, values)
                continue
            totals["created"] += 1
            if apply:
                db.session.add(
                    PrescComm(
                        id=str(uuid.uuid4()),
                        prescriptor_id=presc.id,
                        program_id=program.id,
                        **values,
                    )
                )
    if apply:
        db.session.commit()
    return totals
