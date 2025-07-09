"""StatePrescriptor controller: CRUD for prescriptor states."""
import math
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from sqlalchemy.exc import IntegrityError

from sigp import db
from sigp.models import Base
from sigp.security import require_perm

state_prescriptor_bp = Blueprint("state_prescriptor", __name__, url_prefix="/state-prescriptors")

def _model(name):
    return getattr(Base.classes, name, None)

# List
@state_prescriptor_bp.get("/")
@login_required
@require_perm("read_state_prescriptor")
def state_prescriptors_list():
    M = _model("state_prescriptor")
    if not M:
        return "Modelo state_prescriptor no disponible", 500
    q = request.args.get("q", "").strip()
    query = db.session.query(M)
    if q:
        query = query.filter(M.name.ilike(f"%{q}%"))
    page = int(request.args.get("page", 1))
    per_page = 10
    total = query.count()
    rows = query.order_by(M.name).limit(per_page).offset((page-1)*per_page).all()
    pages = math.ceil(total/per_page)
    return render_template("list/state_prescriptors.html", rows=rows, q=q, page=page, pages=pages)

# helper

def _form(row_id=None):
    M = _model("state_prescriptor")
    if not M:
        return "Modelo state_prescriptor no disponible", 500
    row = db.session.get(M, row_id) if row_id else None
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("El nombre es obligatorio", "warning")
        else:
            try:
                if not row:
                    row = M(id=None)
                    db.session.add(row)
                row.name = name
                db.session.commit()
                flash("Estado guardado", "success")
                return redirect(url_for("state_prescriptor.state_prescriptors_list"))
            except IntegrityError:
                db.session.rollback()
                flash("Nombre duplicado", "danger")
    return render_template("records/state_prescriptor_form.html", row=row)

@state_prescriptor_bp.route("/new", methods=["GET", "POST"])
@login_required
@require_perm("create_state_prescriptor")
def new():
    return _form()

@state_prescriptor_bp.route("/<int:row_id>/edit", methods=["GET", "POST"])
@login_required
@require_perm("update_state_prescriptor")
def edit(row_id):
    return _form(row_id)

@state_prescriptor_bp.post("/<int:row_id>/delete")
@login_required
@require_perm("delete_state_prescriptor")
def delete(row_id):
    M = _model("state_prescriptor")
    if not M:
        return "Modelo state_prescriptor no disponible", 500
    row = db.session.get(M, row_id)
    if row:
        db.session.delete(row)
        db.session.commit()
        flash("Estado eliminado", "info")
    return redirect(url_for("state_prescriptor.state_prescriptors_list"))
