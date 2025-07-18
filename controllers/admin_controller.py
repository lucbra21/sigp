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
Invoice = getattr(Base.classes, "invoice", None)

PEND_APROB_ID = 1  # PEND_APROB_ADMIN
PEND_FACT_ID = 2  # PEND_FACTURAR
ANULADO_ID = 5  # ANULADO
SUSPENDIDO_ID = 6  # SUSPENDIDO
DEFAULT_RENDIDO_ID = 4  # RENDIDO


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

def _state_id(code: str) -> int | None:
    """Devuelve el id de state_ledger dado su código."""
    if StateLedger is None:
        return None
    col = None
    if hasattr(StateLedger, "code"):
        col = StateLedger.code
    elif hasattr(StateLedger, "name"):
        col = StateLedger.name
    if col is None:
        return None
    row = db.session.query(StateLedger).filter(col == code).first()
    return row.id if row else None


@admin_bp.get("/payments/approval")
@login_required
@require_perm("manage_payments")
def pay_approval():
    # Filtros de periodo
    now = _dt.datetime.utcnow()
    def _opt_int(name):
        try:
            val = request.args.get(name)
            return int(val) if val else None
        except (TypeError, ValueError):
            return None
    def _int_param(name, default):
        v = _opt_int(name)
        return v if v is not None else default
    from_month = _int_param("from_month", now.month)
    from_year  = _int_param("from_year",  now.year)
    to_month   = _int_param("to_month",   now.month)
    to_year    = _int_param("to_year",    now.year)
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
            pres_map = {p.id: (getattr(p, 'squeeze_page_name', None) or getattr(p, 'name', p.id)) for p in pres_rows}
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

@admin_bp.post("/payments/canceled/<ledger_id>/invoice")
@login_required
@require_perm("manage_payments")
def invoice_payment(ledger_id):
    if Ledger is None:
        flash("Tabla ledger no disponible", "danger")
        return redirect(url_for("admin.list_canceled"))
    row = db.session.get(Ledger, ledger_id)
    if not row:
        flash("Movimiento no encontrado", "warning")
        return redirect(url_for("admin.list_canceled"))
    row.state_id = PEND_FACT_ID
    row.approved_at = _dt.datetime.utcnow()
    db.session.commit()
    db.session.flush()
    _notify_and_log([row], PEND_FACT_ID)
    flash("Movimiento enviado a facturar", "success")
    return redirect(url_for("admin.list_canceled"))

# ---------------------------------------------------------------------------
# Rendición de facturas (pago a prescriptores)
# ---------------------------------------------------------------------------

@admin_bp.get("/payments/settlements")
@login_required
@require_perm("manage_payments")
def settlements_form():
    Prescriptor = getattr(Base.classes, "prescriptors", None)
    if Invoice is None or Prescriptor is None:
        flash("Modelos no disponibles", "danger")
        return redirect(url_for("admin.pay_approval"))

    presc_id = request.args.get("prescriptor", "")
    query = db.session.query(Invoice).filter(Invoice.paid_at == None)  # noqa: E711
    if presc_id:
        query = query.filter(Invoice.prescriptor_id == presc_id)
    invoices = query.order_by(Invoice.created_at).all()

    # build map prescriptor
    presc_objs = db.session.query(Prescriptor).all()
    presc_rows = [
        (p.id,
         getattr(p, 'squeeze_page_name', None)
         or getattr(p, 'nombre', None)
         or getattr(p, 'name', str(p.id)))
        for p in presc_objs
    ]
    presc_map = {pid: pname for pid, pname in presc_rows}

    return render_template("list/settlements.html", invoices=invoices, prescriptors=presc_rows, presc_sel=presc_id, presc_map=presc_map)


