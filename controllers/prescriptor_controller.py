"""Controlador de Prescriptores.

CRUD básico usando modelos reflejados.
"""

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length

from sigp import db
from sigp.models import Base

# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

prescriptors_bp = Blueprint("prescriptors", __name__, url_prefix="/prescriptors")

# ---------------------------------------------------------------------------
# Dynamic WTForm
# ---------------------------------------------------------------------------


def prescriptor_form_factory(states: list[str]):
    """Genera un formulario dinámico para Prescriptor."""

    class _PrescriptorForm(FlaskForm):
        nombre = StringField(
            "Nombre",
            validators=[DataRequired(), Length(max=255)],
            render_kw={"placeholder": "Nombre del prescriptor"},
        )
        tipo = StringField(
            "Tipo",
            validators=[DataRequired(), Length(max=100)],
            render_kw={"placeholder": "Tipo"},
        )
        estado = SelectField("Estado", choices=[(s, s) for s in states], validators=[DataRequired()])
        submit = SubmitField("Guardar")

        class Meta:
            csrf = True

    return _PrescriptorForm


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_model():
    return getattr(Base.classes, "prescriptors", None)


def _get_estado_choices():
    """Devuelve listado de estados únicos (ejemplo)"""
    Model = _get_model()
    if not Model:
        return []
    estados = db.session.query(Model.estado).distinct().all()
    return [e[0] for e in estados if e[0] is not None]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@prescriptors_bp.get("/")
@login_required
def list_prescriptors():
    Model = _get_model()
    if not Model:
        flash("Modelo Prescriptor no disponible", "danger")
        return redirect("/")

    page = request.args.get("page", 1, type=int)
    per_page = 20

    query = db.session.query(Model)
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()

    return render_template(
        "list/prescriptors.html",
        items=items,
        page=page,
        per_page=per_page,
        total=total,
    )


@prescriptors_bp.get("/new")
@login_required
def new_prescriptor():
    states = _get_estado_choices()
    FormClass = prescriptor_form_factory(states)
    form = FormClass()
    return render_template("records/prescriptor_form.html", form=form, action=url_for("prescriptors.create_prescriptor"))


@prescriptors_bp.post("/")
@login_required
def create_prescriptor():
    Model = _get_model()
    if not Model:
        flash("Modelo no disponible", "danger")
        return redirect(url_for("prescriptors.list_prescriptors"))

    states = _get_estado_choices()
    FormClass = prescriptor_form_factory(states)
    form = FormClass()

    if form.validate_on_submit():
        new_obj = Model(
            nombre=form.nombre.data,
            tipo=form.tipo.data,
            estado=form.estado.data,
        )
        db.session.add(new_obj)
        db.session.commit()
        flash("Prescriptor creado", "success")
        return redirect(url_for("prescriptors.list_prescriptors"))

    flash("Errores en el formulario", "danger")
    return render_template("records/prescriptor_form.html", form=form, action=url_for("prescriptors.create_prescriptor"))


@prescriptors_bp.get("/<int:prescriptor_id>/edit")
@login_required
def edit_prescriptor(prescriptor_id):
    Model = _get_model()
    if not Model:
        flash("Modelo no disponible", "danger")
        return redirect(url_for("prescriptors.list_prescriptors"))

    obj = db.session.get(Model, prescriptor_id)
    if not obj:
        flash("Prescriptor no encontrado", "warning")
        return redirect(url_for("prescriptors.list_prescriptors"))

    states = _get_estado_choices()
    FormClass = prescriptor_form_factory(states)
    form = FormClass(obj=obj)
    return render_template(
        "records/prescriptor_form.html",
        form=form,
        action=url_for("prescriptors.update_prescriptor", prescriptor_id=prescriptor_id),
    )


@prescriptors_bp.post("/<int:prescriptor_id>/")
@login_required
def update_prescriptor(prescriptor_id):
    Model = _get_model()
    if not Model:
        flash("Modelo no disponible", "danger")
        return redirect(url_for("prescriptors.list_prescriptors"))

    obj = db.session.get(Model, prescriptor_id)
    if not obj:
        flash("Prescriptor no encontrado", "warning")
        return redirect(url_for("prescriptors.list_prescriptors"))

    states = _get_estado_choices()
    FormClass = prescriptor_form_factory(states)
    form = FormClass()

    if form.validate_on_submit():
        obj.nombre = form.nombre.data
        obj.tipo = form.tipo.data
        obj.estado = form.estado.data
        db.session.commit()
        flash("Prescriptor actualizado", "success")
        return redirect(url_for("prescriptors.list_prescriptors"))

    flash("Errores en el formulario", "danger")
    return render_template(
        "records/prescriptor_form.html",
        form=form,
        action=url_for("prescriptors.update_prescriptor", prescriptor_id=prescriptor_id),
    )
