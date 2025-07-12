"""Helpers relacionados con prescriptores."""
from sigp import db
from sigp.models import Base
import uuid

Prescriptor = getattr(Base.classes, "prescriptors", None)
Program = getattr(Base.classes, "programs", None)
PrescComm = getattr(Base.classes, "prescriptor_commission", None)

def _ensure_models():
    if not (Prescriptor and Program and PrescComm):
        raise RuntimeError("Tablas necesarias no reflejadas")

def sync_commissions_for_prescriptor(presc_id: str):
    """Crea filas de comisión faltantes para un prescriptor."""
    _ensure_models()
    existing_prog_ids = {
        row.program_id for row in db.session.query(PrescComm.program_id).filter_by(prescriptor_id=presc_id)
    }
    prog_rows = db.session.query(Program).all()
    new_objs = []
    for prog in prog_rows:
        if prog.id in existing_prog_ids:
            continue
        new_objs.append(
            PrescComm(
                id=str(uuid.uuid4()),
                prescriptor_id=presc_id,
                program_id=prog.id,
                commission_value=getattr(prog, "commission_value", 0) or 0,
                first_installment_pct=getattr(prog, "first_installment_pct", 0) or 0,
                registration_value=0,
                value_quotas=0,
            )
        )
    if new_objs:
        db.session.bulk_save_objects(new_objs)
        db.session.commit()


def sync_commissions_for_program(program_id: str):
    """Crea filas para un programa nuevo en todos los prescriptores."""
    _ensure_models()
    existing_pairs = {
        (row.prescriptor_id, row.program_id)
        for row in db.session.query(PrescComm.prescriptor_id, PrescComm.program_id)
        .filter_by(program_id=program_id)
    }
    presc_rows = db.session.query(Prescriptor.id).all()
    prog = db.session.get(Program, program_id)
    if not prog:
        return
    new_objs = []
    for (presc_id,) in presc_rows:
        if (presc_id, program_id) in existing_pairs:
            continue
        new_objs.append(
            PrescComm(
                id=str(uuid.uuid4()),
                prescriptor_id=presc_id,
                program_id=program_id,
                commission_value=getattr(prog, "commission_value", 0) or 0,
                first_installment_pct=getattr(prog, "first_installment_pct", 0) or 0,
                registration_value=0,
                value_quotas=0,
            )
        )
    if new_objs:
        db.session.bulk_save_objects(new_objs)
        db.session.commit()
