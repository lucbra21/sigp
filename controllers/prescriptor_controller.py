"""Controlador de Prescriptores.

CRUD básico usando modelos reflejados.
"""

from flask import (
    current_app,
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
from wtforms.validators import DataRequired, Length, Optional, URL

from sigp import db
import uuid
from sigp.models import Base

# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

prescriptors_bp = Blueprint("prescriptors", __name__, url_prefix="/prescriptors")

# ---------------------------------------------------------------------------
# Dynamic WTForm
# ---------------------------------------------------------------------------


def _get_select_choices(model_name: str):
    Model = getattr(Base.classes, model_name, None)
    if not Model:
        return []
    rows = db.session.query(Model).all()
    return [(str(r.id), getattr(r, "name", getattr(r, "nombre", ""))) for r in rows]


def prescriptor_form_factory(is_create=True):
    """Genera un formulario dinámico para Prescriptor."""

    state_choices = _get_select_choices("state_prescriptor")
    type_choices = _get_select_choices("prescriptor_types")
    substate_choices = [("", "-")] + _get_select_choices("substate_prescriptor")
    conf_choices = [("", "-")] + _get_select_choices("confidence_level")
    squeeze_status_choices = [("TEST", "TEST"), ("PRODUCCION", "PRODUCCION"), ("DESACTIVADA", "DESACTIVADA")]

    class _PrescriptorForm(FlaskForm):
        user_id = StringField("Usuario", render_kw={"readonly": True})
        type_id = SelectField("Tipo", choices=type_choices, validators=[DataRequired()])
        proposed_type_id = SelectField("Tipo propuesto", choices=[("", "-")] + type_choices, validators=[Optional()])
        state_id = SelectField("Estado", choices=state_choices, validators=[DataRequired()])
        sub_state = SelectField("Subestado", choices=substate_choices, validators=[Optional()])
        squeeze_url_tst = StringField("Squeeze URL Test", validators=[Optional(), URL(), Length(max=255)])
        squeeze_url_prd = StringField("Squeeze URL Prod", validators=[Optional(), URL(), Length(max=255)])
        confidence_level_id = SelectField("Nivel de confianza", choices=conf_choices, validators=[Optional()])
        squeeze_page_name = StringField("Nombre", validators=[DataRequired(), Length(max=255)])
        squeeze_page_status = SelectField("Estado squeeze page", choices=squeeze_status_choices, validators=[Optional()])
        submit = SubmitField("Guardar")

        class Meta:
            csrf = True

        # Eliminar campos que no deben mostrarse en el alta
    if is_create:
        for fld in [
            "type_id",
            "state_id",
            "sub_state",
            "squeeze_url_tst",
            "squeeze_url_prd",
            "squeeze_page_status",
        ]:
            if hasattr(_PrescriptorForm, fld):
                delattr(_PrescriptorForm, fld)
    return _PrescriptorForm


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_model():
    return getattr(Base.classes, "prescriptors", None)


# def _get_estado_choices():
#     """Legacy helper no longer used"""
#     return []
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

    # Parámetros de paginación y filtros
    page = request.args.get("page", 1, type=int)
    per_page = 20
    nombre_f = request.args.get("nombre", type=str, default="").strip()
    tipo_f = request.args.get("tipo", type=str, default="")
    estado_f = request.args.get("estado", type=str, default="")

    # Modelos relacionados
    Types = getattr(Base.classes, "prescriptor_types", None)
    Users = getattr(Base.classes, "users", None)
    States = getattr(Base.classes, "state_prescriptor", None)

    # Query principal con joins para obtener nombres legibles
    query = (
        db.session.query(
            Model.id.label("id"),
            Model.squeeze_page_name.label("nombre"),
            Types.name.label("tipo"),
            States.name.label("estado"),
            Users.name.label("usuario"),
        )
        .outerjoin(Types, Types.id == Model.type_id)
        .outerjoin(States, States.id == Model.state_id)
        .outerjoin(Users, Users.id == Model.user_id)
    )

    # Aplicar filtros si vienen
    if nombre_f:
        query = query.filter(Model.squeeze_page_name.ilike(f"%{nombre_f}%"))
    if tipo_f:
        query = query.filter(Model.type_id == int(tipo_f))
    if estado_f:
        query = query.filter(Model.state_id == int(estado_f))

    total = query.count()
    items = (
        query.order_by(Model.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    # Para selects del filtro
    type_choices = _get_select_choices("prescriptor_types")
    state_choices = _get_select_choices("state_prescriptor")

    return render_template(
        "list/prescriptors.html",
        items=items,
        page=page,
        per_page=per_page,
        filters={"nombre": nombre_f, "tipo": tipo_f, "estado": estado_f},
        type_choices=type_choices,
        state_choices=state_choices,
        total=total,
    )


@prescriptors_bp.get("/new")
@login_required
def new_prescriptor():
    FormClass = prescriptor_form_factory(is_create=True)
    form = FormClass()
    current_app.logger.info(">>> creando prescriptor con data %s", form.data)
    form.user_id.data = current_user.name
    return render_template(
        "records/prescriptor_form.html",
        form=form,
        action=url_for("prescriptors.create_prescriptor"),
    )


@prescriptors_bp.post("/")
@login_required
def create_prescriptor():
    Model = _get_model()
    if not Model:
        flash("Modelo no disponible", "danger")
        return redirect(url_for("prescriptors.list_prescriptors"))

    FormClass = prescriptor_form_factory(is_create=True)
    form = FormClass()
    current_app.logger.info(">>> creando prescriptor con data %s", form.data)

    if form.validate_on_submit():
        # Construir objeto con todos los campos disponibles
        new_obj = Model(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            type_id=int(form.type_id.data),
            proposed_type_id=int(form.proposed_type_id.data) if form.proposed_type_id.data else None,
            state_id=int(form.state_id.data),
            sub_state_id=int(form.sub_state.data) if form.sub_state.data else None,
            confidence_level_id=int(form.confidence_level_id.data) if form.confidence_level_id.data else None,
            squeeze_url_tst=form.squeeze_url_tst.data or None,
            squeeze_url_prd=form.squeeze_url_prd.data or None,
            squeeze_page_name=form.squeeze_page_name.data,
            squeeze_page_status=form.squeeze_page_status.data or None,
        )
        # Establecer valores por defecto de negocio
        # Estado Activo (1)
        if hasattr(new_obj, "state_id"):
            new_obj.state_id = 1
        # Sub estado Candidato (1)
        if hasattr(new_obj, "sub_state_id"):
            new_obj.sub_state_id = 1
        # Squeeze page status TEST
        if hasattr(new_obj, "squeeze_page_status") and not new_obj.squeeze_page_status:
            new_obj.squeeze_page_status = "TEST"
        # Guardar usuario logueado en user_getter_id si existe dicha columna
        if hasattr(new_obj, "user_getter_id"):
            new_obj.user_getter_id = current_user.id

        db.session.add(new_obj)
        try:
            db.session.commit()
            flash("Prescriptor creado", "success")
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception("Error al guardar prescriptor: %s", e)
            flash("Error al guardar prescriptor", "danger")
            return render_template("records/prescriptor_form.html", form=form, action=url_for("prescriptors.create_prescriptor"))
        return redirect(url_for("prescriptors.list_prescriptors"))

    current_app.logger.info("Errores de validación: %s", form.errors)
    flash("Errores en el formulario", "danger")
    return render_template("records/prescriptor_form.html", form=form, action=url_for("prescriptors.create_prescriptor"))


@prescriptors_bp.get("/<prescriptor_id>/edit")
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

    FormClass = prescriptor_form_factory(is_create=False)
    form = FormClass(obj=obj)
    return render_template(
        "records/prescriptor_form.html",
        form=form,
        action=url_for("prescriptors.update_prescriptor", prescriptor_id=prescriptor_id),
    )


@prescriptors_bp.post("/<prescriptor_id>")
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

    FormClass = prescriptor_form_factory(is_create=False)
    form = FormClass()
    current_app.logger.info(">>> creando prescriptor con data %s", form.data)

    if form.validate_on_submit():
        
        
        obj.state_id = int(form.state_id.data)
        try:
            db.session.commit()
            flash("Prescriptor actualizado", "success")
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception("Error al actualizar prescriptor: %s", e)
            flash("Error al actualizar prescriptor", "danger")
            return render_template("records/prescriptor_form.html", form=form, action=url_for("prescriptors.update_prescriptor", prescriptor_id=prescriptor_id))
        return redirect(url_for("prescriptors.list_prescriptors"))

    current_app.logger.info("Errores de validación: %s", form.errors)
    flash("Errores en el formulario", "danger")
    return render_template(
        "records/prescriptor_form.html",
        form=form,
        action=url_for("prescriptors.update_prescriptor", prescriptor_id=prescriptor_id),
    )