@admin_bp.post("/payments/settlements")
@login_required
@require_perm("manage_payments")
def settlements_save():
    ids = request.form.getlist("selected_ids")
    if not ids:
        flash("No seleccionaste facturas", "warning")
        return redirect(url_for("admin.settlements_form"))

    files = request.files
    _today = _dt.datetime.utcnow()

    pend_ids = ids.copy()
    # get invoices records
    inv_rows = db.session.query(Invoice).filter(Invoice.id.in_(pend_ids), Invoice.paid_at == None).all()  # noqa: E711
    if not inv_rows:
        flash("Facturas seleccionadas no válidas", "warning")
        return redirect(url_for("admin.settlements_form"))

    # prepare state id
    rend_id = _state_id("RENDIDO") or DEFAULT_RENDIDO_ID

    for inv in inv_rows:
        # handle file
        file_field = f"file_{inv.id}"
        f = files.get(file_field)
        receipt_path = None
        if f and f.filename:
            ext = f.filename.rsplit(".",1)[-1].lower()
            from sigp.config import Config
            save_dir = os.path.join(os.getcwd(), Config.RECEIPT_UPLOAD_FOLDER)
            os.makedirs(save_dir, exist_ok=True)
            fname = f"{inv.id}.{ext}"
            full = os.path.join(save_dir, fname)
            f.save(full)
            receipt_path = os.path.join(Config.RECEIPT_UPLOAD_FOLDER, fname)
            setattr(inv, "receipt_path", receipt_path)
        # monto rendido
        amt_str = request.form.get(f"amount_{inv.id}")
        try:
            amt_val = float(amt_str) if amt_str else None
        except ValueError:
            amt_val = None
        if amt_val is not None:
            setattr(inv, "paid_amount", amt_val)
        setattr(inv, "paid_at", _today)

    # update ledgers linked
    if inv_rows:
        inv_ids = [inv.id for inv in inv_rows]
        updated = (
            db.session.query(Ledger)
            .filter(Ledger.invoice_id.in_(inv_ids))
            .update({Ledger.state_id: rend_id}, synchronize_session=False)
        )
        if hasattr(Ledger, "paid_at"):
            db.session.query(Ledger).filter(Ledger.invoice_id.in_(inv_ids)).update({Ledger.paid_at: _today}, synchronize_session=False)
        app.logger.info("Rendidas %s comisiones", updated)

    db.session.commit()

    # notificaciones, emails, historial
    notify_settlement(inv_rows)

    flash(f"Se rindieron {len(inv_rows)} facturas", "success")
    return redirect(url_for("admin.settlements_form"))


def notify_settlement(inv_rows):
    """Crear notificaciones, emails y log de leads."""
    if not inv_rows:
        return
    Notification = getattr(Base.classes, "notifications", None)
    Prescriptor = getattr(Base.classes, "prescriptors", None)
    User = getattr(Base.classes, "users", None)
    if Notification is None or Prescriptor is None or User is None:
        return
    from sigp.common.email_utils import send_simple_mail
    for inv in inv_rows:
        presc = db.session.get(Prescriptor, inv.prescriptor_id)
        if not presc:
            continue
        # user email
        user = db.session.get(User, getattr(presc, "user_id", None)) if User else None
        email_to = getattr(user, "email", None)
        # Notificación
        notif = Notification(
            user_id=getattr(user, "id", None),
            title="Pago de comisión rendido",
            message=f"Tu factura {inv.number} (total {inv.total} €) ha sido rendida.",
            created_at=_dt.datetime.utcnow(),
        )
        db.session.add(notif)
        # Email
        if email_to:
            try:
                send_simple_mail([email_to], "Pago de comisión rendido", notif.message)
            except Exception as exc:  # pylint: disable=broad-except
                app.logger.error("Mail rendición: %s", exc)
        # Historico lead
        rows = db.session.query(Ledger).filter(Ledger.invoice_id == inv.id).all()
        for r in rows:
            if r.lead_id:
                from sigp.common.lead_utils import log_lead_change
                log_lead_change(r.lead_id, _state_id("RENDIDO") or DEFAULT_RENDIDO_ID, "Comisión rendida")

