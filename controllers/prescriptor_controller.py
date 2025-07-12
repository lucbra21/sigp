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
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, URL

from sigp import db
import os
from werkzeug.utils import secure_filename
import hashlib
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
        # squeeze_url_tst = StringField("Squeeze URL Test", validators=[Optional(), URL(), Length(max=255)])
        # squeeze_url_prd = StringField("Squeeze URL Prod", validators=[Optional(), URL(), Length(max=255)])

        photo_file = FileField("Foto", validators=[Optional(), FileAllowed(['jpg','jpeg','png','gif'], 'Imágenes')])
        squeeze_page_image_1_file = FileField("Imagen 1", validators=[Optional(), FileAllowed(['jpg','jpeg','png','gif'], 'Imágenes')])
        squeeze_page_image_2_file = FileField("Imagen 2", validators=[Optional(), FileAllowed(['jpg','jpeg','png','gif'], 'Imágenes')])
        squeeze_page_image_3_file = FileField("Imagen 3", validators=[Optional(), FileAllowed(['jpg','jpeg','png','gif'], 'Imágenes')])
        face_url = StringField("Facebook URL", validators=[Optional(), Length(max=255)])
        linkedin_url = StringField("LinkedIn URL", validators=[Optional(), Length(max=255)])
        instagram_url = StringField("Instagram URL", validators=[Optional(), Length(max=255)])
        x_url = StringField("X/Twitter URL", validators=[Optional(), Length(max=255)])
        confidence_level_id = SelectField("Nivel de confianza", choices=conf_choices, validators=[Optional()])
        email = StringField("Email", validators=[DataRequired(), Length(max=255)])
        cellular = StringField("Celular", validators=[DataRequired(), Length(max=50)])
        squeeze_page_name = StringField("Nombre", validators=[DataRequired(), Length(max=255)])
        squeeze_page_status = SelectField("Estado squeeze page", choices=squeeze_status_choices, validators=[Optional()])
        observations = TextAreaField("Observaciones", validators=[Optional(), Length(max=1000)])
        contract_file = FileField("Contrato (PDF)", validators=[FileAllowed(["pdf"], "Solo PDF")])
        submit = SubmitField("Guardar")

        class Meta:
            csrf = True

        # Eliminar campos que no deben mostrarse en el alta
    # Ocultar en creación campos avanzados
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
        # Construir dinámicamente los campos disponibles en el formulario
        obj_kwargs = {
            "id": str(uuid.uuid4()),
            "squeeze_page_name": form.squeeze_page_name.data,
        }
        if hasattr(form, "type_id") and form.type_id.data:
            obj_kwargs["type_id"] = int(form.type_id.data)
        if hasattr(form, "proposed_type_id") and form.proposed_type_id.data:
            obj_kwargs["proposed_type_id"] = int(form.proposed_type_id.data)
            # Si no hay type_id en el formulario, usar el mismo valor para cumplir NOT NULL
            if "type_id" not in obj_kwargs:
                obj_kwargs["type_id"] = obj_kwargs["proposed_type_id"]
        if hasattr(form, "state_id") and form.state_id.data:
            obj_kwargs["state_id"] = int(form.state_id.data)
        if hasattr(form, "sub_state") and form.sub_state.data:
            obj_kwargs["sub_state_id"] = int(form.sub_state.data)
        if hasattr(form, "confidence_level_id") and form.confidence_level_id.data:
            obj_kwargs["confidence_level_id"] = int(form.confidence_level_id.data)
        if hasattr(form, "squeeze_url_tst"):
            obj_kwargs["squeeze_url_tst"] = form.squeeze_url_tst.data or None
        if hasattr(form, "squeeze_url_prd"):
            obj_kwargs["squeeze_url_prd"] = form.squeeze_url_prd.data or None
        # social URLs
        for fld in ["face_url","linkedin_url","instagram_url","x_url"]:
            if hasattr(form, fld):
                obj_kwargs[fld] = getattr(form, fld).data or None
        if hasattr(form, "squeeze_page_status"):
            obj_kwargs["squeeze_page_status"] = form.squeeze_page_status.data or "TEST"
        if hasattr(form, "observations") and form.observations.data:
             obj_kwargs["observations"] = form.observations.data
        if hasattr(form, "contract_file") and form.contract_file.data:
            filename = f"{obj_kwargs['id']}.pdf"
            path = current_app.config["CONTRACT_UPLOAD_FOLDER"] / filename
            form.contract_file.data.save(path)
            obj_kwargs["contract_url"] = url_for("static", filename=f"contracts/{filename}")

        # Crear usuario asociado
        UserModel = getattr(Base.classes, "users", None)
        if not UserModel:
            flash("Modelo users no disponible", "danger")

        new_user = UserModel(id=str(uuid.uuid4()))
        new_user.name = form.squeeze_page_name.data
        new_user.email = form.email.data
        new_user.cellular = form.cellular.data
        new_user.role_id = "5e6e517e-584b-42be-a7a3-564ee14e8723"
        new_user.state_id = 1  # INACTIVO
        # asignar password aleatorio
        temp_pass = str(uuid.uuid4())
        new_user.password_hash = hashlib.sha256(temp_pass.encode()).hexdigest()
        db.session.add(new_user)
        db.session.flush()  # obtener id

        obj_kwargs["user_id"] = new_user.id

        new_obj = Model(**obj_kwargs)
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
    # precargar datos de usuario (dueño) y nombre creador
    UserModel = getattr(Base.classes, "users", None)
    if UserModel:
        # dueño (login del prescriptor)
        if obj.user_id:
            u_owner = db.session.get(UserModel, obj.user_id)
            if u_owner:
                form.email.data = u_owner.email
                form.cellular.data = getattr(u_owner, "cellular", "")
        # creador del registro
        creator_id = getattr(obj, "user_getter_id", None) or obj.user_id
        if creator_id:
            creator = db.session.get(UserModel, creator_id)
            if creator:
                form.user_id.data = creator.name
    # Alinear sub_state SelectField con sub_state_id
    if hasattr(form, "sub_state") and hasattr(obj, "sub_state_id"):
        form.sub_state.data = str(obj.sub_state_id) if obj.sub_state_id else ""
    image_urls = {
        "photo": getattr(obj, "photo_url", None),
        "img1": getattr(obj, "squeeze_page_image_1", None),
        "img2": getattr(obj, "squeeze_page_image_2", None),
        "img3": getattr(obj, "squeeze_page_image_3", None),
    }
    return render_template(
        "records/prescriptor_form.html",
        form=form,
        action=url_for("prescriptors.update_prescriptor", prescriptor_id=prescriptor_id),
        contract_url=getattr(obj, "contract_url", None),
        image_urls=image_urls,
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
    form = FormClass(obj=obj)
    # modelo users para sincronizar nombre/email
    UserModel = getattr(Base.classes, "users", None)
    current_app.logger.info(">>> creando prescriptor con data %s", form.data)

    if form.validate_on_submit():
        # precargar y actualizar email/cellular
        obj.state_id = int(form.state_id.data)
        # actualizar campos simples
        # actualizar nombre
        if hasattr(obj, "squeeze_page_name") and hasattr(form, "squeeze_page_name"):
            obj.squeeze_page_name = form.squeeze_page_name.data
            # actualizar nombre de usuario asociado también
            if UserModel and obj.user_id:
                u = db.session.get(UserModel, obj.user_id)
                if u:
                    u.name = form.squeeze_page_name.data

        simple_fields = [
            "squeeze_url_tst",
            "squeeze_url_prd",
            "face_url",
            "linkedin_url",
            "instagram_url",
            "x_url",
        ]
        for fld in simple_fields:
            if hasattr(obj, fld) and hasattr(form, fld):
                setattr(obj, fld, getattr(form, fld).data or None)

        # gestionar uploads de imágenes
        upload_dir = current_app.config.get("PRESCRIPTOR_IMG_FOLDER", os.path.join(current_app.root_path, "static", "prescriptors"))
        os.makedirs(upload_dir, exist_ok=True)
        def _save_file(file_field, suffix):
            if file_field.data:
                filename = secure_filename(f"{obj.id}_{suffix}.{file_field.data.filename.rsplit('.',1)[-1]}")
                path = os.path.join(upload_dir, filename)
                file_field.data.save(path)
                return url_for("static", filename=f"prescriptors/{filename}")
            return None
        mapping = {
            "photo_file":"photo_url",
            "squeeze_page_image_1_file":"squeeze_page_image_1",
            "squeeze_page_image_2_file":"squeeze_page_image_2",
            "squeeze_page_image_3_file":"squeeze_page_image_3",
        }
        for fld_file, model_attr in mapping.items():
            if hasattr(form, fld_file):
                url = _save_file(getattr(form, fld_file), model_attr)
                if url:
                    setattr(obj, model_attr, url)

        # manejar contrato
        if form.contract_file.data:
            filename = f"{obj.id}.pdf"
            path = current_app.config["CONTRACT_UPLOAD_FOLDER"] / filename
            form.contract_file.data.save(path)
            obj.contract_url = url_for("static", filename=f"contracts/{filename}")
        # actualizar usuario asociado
        UserModel = getattr(Base.classes, "users", None)
        if UserModel and obj.user_id:
            u = db.session.get(UserModel, obj.user_id)
            if u:
                u.email = form.email.data
                u.cellular = form.cellular.data
        try:
            db.session.commit()
            flash("Prescriptor actualizado", "success")
        except Exception as e:
            db.session.rollback()
            current_app.logger.exception("Error al actualizar prescriptor: %s", e)
            flash("Error al actualizar prescriptor", "danger")
            return render_template(
                "records/prescriptor_form.html",
                form=form,
                action=url_for("prescriptors.update_prescriptor", prescriptor_id=prescriptor_id),
                contract_url=getattr(obj, "contract_url", None),
            )
        return redirect(url_for("prescriptors.list_prescriptors"))

    current_app.logger.info("Errores de validación: %s", form.errors)
    flash("Errores en el formulario", "danger")
    image_urls = {
        "photo": getattr(obj, "photo_url", None),
        "img1": getattr(obj, "squeeze_page_image_1", None),
        "img2": getattr(obj, "squeeze_page_image_2", None),
        "img3": getattr(obj, "squeeze_page_image_3", None),
    }
    return render_template(
        "records/prescriptor_form.html",
        form=form,
        action=url_for("prescriptors.update_prescriptor", prescriptor_id=prescriptor_id),
        contract_url=getattr(obj, "contract_url", None),
        image_urls=image_urls,
    )
