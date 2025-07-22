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
from sigp.security import require_perm
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

        photo_file = FileField("Foto Squeeze Page", validators=[Optional(), FileAllowed(['jpg','jpeg','png','gif'], 'Imágenes')])
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
        observations = TextAreaField("Detalles de pago", render_kw={"placeholder": "CBU, Alias, Banco, Titular, etc."}, validators=[Optional(), Length(max=1000)])
        extra_observations = TextAreaField("Observaciones", validators=[Optional(), Length(max=1000)])
        billing_data = TextAreaField("Datos de facturación", validators=[Optional(), Length(max=1000)])
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
# Invoice upload
StateLedger = getattr(Base.classes, "state_ledger", None)

_DEF_STATE_IDS = {}

def _state_id(slug: str):
    """Devuelve id del estado con nombre o codigo dado (cache)."""
    if slug in _DEF_STATE_IDS:
        return _DEF_STATE_IDS[slug]
    if StateLedger is None:
        return None
    q = db.session.query(StateLedger.id)
    if hasattr(StateLedger, "code"):
        q = q.filter((StateLedger.name == slug) | (StateLedger.code == slug))
    else:
        q = q.filter(StateLedger.name == slug)
    row = q.first()
    if row:
        _DEF_STATE_IDS[slug] = row.id
        return row.id
    return None

DEFAULT_PEND_FACT_ID = 2  # fallback cuando no se puede acceder a BD
DEFAULT_FACTURADO_ID = 3


Invoice = getattr(Base.classes, "invoice", None)
Ledger = getattr(Base.classes, "ledger", None)


@prescriptors_bp.get("/invoices/new")
@login_required
def new_invoice():
    prescriptor_id = _get_prescriptor_id(current_user)
    if not prescriptor_id:
        flash("No estás asociado a un prescriptor", "warning")
        return redirect("/")
    if Ledger is None:
        flash("Tabla ledger no disponible", "danger")
        return redirect("/")
    pend_id = _state_id("PENDIENTE_FACTURAR") or DEFAULT_PEND_FACT_ID
    rows = (
        db.session.query(Ledger)
        .filter(Ledger.state_id == pend_id, Ledger.prescriptor_id == prescriptor_id)
        .all()
    )
    return render_template("records/upload_invoice.html", rows=rows)


