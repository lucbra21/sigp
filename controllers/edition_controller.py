"""Edition controller: CRUD for program editions."""
import math
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from sqlalchemy.exc import IntegrityError

from sigp import db
from sigp.models import Base
from sigp.security import require_perm

edition_bp = Blueprint("edition", __name__, url_prefix="/editions")


def _model(name):
    return getattr(Base.classes, name, None)


# -------------------- LIST --------------------
@edition_bp.get("/")
@login_required
@require_perm("read_edition")
def editions_list():
    M = _model("editions")
    if not M:
        return "Modelo editions no disponible", 500
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
        "list/editions.html", rows=rows, q=q, page=page, pages=pages
    )


# -------------------- FORM helper --------------------

def _form(row_id=None):
    M = _model("editions")
    if not M:
        return "Modelo editions no disponible", 500
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
                flash("Edición guardada", "success")
                return redirect(url_for("edition.editions_list"))
            except IntegrityError:
                db.session.rollback()
                flash("Nombre duplicado", "danger")
    return render_template("records/edition_form.html", row=row)


# -------------------- CREATE / UPDATE / DELETE --------------------


@edition_bp.route("/new", methods=["GET", "POST"])
@login_required
@require_perm("create_edition")
def new():
    return _form()


@edition_bp.route("/<int:row_id>/edit", methods=["GET", "POST"])
@login_required
@require_perm("update_edition")
def edit(row_id):
    return _form(row_id)


@edition_bp.post("/<int:row_id>/delete")
@login_required
@require_perm("delete_edition")
def delete(row_id):
    M = _model("editions")
    if not M:
        return "Modelo editions no disponible", 500
    row = db.session.get(M, row_id)
    if row:
        db.session.delete(row)
        db.session.commit()
        flash("Edición eliminada", "info")
    return redirect(url_for("edition.editions_list"))
