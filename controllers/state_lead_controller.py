"""StateLead controller: CRUD for lead states."""
from uuid import uuid4
import math
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from sqlalchemy.exc import IntegrityError

from sigp import db
from sigp.models import Base
from sigp.security import require_perm

state_lead_bp = Blueprint("state_lead", __name__, url_prefix="/state-leads")


def _model(name):
    return getattr(Base.classes, name, None)


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------

@state_lead_bp.get("/")
@login_required
@require_perm("read_state_lead")
def state_leads_list():
    StateLead = _model("state_lead")
    if not StateLead:
        return "Modelo state_lead no disponible", 500

    q = request.args.get("q", "").strip()
    color_filter = request.args.get("color", "").strip()

    query = db.session.query(StateLead)
    if q:
        query = query.filter(StateLead.name.ilike(f"%{q}%"))
    has_color = hasattr(StateLead, "color")
    if has_color:
        if color_filter:
            query = query.filter(StateLead.color == color_filter)
        # Distinct available colors for filter dropdown
        colors_available = [c[0] for c in db.session.query(StateLead.color).distinct().all() if c[0]]
    else:
        colors_available = []

    page = int(request.args.get("page", 1))
    per_page = 10
    total = query.count()
    leads = (
        query.order_by(StateLead.name)
        .limit(per_page)
        .offset((page - 1) * per_page)
        .all()
    )
    pages = math.ceil(total / per_page)
    return render_template(
        "list/state_leads.html",
        leads=leads,
        q=q,
        color_filter=color_filter if 'color_filter' in locals() else '',
        colors_available=colors_available,
        page=page,
        pages=pages,
    )


# ---------------------------------------------------------------------------
# Create & Edit helper
# ---------------------------------------------------------------------------

def _state_lead_form(lead_id=None):
    StateLead = _model("state_lead")
    if not StateLead:
        return "Modelo state_lead no disponible", 500

    lead = db.session.get(StateLead, lead_id) if lead_id else None

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        color = request.form.get("color", "").strip()
        if not name:
            flash("El nombre es obligatorio", "warning")
        else:
            try:
                if not lead:
                    lead = StateLead(id=None)  # auto-increment handled by DB
                    db.session.add(lead)
                lead.name = name
                if hasattr(lead, "description"):
                    lead.description = description or None
                if hasattr(lead, "color"):
                    lead.color = color or None
                db.session.commit()
                flash("Estado guardado", "success")
                return redirect(url_for("state_lead.state_leads_list"))
            except IntegrityError:
                db.session.rollback()
                flash("Nombre duplicado", "danger")

    return render_template("records/state_lead_form.html", lead=lead)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@state_lead_bp.route("/new", methods=["GET", "POST"])
@login_required
@require_perm("create_state_lead")
def state_lead_new():
    return _state_lead_form()


@state_lead_bp.route("/<int:lead_id>/edit", methods=["GET", "POST"])
@login_required
@require_perm("update_state_lead")
def state_lead_edit(lead_id):
    return _state_lead_form(lead_id)


@state_lead_bp.post("/<int:lead_id>/delete")
@login_required
@require_perm("delete_state_lead")
def state_lead_delete(lead_id):
    StateLead = _model("state_lead")
    if not StateLead:
        return "Modelo state_lead no disponible", 500
    lead = db.session.get(StateLead, lead_id)
    if lead:
        db.session.delete(lead)
        db.session.commit()
        flash("Estado eliminado", "info")
    return redirect(url_for("state_lead.state_leads_list"))
