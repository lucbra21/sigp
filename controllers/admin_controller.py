"""Administrative views: approval of commission payments."""
from __future__ import annotations

import datetime as _dt
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required

from sigp import db
from sigp.models import Base
from sigp.security import require_perm
from sigp.common.email_utils import send_simple_mail

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

Ledger = getattr(Base.classes, "ledger", None)
StateLedger = getattr(Base.classes, "state_ledger", None)
Prescriptor = getattr(Base.classes, "prescriptors", None)
Lead = getattr(Base.classes, "leads", None)
LeadHistory = getattr(Base.classes, "lead_history", None)

PEND_APROB_ID = 1  # PEND_APROB_ADMIN
PEND_FACT_ID = 2  # PEND_FACTURAR
ANULADO_ID = 5  # ANULADO
SUSPENDIDO_ID = 6  # SUSPENDIDO


def _notify_and_log(ledger_rows, new_state_id):
    """Send email notifications to prescriptors and log lead history."""
    if not ledger_rows:
        return
    # Group by prescriptor
    if Prescriptor is None:
        return
    presc_ids = {r.prescriptor_id for r in ledger_rows}
    prescs = db.session.query(Prescriptor).filter(Prescriptor.id.in_(presc_ids)).all()
    presc_map = {p.id: p for p in prescs}
    # email body per prescriptor
    mail_data = {}
    for r in ledger_rows:
        p = presc_map.get(r.prescriptor_id)
        if not p or not getattr(p, "email", None):
            continue
        mail_data.setdefault(p.email, []).append(r)
        # history
        if LeadHistory is not None and r.lead_id:
            hist = LeadHistory(lead_id=r.lead_id, ts=_dt.datetime.utcnow(), action="STATE_CHANGE",
                               notes=f"Pago comisión - nuevo estado {new_state_id}")
            db.session.add(hist)
    db.session.commit()
    state_name = _state_name(new_state_id)
    for email, items in mail_data.items():
        lines = [f"Lead {it.lead_id} concepto {it.concept} monto {it.amount}" for it in items]
        body = "Se actualizó el estado de los siguientes pagos a '{}':\n\n".format(state_name) + "\n".join(lines)
        send_simple_mail([email], "Actualización de pagos de comisión", body)


def _state_name(state_id: int) -> str:
    if StateLedger is None:
        return str(state_id)
    st = db.session.get(StateLedger, state_id)
    return st.name if st else str(state_id)


@admin_bp.get("/payments/approval")
@login_required
@require_perm("manage_payments")
def pay_approval():
    # Filtros de periodo
    now = _dt.datetime.utcnow()
    from_month = int(request.args.get("from_month", now.month))
    from_year = int(request.args.get("from_year", now.year))
    to_month = int(request.args.get("to_month", now.month))
    to_year = int(request.args.get("to_year", now.year))
    period_start = from_year * 100 + from_month
    period_end = to_year * 100 + to_month
    if Ledger is None:
        flash("Tabla ledger no disponible", "danger")
        return render_template("list/pay_approval.html", rows=[])

    rows = (
        db.session.query(Ledger)
        .filter(Ledger.state_id == PEND_APROB_ID)
        .filter((Ledger.approve_due_year*100 + Ledger.approve_due_month).between(period_start, period_end))
        .order_by(Ledger.approve_due_year, Ledger.approve_due_month)
        .all()
    )
    # Build maps
    pres_map = {}
    lead_map = {}
    if rows:
        if Prescriptor is not None:
            pids = {r.prescriptor_id for r in rows}
            pres_rows = db.session.query(Prescriptor).filter(Prescriptor.id.in_(pids)).all()
            pres_map = {p.id: getattr(p, "name", p.id) for p in pres_rows}
        if Lead is not None:
            lids = {r.lead_id for r in rows if r.lead_id}
            lead_rows = db.session.query(Lead).filter(Lead.id.in_(lids)).all()
            lead_map = {l.id: getattr(l, "candidate_name", l.id) for l in lead_rows}

    return render_template("list/pay_approval.html", rows=rows, pres_map=pres_map, lead_map=lead_map,
                           from_month=from_month, from_year=from_year, to_month=to_month, to_year=to_year)


