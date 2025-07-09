"""Controlador de autenticación.

Define un Blueprint llamado ``auth`` con rutas para login y logout.
"""
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
)
from flask_login import login_user, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length

import hashlib
from sigp import db, bcrypt
from sigp.models import Base

# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# ---------------------------------------------------------------------------
# Formulario de Login
# ---------------------------------------------------------------------------


class LoginForm(FlaskForm):
    email = StringField(
        "Correo electrónico",
        validators=[DataRequired(), Email(), Length(max=255)],
        render_kw={"placeholder": "email@example.com"},
    )
    password = PasswordField(
        "Contraseña", validators=[DataRequired(), Length(min=4, max=255)]
    )
    remember = BooleanField("Recordarme")
    submit = SubmitField("Ingresar")

    class Meta:
        csrf = True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_user_class():
    """Obtiene la clase de usuario reflejada, asumiendo tabla ``users``."""
    return getattr(Base.classes, "users", None)


# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------


@auth_bp.get("/login")
def login_get():
    # Si ya está logueado redirigimos
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = LoginForm()
    return render_template("layouts/login.html", form=form)


@auth_bp.post("/login")
def login_post():
    form = LoginForm(request.form)

    if not form.validate_on_submit():
        flash("Datos de formulario inválidos", "danger")
        return redirect(url_for("auth.login_get"))

    User = _get_user_class()
    if not User:
        flash("Modelo de usuario no disponible", "danger")
        return redirect(url_for("auth.login_get"))

    user = db.session.query(User).filter_by(email=form.email.data).first()

    if user and user.password_hash and user.password_hash.lower() == hashlib.sha256(form.password.data.encode()).hexdigest():
        login_user(user, remember=form.remember.data)
        return redirect("/")

    flash("Credenciales incorrectas", "danger")
    return redirect(url_for("auth.login_get"))


@auth_bp.get("/logout")
def logout():
    logout_user()
    flash("Sesión finalizada", "info")
    return redirect(url_for("auth.login_get"))
