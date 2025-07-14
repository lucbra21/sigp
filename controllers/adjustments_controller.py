from datetime import date
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required

from sigp.common.security import require_perm
from sigp import db
from sigp.services.adjustment_service import (
    create_credit_note,
    create_debit_note,
    AdjustmentError,
    balance_for_prescriptor,
)

adjustments_bp = Blueprint("adjustments", __name__, url_prefix="/adjustments")

# prescriptor model
from sigp.models import Base
Prescriptor = getattr(Base.classes, "prescriptor", None) or getattr(Base.classes, "prescriptors", None)
CreditNote = getattr(Base.classes, "credit_notes", None)
DebitNote = getattr(Base.classes, "debit_notes", None)


@adjustments_bp.get("/")
@login_required
@require_perm("manage_payments")
def adjustments_page():
    prescriptors = []
    notes = []
    if Prescriptor is not None:
        prescriptors = (
            db.session.query(Prescriptor.id, Prescriptor.squeeze_page_name.label("name"))
            .order_by(Prescriptor.squeeze_page_name)
            .all()
        )
    # fetch notes
    if CreditNote is not None and DebitNote is not None:
        cq = (
            db.session.query(
                CreditNote.id,
                CreditNote.amount.label("amount"),
                CreditNote.note_date.label("note_date"),
                CreditNote.concept.label("concept"),
                Prescriptor.squeeze_page_name.label("prescriptor"),
                db.literal("Crédito").label("type"),
                CreditNote.created_at.label("created_at"),
            )
            .join(Prescriptor, Prescriptor.id == CreditNote.prescriptor_id)
        )
        dq = (
            db.session.query(
                DebitNote.id,
                DebitNote.amount.label("amount"),
                DebitNote.note_date.label("note_date"),
                DebitNote.concept.label("concept"),
                Prescriptor.squeeze_page_name.label("prescriptor"),
                db.literal("Débito").label("type"),
                DebitNote.created_at.label("created_at"),
            )
            .join(Prescriptor, Prescriptor.id == DebitNote.prescriptor_id)
        )
        union_q = cq.union_all(dq).subquery()
        notes = db.session.query(*union_q.c).order_by(union_q.c.created_at.desc()).all()
    from datetime import date as _dt
    return render_template("list/adjustments_list.html", prescriptors=prescriptors, notes=notes, today=_dt.today().isoformat())


@adjustments_bp.post("/")
@login_required
@require_perm("manage_payments")
def add_note():
    data = request.get_json(force=True)
    prescriptor_id = data.get("prescriptor_id")
    amount = float(data.get("amount", 0))
    note_type = data.get("type", "C").upper()  # C o D
    concept = data.get("concept")
    note_date = date.fromisoformat(data.get("date")) if data.get("date") else date.today()

    try:
        if note_type == "C":
            note = create_credit_note(prescriptor_id, amount, note_date, concept)
        else:
            note = create_debit_note(prescriptor_id, amount, note_date, concept)
        return jsonify({"status": "ok", "id": note.id}), 201
    except AdjustmentError as e:
        return jsonify({"status": "error", "msg": str(e)}), 400


@adjustments_bp.get("/<prescriptor_id>/balance")
@login_required
@require_perm("manage_payments")
def get_balance(prescriptor_id):
    credit, debit, net = balance_for_prescriptor(prescriptor_id)
    return jsonify({"credit": credit, "debit": debit, "net": net})


# ---- UI routes for creating notes ----

from flask import redirect, url_for, flash

@adjustments_bp.get("/new/<note_type>")
@login_required
@require_perm("manage_payments")
def new_note_page(note_type):
    if note_type not in ("C", "D"):
        return redirect(url_for("adjustments.adjustments_page"))
    prescriptors = db.session.query(Prescriptor.id, Prescriptor.squeeze_page_name.label("name")).order_by(Prescriptor.squeeze_page_name).all() if Prescriptor else []
    from datetime import date as _dt
    return render_template("records/adjustment_note_form.html", note_type=note_type, prescriptors=prescriptors, today=_dt.today().isoformat())


@adjustments_bp.post("/new/<note_type>")
@login_required
@require_perm("manage_payments")
def create_note_form(note_type):
    if note_type not in ("C", "D"):
        return redirect(url_for("adjustments.adjustments_page"))
    prescriptor_id = request.form.get("prescriptor_id")
    amount = float(request.form.get("amount", 0))
    concept = request.form.get("concept")
    note_date = date.fromisoformat(request.form.get("date")) if request.form.get("date") else date.today()
    try:
        if note_type == "C":
            create_credit_note(prescriptor_id, amount, note_date, concept)
            flash("Nota de crédito creada", "success")
        else:
            create_debit_note(prescriptor_id, amount, note_date, concept)
            flash("Nota de débito creada", "success")
    except AdjustmentError as e:
        flash(str(e), "danger")
    return redirect(url_for("adjustments.adjustments_page"))