# ---- LISTADOS POR ESTADO ----
@admin_bp.get("/payments/suspended")
@login_required
@require_perm("manage_payments")
def list_suspended():
    now = _dt.datetime.utcnow()
    def _opt_int(name):
        try:
            val = request.args.get(name)
            return int(val) if val else None
        except (TypeError, ValueError):
            return None
    def _int_param(name, default):
        v = _opt_int(name)
        return v if v is not None else default
    from_month = _int_param("from_month", now.month)
    from_year  = _int_param("from_year",  now.year)
    to_month   = _int_param("to_month",   now.month)
    to_year    = _int_param("to_year",    now.year)
    query = db.session.query(Ledger).filter(Ledger.state_id == SUSPENDIDO_ID)
    period_start = from_year * 100 + from_month
    query = query.filter((Ledger.approve_due_year*100 + Ledger.approve_due_month) >= period_start)
    if request.args.get("to_year") or request.args.get("to_month"):
        period_end = to_year * 100 + to_month
        query = query.filter((Ledger.approve_due_year*100 + Ledger.approve_due_month) <= period_end)
    rows = query.order_by(Ledger.approve_due_year, Ledger.approve_due_month).all()
    pres_map, lead_map = {}, {}
    if rows:
        if Prescriptor is not None:
            pids = {r.prescriptor_id for r in rows}
            pres_rows = db.session.query(Prescriptor).filter(Prescriptor.id.in_(pids)).all()
            pres_map = {p.id: (getattr(p, 'squeeze_page_name', None) or getattr(p, 'name', p.id)) for p in pres_rows}
        if Lead is not None:
            lids = {r.lead_id for r in rows if r.lead_id}
            lead_rows = db.session.query(Lead).filter(Lead.id.in_(lids)).all()
            lead_map = {l.id: getattr(l, "candidate_name", l.id) for l in lead_rows}
    return render_template("list/pay_status.html", rows=rows, pres_map=pres_map, lead_map=lead_map,
                           page_title="Pagos suspendidos", state_id=SUSPENDIDO_ID, SUSPENDIDO_ID=SUSPENDIDO_ID, ANULADO_ID=ANULADO_ID)


@admin_bp.get("/payments/canceled")
@login_required
@require_perm("manage_payments")
def list_canceled():
    now = _dt.datetime.utcnow()
    def _opt_int(name):
        try:
            val = request.args.get(name)
            return int(val) if val else None
        except (TypeError, ValueError):
            return None
    def _int_param(name, default):
        v = _opt_int(name)
        return v if v is not None else default
    from_month = _int_param("from_month", now.month)
    from_year  = _int_param("from_year",  now.year)
    to_month   = _int_param("to_month",   now.month)
    to_year    = _int_param("to_year",    now.year)
    query = db.session.query(Ledger).filter(Ledger.state_id == ANULADO_ID)
    period_start = from_year * 100 + from_month
    query = query.filter((Ledger.approve_due_year*100 + Ledger.approve_due_month) >= period_start)
    if request.args.get("to_year") or request.args.get("to_month"):
        period_end = to_year * 100 + to_month
        query = query.filter((Ledger.approve_due_year*100 + Ledger.approve_due_month) <= period_end)
    rows = query.order_by(Ledger.approve_due_year, Ledger.approve_due_month).all()
    pres_map, lead_map = {}, {}
    if rows:
        if Prescriptor is not None:
            pids = {r.prescriptor_id for r in rows}
            pres_rows = db.session.query(Prescriptor).filter(Prescriptor.id.in_(pids)).all()
            pres_map = {p.id: (getattr(p, 'squeeze_page_name', None) or getattr(p, 'name', p.id)) for p in pres_rows}
        if Lead is not None:
            lids = {r.lead_id for r in rows if r.lead_id}
            lead_rows = db.session.query(Lead).filter(Lead.id.in_(lids)).all()
            lead_map = {l.id: getattr(l, "candidate_name", l.id) for l in lead_rows}
    return render_template("list/pay_status.html", rows=rows, pres_map=pres_map, lead_map=lead_map,
                           page_title="Pagos anulados", state_id=ANULADO_ID, SUSPENDIDO_ID=SUSPENDIDO_ID, ANULADO_ID=ANULADO_ID)

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