@prescriptors_bp.post("/invoices")
@login_required
def create_invoice():
    prescriptor_id = _get_prescriptor_id(current_user)
    if not prescriptor_id:
        flash("No estás asociado a un prescriptor", "warning")
        return redirect("/")
    if Ledger is None or Invoice is None:
        flash("Modelos no disponibles", "danger")
        return redirect("/")

    number = request.form.get("number", "").strip()
    date_str = request.form.get("invoice_date", "")
    import datetime as _dt
    try:
        invoice_date = _dt.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        flash("Fecha inválida", "warning")
        return redirect(url_for("prescriptors.new_invoice"))

    ledger_ids = request.form.getlist("ledger_ids")
    if not ledger_ids:
        flash("Selecciona movimientos a facturar", "warning")
        return redirect(url_for("prescriptors.new_invoice"))

    file = request.files.get("file")
    if not file or file.filename == "":
        flash("Adjunta el archivo de factura", "warning")
        return redirect(url_for("prescriptors.new_invoice"))

    from sigp.config import Config
    allowed = Config.INVOICE_ALLOWED_EXT
    ext = file.filename.rsplit(".",1)[-1].lower()
    if ext not in allowed:
        flash("Tipo de archivo no permitido", "warning")
        return redirect(url_for("prescriptors.new_invoice"))
    import uuid, os
    fname = f"{uuid.uuid4()}.{ext}"
    save_dir = os.path.join(os.getcwd(), Config.INVOICE_UPLOAD_FOLDER)
    os.makedirs(save_dir, exist_ok=True)
    full_path = os.path.join(save_dir, fname)
    file.save(full_path)

    # Calcular total
    pend_id = _state_id("PENDIENTE_FACTURAR") or DEFAULT_PEND_FACT_ID
    rows = (
        db.session.query(Ledger)
        .filter(Ledger.id.in_(ledger_ids), Ledger.state_id == pend_id, Ledger.prescriptor_id == prescriptor_id)
        .all()
    )
    if not rows:
        flash("Movimientos seleccionados no válidos", "warning")
        return redirect(url_for("prescriptors.new_invoice"))
    total = sum([float(r.amount) for r in rows])

    import uuid as _uuid
    inv = Invoice(
        id=str(_uuid.uuid4()),
        prescriptor_id=prescriptor_id,
        number=number,
        invoice_date=invoice_date,
        total=total,
        file_path=os.path.join(Config.INVOICE_UPLOAD_FOLDER, fname),
        created_at=_dt.datetime.utcnow(),
    )
    db.session.add(inv)
    db.session.flush()

    fact_id = _state_id("FACTURADO") or DEFAULT_FACTURADO_ID
    for r in rows:
        r.state_id = fact_id
        r.invoice_id = inv.id

    db.session.commit()

    # enviar email a administración y usuarios de Finanzas
    try:
        from sigp.common.email_utils import send_simple_mail
        
        # Correos definidos en configuración
        admin_emails = current_app.config.get("ADMIN_EMAILS") or []
        if isinstance(admin_emails, str):
            admin_emails = [e.strip() for e in admin_emails.split(",") if e.strip()]

        # ---- Obtener usuarios con rol Finanzas ----
        Role = getattr(Base.classes, "roles", None)
        User = getattr(Base.classes, "users", None)
        Notification = getattr(Base.classes, "notifications", None)
        # tabla asociación user-role (puede ser roles_users, user_roles, etc.)
        UserRole = None
        for cls in Base.classes.values():
            cols = set(getattr(cls.__table__, "columns").keys())
            if {"user_id", "role_id"}.issubset(cols):
                UserRole = cls
                break
        finance_emails = []
        finance_user_ids = []
        if Role is not None and User is not None:
            # roles cuyo nombre o código contiene 'FINAN'
            role_q = db.session.query(Role.id)
            for col in (getattr(Role, "code", None), getattr(Role, "name", None)):
                if col is not None:
                    role_q = role_q.filter(col.ilike("%FINAN%"))
                    break
            fin_role_ids = [r.id for r in role_q.all()]
            if fin_role_ids:
                if UserRole is not None:
                    uids = [r.user_id for r in db.session.query(UserRole.user_id).filter(UserRole.role_id.in_(fin_role_ids))]
                    finance_user_ids = uids
                elif hasattr(User, "role_id"):
                    uids = [u.id for u in db.session.query(User.id).filter(User.role_id.in_(fin_role_ids))]
                    finance_user_ids = uids
                if finance_user_ids:
                    u_rows = db.session.query(User).filter(User.id.in_(finance_user_ids)).all()
                    finance_emails = [getattr(u, "email", None) for u in u_rows if getattr(u, "email", None)]
        # Combinar correos, eliminar duplicados
        recipients = list({*admin_emails, *finance_emails})

        subj = f"Nueva factura #{number} subida por prescriptor {prescriptor_id}"
        if recipients:
            html_body = render_template('emails/new_invoice_uploaded.html',
                                        number=number,
                                        date=invoice_date,
                                        total=total,
                                        rows_count=len(rows),
                                        base_url=current_app.config.get('BASE_URL') or request.host_url.rstrip('/') )
            text_body = (
                f"Nueva factura subida.\n\n"
                f"Número: {number}\nFecha: {invoice_date}\nTotal: {total:.2f} €\nMovimientos: {len(rows)}\n\n"
                f"Revisar: {current_app.config.get('BASE_URL') or request.host_url.rstrip('/')}/settlements/"
            )
            send_simple_mail(recipients, subj, html_body, html=True, text_body=text_body)

        # ---- Notificaciones in-app ----
        if Notification is not None and finance_user_ids:
            from datetime import datetime as _dt
            for uid in finance_user_ids:
                notif = Notification(
                    user_id=uid,
                    title="Nueva factura subida",
                    message=f"El prescriptor {prescriptor_id} subió la factura #{number} por {total:.2f} €.",
                    created_at=_dt.utcnow(),
                )
                db.session.add(notif)
            db.session.commit()
    except Exception as exc:  # pylint: disable=broad-except
        current_app.logger.error("Error enviando mail/notification de factura: %s", exc)

    flash("Factura subida correctamente", "success")
    return redirect(url_for("prescriptors.new_invoice"))


def _get_prescriptor_id(user):
    pid = getattr(user, "prescriptor_id", None)
    if pid:
        return pid
    PresModel = getattr(Base.classes, "prescriptors", None)
    if PresModel and getattr(user, "id", None):
        row = db.session.query(PresModel.id).filter(PresModel.user_id == user.id).first()
        if row:
            return row.id
    return None

