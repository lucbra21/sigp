"""ConfidenceLevel controller: CRUD for confidence levels."""
import math
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from sqlalchemy.exc import IntegrityError

from sigp import db
from sigp.models import Base
from sigp.security import require_perm

confidence_level_bp = Blueprint("confidence_level", __name__, url_prefix="/confidence-levels")


def _model(name):
    return getattr(Base.classes, name, None)


# -------------------- LIST --------------------
@confidence_level_bp.get("/")
@login_required
@require_perm("read_confidence_level")
def levels_list():
    M = _model("confidence_level")
    if not M:
        return "Modelo confidence_level no disponible", 500
    q = request.args.get("q", "").strip()
    query = db.session.query(M)
    if q:
        query = query.filter(M.name.ilike(f"%{q}%"))
    page = int(request.args.get("page", 1))
    per_page = 10
    total = query.count()
    rows = (
        query.order_by(M.name)
        .limit(per_page)
        .offset((page - 1) * per_page)
        .all()
    )
    pages = math.ceil(total / per_page)
    return render_template(
        "list/confidence_levels.html", rows=rows, q=q, page=page, pages=pages
    )


# -------------------- FORM helper --------------------

def _form(row_id=None):
    M = _model("confidence_level")
    if not M:
        return "Modelo confidence_level no disponible", 500
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
                flash("Nivel de confianza guardado", "success")
                return redirect(url_for("confidence_level.levels_list"))
            except IntegrityError:
                db.session.rollback()
                flash("Nombre duplicado", "danger")
    return render_template("records/confidence_level_form.html", row=row)


# -------------------- CREATE / UPDATE / DELETE --------------------


@confidence_level_bp.route("/new", methods=["GET", "POST"])
@login_required
@require_perm("create_confidence_level")
def new():
    return _form()


@confidence_level_bp.route("/<int:row_id>/edit", methods=["GET", "POST"])
@login_required
@require_perm("update_confidence_level")
def edit(row_id):
    return _form(row_id)


@confidence_level_bp.post("/<int:row_id>/delete")
@login_required
@require_perm("delete_confidence_level")
def delete(row_id):
    M = _model("confidence_level")
    if not M:
        return "Modelo confidence_level no disponible", 500
    row = db.session.get(M, row_id)
    if row:
        db.session.delete(row)
        db.session.commit()
        flash("Nivel de confianza eliminado", "info")
    return redirect(url_for("confidence_level.levels_list"))