@admin_bp.post("/payments/approval/bulk")
@login_required
@require_perm("manage_payments")
def bulk_approve(): # approve selected
    ids = request.form.getlist("selected_ids")
    if not ids:
        flash("No seleccionaste movimientos", "warning")
        return redirect(url_for("admin.pay_approval"))
    updated = (
        db.session.query(Ledger)
        .filter(Ledger.id.in_(ids), Ledger.state_id == PEND_APROB_ID)
        .update({Ledger.state_id: PEND_FACT_ID, Ledger.approved_at: _dt.datetime.utcnow()}, synchronize_session=False)
    )
    db.session.commit()
    # fetch affected rows for email/history
    rows = db.session.query(Ledger).filter(Ledger.id.in_(ids)).all()
    _notify_and_log(rows, PEND_FACT_ID)
    flash(f"Se aprobaron {updated} movimientos", "success")
    return redirect(url_for("admin.pay_approval"))


@admin_bp.post("/payments/approval/<ledger_id>/approve")
@login_required
@require_perm("manage_payments")

def approve_payment(ledger_id):
    if Ledger is None:
        flash("Tabla ledger no disponible", "danger")
        return redirect(url_for("admin.pay_approval"))
    row = db.session.get(Ledger, ledger_id)
    if not row:
        flash("Movimiento no encontrado", "warning")
        return redirect(url_for("admin.pay_approval"))
    row.state_id = PEND_FACT_ID
    row.approved_at = _dt.datetime.utcnow()
    db.session.commit()
    db.session.flush()
    _notify_and_log([row], PEND_FACT_ID)
    flash("Movimiento aprobado", "success")
    return redirect(url_for("admin.pay_approval"))


@admin_bp.post("/payments/approval/<ledger_id>/reject")
@login_required
@require_perm("manage_payments")

def reject_payment(ledger_id):
    if Ledger is None:
        flash("Tabla ledger no disponible", "danger")
        return redirect(url_for("admin.pay_approval"))
    row = db.session.get(Ledger, ledger_id)
    if not row:
        flash("Movimiento no encontrado", "warning")
        return redirect(url_for("admin.pay_approval"))
    row.state_id = ANULADO_ID
    row.approved_at = _dt.datetime.utcnow()
    db.session.commit()
    db.session.flush()
    _notify_and_log([row], ANULADO_ID)
    flash("Movimiento anulado", "info")
    return redirect(url_for("admin.pay_approval"))


@admin_bp.post("/payments/approval/<ledger_id>/suspend")
@login_required
@require_perm("manage_payments")
def suspend_payment(ledger_id):
    if Ledger is None:
        flash("Tabla ledger no disponible", "danger")
        return redirect(url_for("admin.pay_approval"))
    row = db.session.get(Ledger, ledger_id)
    if not row:
        flash("Movimiento no encontrado", "warning")
        return redirect(url_for("admin.pay_approval"))
    row.state_id = SUSPENDIDO_ID
    row.approved_at = _dt.datetime.utcnow()
    db.session.commit()
    db.session.flush()
    _notify_and_log([row], SUSPENDIDO_ID)
    flash("Movimiento suspendido", "warning")
    return redirect(url_for("admin.pay_approval"))

# ---- RUTAS EN LOTE ----
@admin_bp.post("/payments/approval/bulk_cancel")
@login_required
@require_perm("manage_payments")
def bulk_cancel():
    ids = request.form.getlist("selected_ids")
    if not ids:
        flash("No seleccionaste movimientos", "warning")
        return redirect(url_for("admin.pay_approval"))
    upd = (
        db.session.query(Ledger)
        .filter(Ledger.id.in_(ids), Ledger.state_id == PEND_APROB_ID)
        .update({Ledger.state_id: ANULADO_ID, Ledger.approved_at: _dt.datetime.utcnow()}, synchronize_session=False)
    )
    db.session.commit()
    rows = db.session.query(Ledger).filter(Ledger.id.in_(ids)).all()
    _notify_and_log(rows, ANULADO_ID)
    flash(f"Se anularon {upd} movimientos", "info")
    return redirect(url_for("admin.pay_approval"))


@admin_bp.post("/payments/approval/bulk_suspend")
@login_required
@require_perm("manage_payments")
def bulk_suspend():
    ids = request.form.getlist("selected_ids")
    if not ids:
        flash("No seleccionaste movimientos", "warning")
        return redirect(url_for("admin.pay_approval"))
    upd = (
        db.session.query(Ledger)
        .filter(Ledger.id.in_(ids), Ledger.state_id == PEND_APROB_ID)
        .update({Ledger.state_id: SUSPENDIDO_ID, Ledger.approved_at: _dt.datetime.utcnow()}, synchronize_session=False)
    )
    db.session.commit()
    rows = db.session.query(Ledger).filter(Ledger.id.in_(ids)).all()
    _notify_and_log(rows, SUSPENDIDO_ID)
    flash(f"Se suspendieron {upd} movimientos", "warning")
    return redirect(url_for("admin.pay_approval"))
