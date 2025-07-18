"""Users controller: ABM con paginación y filtro."""
import uuid
import math
import hashlib
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)
from flask_login import login_required

from sigp import db
from sqlalchemy import or_
from sigp.models import Base

users_bp = Blueprint("users", __name__, url_prefix="/users")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _model(name):
    return getattr(Base.classes, name, None)


def _get_choices(model):
    return db.session.query(model).order_by(model.name).all() if model else []


# ---------------------------------------------------------------------------
# Listado
# ---------------------------------------------------------------------------


@users_bp.get("/")
@login_required
def users_list():
    User = _model("users")
    Role = _model("roles")
    if not User:
        return "Modelo users no disponible", 500

    q = request.args.get("q", "").strip()
    role_filter = request.args.get("role")
    state_filter = request.args.get("state", "2")

    query = db.session.query(User)
    if q:
        query = query.filter(
            or_(
                User.email.ilike(f"%{q}%"),
                User.name.ilike(f"%{q}%"),
                User.lastname.ilike(f"%{q}%"),
            )
        )
    if role_filter:
        query = query.filter(User.role_id == role_filter)
    if state_filter:
        query = query.filter(User.state_id == int(state_filter))

    page = int(request.args.get("page", 1))
    per_page = 10
    total = query.count()
    users = (
        query.order_by(User.email)
        .limit(per_page)
        .offset((page - 1) * per_page)
        .all()
    )
    pages = math.ceil(total / per_page)
    roles_full = _get_choices(Role)
    roles_lookup = {r.id: r.name for r in roles_full}
    return render_template(
        "list/users.html",
        users=users,
        q=q,
        page=page,
        pages=pages,
        roles=roles_full,
        roles_lookup=roles_lookup,
        role_filter=role_filter,
        state_filter=state_filter,
    )


# ---------------------------------------------------------------------------
# Crear y editar
# ---------------------------------------------------------------------------


@users_bp.route("/new", methods=["GET", "POST"])
@login_required
def user_new():
    return _user_form()


@users_bp.route("/<user_id>/edit", methods=["GET", "POST"])
@login_required
def user_edit(user_id):
    return _user_form(user_id)


def _user_form(user_id=None):
    User = _model("users")
    Role = _model("roles")
    if not User:
        return "Modelo users no disponible", 500

    user = db.session.get(User, user_id) if user_id else None

    roles = _get_choices(Role)
    state_choices = [
        (1, "Inactivo"),
        (2, "Activo"),
        (3, "Suspendido"),
    ]

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        name = request.form.get("name", "").strip()
        lastname = request.form.get("lastname", "").strip()
        cellular = request.form.get("cellular", "").strip()
        role_id = request.form.get("role_id")
        state_id = int(request.form.get("state_id", 2))
        password = request.form.get("password", "").strip()

        # Validations
        if not email or not name:
            flash("Email y nombre son obligatorios", "danger")
            return redirect(request.url)
        # Verificar duplicado de email
        existing = db.session.query(User).filter(User.email == email).first()
        if existing and (user is None or existing.id != user.id):
            flash("El email ya está registrado en otro usuario", "danger")
            return redirect(request.url)

        
            flash("Email y nombre son obligatorios", "danger")
            return redirect(request.url)

        if user is None:
            user = User(id=str(uuid.uuid4()))
            db.session.add(user)

        user.email = email.strip().lower()
        user.name = name
        user.lastname = lastname
        user.cellular = cellular
        user.role_id = role_id
        user.state_id = state_id

        if password:
            user.password_hash = hashlib.sha256(password.encode()).hexdigest()

        db.session.commit()
        flash("Usuario guardado", "success")
        return redirect(url_for("users.users_list"))

    return render_template(
        "records/user_form.html",
        user=user,
        roles=roles,
        state_choices=state_choices,
    )


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


@users_bp.post("/<user_id>/delete")
@login_required
def user_delete(user_id):
    User = _model("users")
    if not User:
        return "Modelo users no disponible", 500
    user = db.session.get(User, user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash("Usuario eliminado", "info")
    return redirect(url_for("users.users_list"))
