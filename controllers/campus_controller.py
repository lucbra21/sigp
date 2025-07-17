"""Campus controller: CRUD similar to roles."""
from flask import Blueprint, render_template, request, redirect, url_for, flash
import uuid, math
from flask_login import login_required

from sigp import db
from sigp.models import Base

campus_bp = Blueprint("campus", __name__, url_prefix="/campus")


def _model():
    return getattr(Base.classes, "campus", None)


@campus_bp.get("/")
@login_required
def campus_list():
    Campus = _model()
    if not Campus:
        return "Modelo campus no disponible", 500

    q = request.args.get("q", "").strip()
    query = db.session.query(Campus)
    if q and hasattr(Campus, "name"):
        query = query.filter(Campus.name.ilike(f"%{q}%"))

    page = int(request.args.get("page", 1))
    per_page = 10
    total = query.count()
    campuses = (
        query.order_by(getattr(Campus, "name", Campus.id))
        .limit(per_page)
        .offset((page - 1) * per_page)
        .all()
    )
    pages = math.ceil(total / per_page)
    return render_template("list/campuses.html", campuses=campuses, q=q, page=page, pages=pages)


@campus_bp.route("/new", methods=["GET", "POST"])
@login_required
def campus_new():
    Campus = _model()
    if not Campus:
        return "Modelo campus no disponible", 500

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("El nombre es obligatorio", "danger")
            return redirect(url_for("campus.campus_new"))
        c = Campus(id=str(uuid.uuid4()), name=name)
        db.session.add(c)
        db.session.commit()
        flash("Campus creado", "success")
        return redirect(url_for("campus.campus_list"))
    return render_template("records/campus_form.html", campus=None)


@campus_bp.route("/<campus_id>/edit", methods=["GET", "POST"])
@login_required
def campus_edit(campus_id):
    Campus = _model()
    if not Campus:
        return "Modelo campus no disponible", 500
    campus = db.session.get(Campus, campus_id)
    if not campus:
        flash("Campus no encontrado", "warning")
        return redirect(url_for("campus.campus_list"))
    if request.method == "POST":
        campus.name = request.form.get("name", campus.name).strip()
        db.session.commit()
        flash("Campus actualizado", "success")
        return redirect(url_for("campus.campus_list"))
    return render_template("records/campus_form.html", campus=campus)


@campus_bp.post("/<campus_id>/delete")
@login_required
def campus_delete(campus_id):
    Campus = _model()
    if not Campus:
        return "Modelo campus no disponible", 500
    campus = db.session.get(Campus, campus_id)
    if campus:
        db.session.delete(campus)
        db.session.commit()
        flash("Campus eliminado", "info")
    return redirect(url_for("campus.campus_list"))