# Historial de un lead propio
@prescriptors_bp.get("/leads/<lead_id>/history")
@login_required
def my_lead_history(lead_id):
    Lead = getattr(Base.classes, "leads", None)
    LeadHistory = getattr(Base.classes, "lead_history", None)
    if not (Lead and LeadHistory):
        abort(404)
    lead = db.session.get(Lead, lead_id)
    if not lead or lead.prescriptor_id != _get_prescriptor_id(current_user):
        abort(403)
    history = db.session.query(LeadHistory).filter(LeadHistory.lead_id==lead_id).order_by(LeadHistory.changed_at.desc()).all()
    StateLead = getattr(Base.classes, "state_lead", None)
    state_map = {}
    if StateLead is not None:
        srows = db.session.query(StateLead.id, StateLead.name).all()
        state_map = {s.id: s.name for s in srows}
    return render_template("list/lead_history.html", history=history, state_map=state_map, user_map={})

# Libro mayor del prescriptor
@prescriptors_bp.get("/ledger")
@login_required
def my_ledger():
    # permisos extendidos (admin/finanzas) → puede elegir prescriptor
    from sigp.common.security import has_perm
    can_all = has_perm(current_user, "manage_payments") or has_perm(current_user, "manage_leads")

    # prescriptor elegido
    presc_id_param = request.args.get("prescriptor")
    prescriptor_id = _get_prescriptor_id(current_user)
    if can_all and presc_id_param:
        prescriptor_id = presc_id_param

    if not prescriptor_id and not can_all:
        flash("No estás asociado a un prescriptor", "warning")
        return redirect("/")

    if Ledger is None:
        flash("Tabla ledger no disponible", "danger")
        return redirect("/")
    StateLedger = getattr(Base.classes, "state_ledger", None)
    state_f = request.args.get("state", "")
    query = (
        db.session.query(
            Ledger.id,
            Ledger.concept,
            Ledger.amount,
            Ledger.created_at,
            Ledger.state_id,
            StateLedger.name.label("state_name"),
        )
        .join(StateLedger, StateLedger.id == Ledger.state_id)
        .filter(Ledger.prescriptor_id == prescriptor_id)
        .order_by(Ledger.created_at.desc())
    )
    if state_f:
        query = query.filter(Ledger.state_id == state_f)
    rows = query.all() if prescriptor_id else []
    states = db.session.query(StateLedger.id, StateLedger.name).all()

    # lista de prescriptores para selector si admin
    presc_choices = []
    if can_all:
        PresModel = getattr(Base.classes, "prescriptors", None)
        if PresModel:
            presc_choices = (
                db.session.query(PresModel.id, PresModel.squeeze_page_name).order_by(PresModel.squeeze_page_name).all()
            )
    return render_template(
        "list/my_ledger.html",
        rows=rows,
        states=states,
        state_f=state_f,
        presc_choices=presc_choices,
        prescriptor_id=prescriptor_id,
        can_select=can_all,
    )

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
            Model.sub_state_id.label("sub_state_id"),
            Model.confidence_level_id.label("confidence_level_id"),
            Model.squeeze_page_status.label("squeeze_page_status"),
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

    # Build label maps
    substate_choices = _get_select_choices("substate_prescriptor")
    conf_choices = _get_select_choices("confidence_level")
    sub_map = {int(val): lbl for val, lbl in substate_choices if val}
    conf_map = {int(val): lbl for val, lbl in conf_choices if val}

    # Build list of simple dicts/namespaces for template (avoid mutating Row objects)
    from types import SimpleNamespace
    display_items = []
    for row in items:
        mapping = row._mapping if hasattr(row, '_mapping') else row.__dict__
        sid_raw = mapping.get('sub_state_id') if isinstance(mapping, dict) else getattr(row, 'sub_state_id', None)
        cid_raw = mapping.get('confidence_level_id') if isinstance(mapping, dict) else getattr(row, 'confidence_level_id', None)
        try:
            sid = int(sid_raw) if sid_raw is not None else None
        except (ValueError, TypeError):
            sid = None
        try:
            cid = int(cid_raw) if cid_raw is not None else None
        except (ValueError, TypeError):
            cid = None
        data = dict(mapping)
        data['sub_state_name'] = sub_map.get(sid, '')
        data['confidence_name'] = conf_map.get(cid, '')
        # Squeeze page status directo
        data['squeeze_page_status'] = mapping.get('squeeze_page_status', getattr(row, 'squeeze_page_status', ''))
        display_items.append(SimpleNamespace(**data))

    # Para selects del filtro
    type_choices = _get_select_choices("prescriptor_types")
    state_choices = _get_select_choices("state_prescriptor")


    return render_template(
        "list/prescriptors.html",
        items=display_items,
        page=page,
        per_page=per_page,
        filters={"nombre": nombre_f, "tipo": tipo_f, "estado": estado_f},
        type_choices=type_choices,
        state_choices=state_choices,
        sub_map=sub_map,
        conf_map=conf_map,
        total=total,
    )


