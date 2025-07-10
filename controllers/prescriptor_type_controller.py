"""PrescriptorType controller: CRUD for prescriptor types."""
import math
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from sqlalchemy.exc import IntegrityError

from sigp import db
from sigp.models import Base
from sigp.security import require_perm

prescriptor_type_bp = Blueprint("prescriptor_type", __name__, url_prefix="/prescriptor-types")

def _model(name):
    return getattr(Base.classes, name, None)

# List
@prescriptor_type_bp.get("/")
@login_required
@require_perm("read_prescriptor_type")
def types_list():
    M = _model("prescriptor_types")
    if not M:
        return "Modelo prescriptor_types no disponible", 500
    q = request.args.get("q", "").strip()
    query = db.session.query(M)
    if q:
        query = query.filter(M.name.ilike(f"%{q}%"))
    page = int(request.args.get("page", 1))
    per_page = 10
    total = query.count()
    rows = query.order_by(M.name).limit(per_page).offset((page-1)*per_page).all()
    pages = math.ceil(total/per_page)
    return render_template("list/prescriptor_types.html", rows=rows, q=q, page=page, pages=pages)

# helper

def _form(row_id=None):
    M = _model("prescriptor_types")
    if not M:
        return "Modelo prescriptor_types no disponible", 500
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
                flash("Tipo guardado", "success")
                return redirect(url_for("prescriptor_type.types_list"))
            except IntegrityError:
                db.session.rollback()
                flash("Nombre duplicado", "danger")
    return render_template("records/prescriptor_type_form.html", row=row)

@prescriptor_type_bp.route("/new", methods=["GET", "POST"])
@login_required
@require_perm("create_prescriptor_type")
def new():
    return _form()

@prescriptor_type_bp.route("/<int:row_id>/edit", methods=["GET", "POST"])
@login_required
@require_perm("update_prescriptor_type")
def edit(row_id):
    return _form(row_id)

@prescriptor_type_bp.post("/<int:row_id>/delete")
@login_required
@require_perm("delete_prescriptor_type")
def delete(row_id):
    M = _model("prescriptor_types")
    if not M:
        return "Modelo prescriptor_types no disponible", 500
    row = db.session.get(M, row_id)
    if row:
        db.session.delete(row)
        db.session.commit()
        flash("Tipo eliminado", "info")
    return redirect(url_for("prescriptor_type.types_list"))
