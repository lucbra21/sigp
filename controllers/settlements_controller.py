from __future__ import annotations

"""Blueprint de Finanzas para rendición de facturas de prescriptores."""

from pathlib import Path
from typing import List

from flask import (
    Blueprint,
    current_app as app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import login_required
from werkzeug.utils import secure_filename

from sigp import db
from sigp.models import Base
from sigp.security import require_perm  # reutilizar sistema actual
from sigp.services.settlement_service import settle_invoices, SettlementError
from datetime import date

settlements_bp = Blueprint("settlements", __name__, url_prefix="/settlements")

# tablas reflejadas
Invoice = getattr(Base.classes, "invoice", None)
Prescriptor = getattr(Base.classes, "prescriptor", None) or getattr(Base.classes, "prescriptors", None)
Ledger = getattr(Base.classes, "ledger", None)


def _allowed_file(filename: str) -> bool:
    """Comprueba extensión permitida."""
    allowed = {ext.lower() for ext in app.config.get("INVOICE_ALLOWED_EXT", {"pdf", "jpg", "jpeg", "png"})}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


@settlements_bp.get("/")
@login_required
@require_perm("manage_payments")
def pending_all():
    """Pantalla inicial: lista de TODAS las facturas pendientes con filtros opcionales."""
    if Invoice is None or Ledger is None:
        flash("Tablas necesarias no disponibles", "danger")
        return redirect(url_for("dashboard.dashboard_home"))

    prescriptor_id = request.args.get("prescriptor_id")
    date_from = request.args.get("date_from", type=date.fromisoformat if request.args.get("date_from") else lambda x: None)
    date_to = request.args.get("date_to", type=date.fromisoformat if request.args.get("date_to") else lambda x: None)

    q = (
        db.session.query(Invoice)
        .join(Ledger, Ledger.invoice_id == Invoice.id)
        .filter(Ledger.state_id != 4)
    )
    if prescriptor_id:
        q = q.filter(Invoice.prescriptor_id == prescriptor_id)
    if date_from:
        q = q.filter(Invoice.invoice_date >= date_from)
    if date_to:
        q = q.filter(Invoice.invoice_date <= date_to)

    invoices = q.order_by(Invoice.invoice_date.desc()).limit(500).all()

    # prescriptores para filtro
    label_col = None
    if Prescriptor:
        for attr in ("squeeze_page_name", "name", "email"):
            if hasattr(Prescriptor, attr):
                label_col = getattr(Prescriptor, attr)
                break
        order_col = label_col or Prescriptor.id
        prescriptors = db.session.query(Prescriptor).order_by(order_col).all()
    else:
        prescriptors = []
    presc_map = {p.id: (getattr(p, label_col.key) if label_col else str(p.id)) for p in prescriptors}

    return render_template(
        "list/settlements_pending_all.html",
        invoices=invoices,
        prescriptors=prescriptors,
        presc_sel=prescriptor_id or "",
        date_from=request.args.get("date_from", ""),
        date_to=request.args.get("date_to", ""),
        presc_map=presc_map,
        label_attr=label_col.key if label_col else None,
    )


@settlements_bp.get("/select")
@login_required
@require_perm("manage_payments")
def select_prescriptor():
    """Pantalla 1: selección de prescriptor."""
    if Prescriptor is None:
        flash("Tabla prescriptor no disponible", "danger")
        return redirect(url_for("dashboard.dashboard_home"))

    q = request.args.get("q", "").strip()
    prescriptors_q = db.session.query(Prescriptor)
    # determinar columna 'label' disponible
    label_col = None
    for attr in ("squeeze_page_name", "name", "email"):
        if hasattr(Prescriptor, attr):
            label_col = getattr(Prescriptor, attr)
            break
    if q and label_col is not None:
        prescriptors_q = prescriptors_q.filter(label_col.ilike(f"%{q}%"))
    order_col = label_col or Prescriptor.id
    prescriptors = prescriptors_q.order_by(order_col).limit(50).all()
    return render_template("list/settlements_select.html", prescriptors=prescriptors, q=q, label_attr=label_col.key if label_col is not None else None)


@settlements_bp.get("/pending/<prescriptor_id>")
@login_required
@require_perm("manage_payments")
def pending_invoices(prescriptor_id):
    if Invoice is None or Ledger is None:
        flash("Tablas necesarias no disponibles", "danger")
        return redirect(url_for("settlements.pending_all"))

    invoices = (
        db.session.query(Invoice)
        .join(Ledger, Ledger.invoice_id == Invoice.id)
        .filter(Invoice.prescriptor_id == prescriptor_id, Ledger.state_id != 4)
        .order_by(Invoice.invoice_date.desc())
        .all()
    )
    # datos del prescriptor
    presc_name = ""
    payment_details = ""
    if Prescriptor is not None:
        presc = db.session.get(Prescriptor, prescriptor_id)
        if presc is not None:
            presc_name = getattr(presc, "squeeze_page_name", "") or getattr(presc, "name", "")
            payment_details = getattr(presc, "payment_details", "")
    return render_template("records/upload_settlement.html", invoices=invoices, prescriptor_id=prescriptor_id,
                           presc_name=presc_name, payment_details=payment_details)


@settlements_bp.get("/invoice/<invoice_id>")
@login_required
@require_perm("manage_payments")
def invoice_detail(invoice_id):
    if Invoice is None:
        abort(404)
    inv = db.session.get(Invoice, invoice_id)
    if inv is None:
        abort(404)
    ledgers = []
    if Ledger is not None:
        ledgers = db.session.query(Ledger).filter(Ledger.invoice_id == inv.id).all()
    return render_template("records/settlement_invoice_detail.html", inv=inv, ledgers=ledgers)


@settlements_bp.post("/settle")
@login_required
@require_perm("manage_payments")
def settle():
    """Procesa rendición."""
    invoice_ids = request.form.getlist("invoice_ids")
    paid_amounts = request.form.getlist("paid_amount") or [None]*len(request.form.getlist("invoice_ids"))
    receipt_file = request.files.get("receipt")

    if not invoice_ids:
        flash("Seleccione al menos una factura", "warning")
        return redirect(request.referrer or url_for("settlements.pending_all"))

    filename = None
    if receipt_file and receipt_file.filename:
        if not _allowed_file(receipt_file.filename):
            flash("Tipo de archivo no permitido", "danger")
            return redirect(request.referrer)
        uploads_folder = Path(app.root_path) / app.config.get("RECEIPT_UPLOAD_FOLDER", "static/receipts")
        uploads_folder.mkdir(parents=True, exist_ok=True)
        filename = secure_filename(receipt_file.filename)
        receipt_file.save(uploads_folder / filename)

    try:
        settle_invoices(invoice_ids, paid_amounts, filename)
        flash(f"{len(invoice_ids)} facturas rendidas.", "success")
    except SettlementError as e:
        flash(str(e), "danger")
    except Exception:
        flash("Error inesperado", "danger")
    return redirect(url_for("settlements.pending_all"))