@prescriptors_bp.get("/new")
@login_required
def new_prescriptor():
    FormClass = prescriptor_form_factory(is_create=True)
    form = FormClass()
    current_app.logger.info(">>> creando prescriptor con data %s", form.data)
    form.user_id.data = current_user.name
    # valores por defecto para datos de facturación
    default_billing = (
        "Concepto: Tutorización\n"
        "INNOVA TRAINING CYF S.L\n"
        "CUIT País: 51600004100 (España - Otro tipo de Entidad)\n"
        "ID Impositivo B19456128\n"
        "Domicilio: C/Campo de Gomara Bajo 4 47008 Valladolid"
    )
    if hasattr(form, "billing_data"):
        form.billing_data.data = default_billing
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
        for fld in ["face_url", "linkedin_url", "instagram_url", "x_url"]:
            if hasattr(form, fld) and hasattr(Model, fld):
                obj_kwargs[fld] = getattr(form, fld).data or None
        if hasattr(form, "squeeze_page_status"):
            obj_kwargs["squeeze_page_status"] = form.squeeze_page_status.data or "TEST"
        if hasattr(form, "observations") and form.observations.data:
             obj_kwargs["payment_details"] = form.observations.data
        if hasattr(form, "extra_observations") and form.extra_observations.data:
             obj_kwargs["observations"] = form.extra_observations.data
        if hasattr(form, "billing_data") and form.billing_data.data:
             obj_kwargs["billing_data"] = form.billing_data.data
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
            # sincronizar comisiones iniciales
            try:
                from sigp.common.prescriptor_utils import sync_commissions_for_prescriptor
                sync_commissions_for_prescriptor(new_obj.id)
            except Exception as exc:
                current_app.logger.exception("Error sincronizando comisiones: %s", exc)
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
        # usuario asociado (captador). Solo precargar si existe, no usar creador como fallback
        if obj.user_id:
            u_owner = db.session.get(UserModel, obj.user_id)
            if u_owner:
                form.email.data = u_owner.email
                form.cellular.data = getattr(u_owner, "cellular", "")
        # precargar detalles de pago
        if hasattr(obj, "payment_details") and hasattr(form, "observations"):
            form.observations.data = getattr(obj, "payment_details", "")
        # precargar observaciones
        if hasattr(obj, "observations") and hasattr(form, "extra_observations"):
            form.extra_observations.data = getattr(obj, "observations", "")
        # precargar datos de facturación
        if hasattr(obj, "billing_data") and hasattr(form, "billing_data"):
            form.billing_data.data = getattr(obj, "billing_data", "")
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
        edit=True,
        obj=obj,
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
        # detalles de pago
        if hasattr(obj, "payment_details") and hasattr(form, "observations"):
            obj.payment_details = form.observations.data or None
        # observaciones
        if hasattr(obj, "observations") and hasattr(form, "extra_observations"):
            obj.observations = form.extra_observations.data or None
        # datos de facturación
        if hasattr(obj, "billing_data") and hasattr(form, "billing_data"):
            obj.billing_data = form.billing_data.data or None

        # gestionar uploads de imágenes
        upload_dir = current_app.config.get("PRESCRIPTOR_IMG_FOLDER", os.path.join(current_app.root_path, "static", "prescriptors"))
        os.makedirs(upload_dir, exist_ok=True)
        def _save_file(file_field, suffix):
            if file_field and getattr(file_field, 'data', None):
                filename = secure_filename(f"{obj.id}_{suffix}.{file_field.data.filename.rsplit('.',1)[-1]}")
                path = os.path.join(upload_dir, filename)
                file_field.data.save(path)
                return url_for("static", filename=f"prescriptors/{filename}")
            return None

        mapping = {
            "photo_file": "photo_url",
            "squeeze_page_image_1_file": "squeeze_page_image_1",
            "squeeze_page_image_2_file": "squeeze_page_image_2",
            "squeeze_page_image_3_file": "squeeze_page_image_3",
        }
        for fld_file, model_attr in mapping.items():
            if hasattr(form, fld_file):
                saved_url = _save_file(getattr(form, fld_file), model_attr)
                if saved_url:
                    setattr(obj, model_attr, saved_url)

        # manejar contrato
        if form.contract_file.data:
            filename = f"{obj.id}.pdf"
            path = current_app.config["CONTRACT_UPLOAD_FOLDER"] / filename
            form.contract_file.data.save(path)
            obj.contract_url = url_for("static", filename=f"contracts/{filename}")

        # actualizar usuario asociado
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
        edit=True,
        obj=obj,
    )


