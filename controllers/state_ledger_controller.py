"""StateLedger controller: CRUD for ledger states."""
import math
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from sqlalchemy.exc import IntegrityError

from sigp import db
from sigp.models import Base
from sigp.security import require_perm

state_ledger_bp = Blueprint("state_ledger", __name__, url_prefix="/state-ledgers")

def _model(name):
    return getattr(Base.classes, name, None)

# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

@state_ledger_bp.get("/")
@login_required
@require_perm("read_state_ledger")
def state_ledgers_list():
    StateLedger = _model("state_ledger")
    if not StateLedger:
        return "Modelo state_ledger no disponible", 500

    q = request.args.get("q", "").strip()
    query = db.session.query(StateLedger)
    if q:
        query = query.filter(StateLedger.name.ilike(f"%{q}%"))

    page = int(request.args.get("page", 1))
    per_page = 10
    total = query.count()
    ledgers = (
        query.order_by(StateLedger.name)
        .limit(per_page)
        .offset((page - 1) * per_page)
        .all()
    )
    pages = math.ceil(total / per_page)
    return render_template(
        "list/state_ledgers.html",
        ledgers=ledgers,
        q=q,
        page=page,
        pages=pages,
    )

# ---------------------------------------------------------------------------
# Create/Edit helper
# ---------------------------------------------------------------------------

def _state_ledger_form(ledger_id=None):
    StateLedger = _model("state_ledger")
    if not StateLedger:
        return "Modelo state_ledger no disponible", 500
    ledger = db.session.get(StateLedger, ledger_id) if ledger_id else None

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("El nombre es obligatorio", "warning")
        else:
            try:
                if not ledger:
                    ledger = StateLedger(id=None)
                    db.session.add(ledger)
                ledger.name = name
                db.session.commit()
                flash("Estado guardado", "success")
                return redirect(url_for("state_ledger.state_ledgers_list"))
            except IntegrityError:
                db.session.rollback()
                flash("Nombre duplicado", "danger")
    return render_template("records/state_ledger_form.html", ledger=ledger)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@state_ledger_bp.route("/new", methods=["GET", "POST"])
@login_required
@require_perm("create_state_ledger")
def state_ledger_new():
    return _state_ledger_form()

@state_ledger_bp.route("/<int:ledger_id>/edit", methods=["GET", "POST"])
@login_required
@require_perm("update_state_ledger")
def state_ledger_edit(ledger_id):
    return _state_ledger_form(ledger_id)

@state_ledger_bp.post("/<int:ledger_id>/delete")
@login_required
@require_perm("delete_state_ledger")
def state_ledger_delete(ledger_id):
    StateLedger = _model("state_ledger")
    if not StateLedger:
        return "Modelo state_ledger no disponible", 500
    ledger = db.session.get(StateLedger, ledger_id)
    if ledger:
        db.session.delete(ledger)
        db.session.commit()
        flash("Estado eliminado", "info")
    return redirect(url_for("state_ledger.state_ledgers_list"))