@prescriptors_bp.route("/my-commissions", methods=["GET"])
@login_required
def my_commissions():
    PrescComm = getattr(Base.classes, "prescriptor_commission", None)
    Program = getattr(Base.classes, "programs", None)
    Model = _get_model()
    if not (PrescComm and Program and Model):
        abort(404)
    presc = db.session.query(Model).filter_by(user_id=current_user.id).first()
    if not presc:
        flash("No eres prescriptor", "warning")
        return redirect(url_for("dashboard.index"))
    rows = db.session.query(PrescComm).filter_by(prescriptor_id=presc.id).all()
    if not rows:
        from sigp.common.prescriptor_utils import sync_commissions_for_prescriptor
        sync_commissions_for_prescriptor(presc.id)
        rows = db.session.query(PrescComm).filter_by(prescriptor_id=presc.id).all()

    # mapas auxiliares
    prog_rows = db.session.query(Program.id, Program.name).all()
    prog_map = {pid: name for pid, name in prog_rows}

    return render_template(
        "records/my_commissions.html",
        rows=rows,
        prog_map=prog_map,
    )


@prescriptors_bp.route("/<prescriptor_id>/commissions", methods=["GET", "POST"])
@login_required
@require_perm("update_prescriptor_commission")
def prescriptor_commissions(prescriptor_id):
    PrescComm = getattr(Base.classes, "prescriptor_commission", None)
    Program = getattr(Base.classes, "programs", None)
    Model = _get_model()
    if not (PrescComm and Program and Model):
        flash("Modelos no disponibles", "danger")
        return redirect(url_for("prescriptors.list_prescriptors"))
    presc = db.session.get(Model, prescriptor_id)
    if not presc:
        flash("Prescriptor no encontrado", "warning")
        return redirect(url_for("prescriptors.list_prescriptors"))

    if request.method == "POST":
        rows = db.session.query(PrescComm).filter_by(prescriptor_id=prescriptor_id).all()
        for r in rows:
            r.commission_value = request.form.get(f"comm_{r.id}", type=float) or 0
            r.first_installment_pct = request.form.get(f"first_{r.id}", type=float) or 0
            r.registration_value = request.form.get(f"reg_{r.id}", type=float) or 0
            r.value_quotas = request.form.get(f"quot_{r.id}", type=float) or 0
        db.session.commit()
        flash("Comisiones guardadas", "success")
        return redirect(url_for("prescriptors.list_prescriptors"))

    rows = db.session.query(PrescComm).filter_by(prescriptor_id=prescriptor_id).all()
    if not rows:
        from sigp.common.prescriptor_utils import sync_commissions_for_prescriptor
        sync_commissions_for_prescriptor(prescriptor_id)
        rows = db.session.query(PrescComm).filter_by(prescriptor_id=prescriptor_id).all()
    Campus = getattr(Base.classes, "campus", None)
    prog_rows = db.session.query(Program.id, Program.name, Program.campus_id).all()
    prog_map = {pid: name for pid, name, _ in prog_rows}
    prog_campus = {pid: camp_id for pid, _, camp_id in prog_rows}
    campus_map = {}
    if Campus is not None:
        campus_rows = db.session.query(Campus.id, Campus.name).all()
        campus_map = {cid: cname for cid, cname in campus_rows}
    return render_template(
        "records/prescriptor_commissions.html",
        rows=rows,
        presc=presc,
        prog_map=prog_map,
        prog_campus=prog_campus,
        campus_map=campus_map,
    )
