"""Leads management blueprint: simple listing of leads."""
from __future__ import annotations

from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
import uuid
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Length, Email, Optional
from flask_login import login_required

from sigp import db
from sigp.models import Base
from flask_login import current_user
from sigp.security import require_perm

leads_bp = Blueprint("leads", __name__, url_prefix="/leads")

# Reflected tables
Lead = getattr(Base.classes, "leads", None)
StateLead = getattr(Base.classes, "state_lead", None)
Program = getattr(Base.classes, "programs", None)
Edition = getattr(Base.classes, "editions", None)

# Estados clave
MATRICULADO_ID = 3
COMPLETADO_ID = 7


# Helper to get display label for a prescriptor

def _presc_label(p):
    """Etiqueta para desplegable: siempre el campo squeeze_page_name si existe."""
    if p is None:
        return ""
    val = getattr(p, "squeeze_page_name", None)
    if val:
        return val
    return getattr(p, "name", getattr(p, "nombre", str(p.id)))

class LeadStatusForm(FlaskForm):
    state_id = SelectField("Nuevo estado", coerce=int, validators=[DataRequired()])
    observations = TextAreaField("Observaciones", validators=[Length(max=500)])
    program_id = SelectField("Programa matriculado", coerce=str, validators=[Optional()])
    edition_id = SelectField("Edición", coerce=int, validators=[Optional()])
    installments = StringField("Cuotas", validators=[Optional(), Length(max=20)])
    start_month = SelectField("Mes inicio", choices=[("03", "Marzo"), ("10", "Octubre")], validators=[Optional()])
    start_year = IntegerField("Año inicio", validators=[Optional()])
    submit = SubmitField("Guardar")


class LeadForm(FlaskForm):
    prescriptor_id = SelectField("Prescriptor", coerce=str, validators=[DataRequired()])
    candidate_name = StringField("Nombre", validators=[DataRequired(), Length(max=100)])
    candidate_email = StringField("Email", validators=[Optional(), Email(), Length(max=255)])
    candidate_cellular = StringField("Celular", validators=[Optional(), Length(max=255)])
    program_info_id = SelectField("Programa", coerce=str, validators=[Optional()])
    state_id = SelectField("Estado", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Guardar")
Prescriptor = getattr(Base.classes, "prescriptors", None)
User = getattr(Base.classes, "users", None)


@leads_bp.route("/")
@login_required
@require_perm("read_leads")
def leads_list():
    """Paginated list of leads."""
    if Lead is None:
        flash("Tabla leads no disponible", "danger")
        return render_template("list/leads_list.html", leads=[], total=0, page=1, per_page=1)

    page = request.args.get("page", 1, type=int)
    per_page = 25

    # Filtros
    cand_q = request.args.get("candidate", "").strip()
    presc_q = request.args.get("prescriptor", "")  # id
    state_q = request.args.get("state", "")  # id

    q = db.session.query(Lead)
    if cand_q:
        q = q.filter(Lead.candidate_name.ilike(f"%{cand_q}%"))
    if presc_q:
        q = q.filter(Lead.prescriptor_id == presc_q)
    if state_q:
        q = q.filter(Lead.state_id == int(state_q))

    q = q.order_by(Lead.created_at.desc())
    total = q.count()
    leads = q.offset((page - 1) * per_page).limit(per_page).all()

    pres_map = {}
    if Prescriptor is not None and leads:
        pres_ids = {l.prescriptor_id for l in leads}
        pres_rows = db.session.query(Prescriptor).filter(Prescriptor.id.in_(pres_ids)).all()
        pres_map = {p.id: _presc_label(p) for p in pres_rows}

    # Mapear id -> nombre de estado
    state_map = {}
    if StateLead is not None and leads:
        sids = {l.state_id for l in leads}
        state_rows = db.session.query(StateLead).filter(StateLead.id.in_(sids)).all()
        state_map = {s.id: s.name for s in state_rows}

    # Choices para filtros
    presc_choices = []
    if Prescriptor is not None:
        presc_rows = db.session.query(Prescriptor).order_by(Prescriptor.squeeze_page_name).all()
        presc_choices = [(p.id, _presc_label(p)) for p in presc_rows]
    state_choices = []
    if StateLead is not None:
        state_rows_all = db.session.query(StateLead).order_by(StateLead.name).all()
        state_choices = [(s.id, s.name) for s in state_rows_all]

    return render_template(
        "list/leads_list.html",
        leads=leads,
        pres_map=pres_map,
        state_map=state_map,
        presc_choices=presc_choices,
        state_choices=state_choices,
        filters={"candidate": cand_q, "prescriptor": presc_q, "state": state_q},
        total=total,
        page=page,
        per_page=per_page,
    )




@leads_bp.get("/my")
@login_required
def my_leads():
    """Listado paginado de leads solo del prescriptor logueado."""
    if Lead is None:
        flash("Tabla leads no disponible", "danger")
        return redirect(url_for("dashboard.dashboard_home"))

    # Identificar prescriptor del usuario
    my_presc_id = None
    if Prescriptor is not None and current_user.is_authenticated:
        presc = db.session.query(Prescriptor).filter(Prescriptor.user_id == current_user.id).first()
        if presc:
            my_presc_id = presc.id
    if not my_presc_id:
        flash("No se encontró un prescriptor asociado a tu usuario", "warning")
        return redirect(url_for("dashboard.dashboard_home"))

    # Filtros
    cand_q = request.args.get("candidate", "").strip()
    state_q = request.args.get("state", "")
    from_q = request.args.get("from", "")
    to_q = request.args.get("to", "")

    page = request.args.get("page", 1, type=int)
    per_page = 25

    q = db.session.query(Lead).filter(Lead.prescriptor_id == my_presc_id)
    if cand_q:
        q = q.filter(Lead.candidate_name.ilike(f"%{cand_q}%"))
    if state_q:
        q = q.filter(Lead.state_id == int(state_q))
    if from_q:
        q = q.filter(Lead.created_at >= from_q)
    if to_q:
        q = q.filter(Lead.created_at <= to_q + " 23:59:59")

    q = q.order_by(Lead.created_at.desc())
    total = q.count()
    leads = q.offset((page - 1) * per_page).limit(per_page).all()

    # State map
    state_map = {}
    state_choices = []
    if StateLead is not None:
        srows = db.session.query(StateLead).all()
        state_map = {s.id: s.name for s in srows}
        state_choices = [(s.id, s.name) for s in srows]

    # Program map
    program_map = {}
    if Program is not None and leads:
        pids = {l.program_info_id for l in leads if l.program_info_id}
        prow = db.session.query(Program).filter(Program.id.in_(pids)).all()
        program_map = {p.id: getattr(p, "name", getattr(p, "nombre", p.id)) for p in prow}

    return render_template(
        "list/my_leads.html",
        leads=leads,
        state_map=state_map,
        state_choices=state_choices,
        program_map=program_map,
        filters={"candidate": cand_q, "state": state_q, "from": from_q, "to": to_q},
        total=total,
        page=page,
        per_page=per_page,
    )


@leads_bp.route("/new", methods=["GET", "POST"])
@login_required
@require_perm("create_leads")
def new_lead():
    if Lead is None:
        flash("Tabla leads no disponible", "danger")
        return redirect(url_for("leads.leads_list"))

    form = LeadForm()
    # prescriptor choices (users con rol PRESCRIPTOR)
    presc_choices = []
    if Prescriptor is not None:
        presc_rows = db.session.query(Prescriptor).all()
        presc_choices = [
            (p.id, _presc_label(p)) for p in presc_rows
        ]

    # if current user is prescriptor restrict
        # Si el usuario logueado es prescriptor, filtrar su propio prescriptor (por email)
    if current_user.is_authenticated and Prescriptor is not None:
        my_presc = db.session.query(Prescriptor).filter(getattr(Prescriptor, 'email', None) == current_user.email).first()
        if my_presc:
            presc_choices = [(my_presc.id, _presc_label(my_presc))]
            form.prescriptor_id.data = my_presc.id
    form.prescriptor_id.choices = presc_choices
    # Program choices
    if Program is not None:
        prog_rows = db.session.query(Program).all()
        form.program_info_id.choices = [(p.id, getattr(p, 'name', getattr(p, 'nombre', str(p.id)))) for p in prog_rows]
    else:
        form.program_info_id.choices = []

    if StateLead:
        form.state_id.choices = [(s.id, s.name) for s in db.session.query(StateLead).order_by(StateLead.id)]

    if form.validate_on_submit():
        lead_id = str(uuid.uuid4())
        lead = Lead(
            id=lead_id,
            prescriptor_id=form.prescriptor_id.data,
            program_info_id=form.program_info_id.data or None,
            state_id=form.state_id.data,
            candidate_name=form.candidate_name.data,
            candidate_email=form.candidate_email.data,
            candidate_cellular=form.candidate_cellular.data,
        )
        db.session.add(lead)
        db.session.commit()
        # registrar movimiento inicial en historial
        from sigp.common.lead_utils import log_lead_change
        log_lead_change(lead.id, lead.state_id, "Alta de lead")
        db.session.commit()

        # enviar notificación a comerciales si el programa tiene emails configurados
        if Program is not None and form.program_info_id.data:
            program = db.session.get(Program, form.program_info_id.data)
            if program and getattr(program, "commercial_emails", None):
                from sigp.common.email_utils import send_simple_mail
                emails = [e.strip() for e in program.commercial_emails.split(',') if e.strip()]
                if emails:
                    subject = f"Nuevo lead para programa {getattr(program, 'name', program.id)}"
                    body = (
                        "Se ha generado un nuevo lead desde la gestión interna.\n\n"
                        f"Prescriptor ID: {form.prescriptor_id.data}\n"
                        f"Programa: {getattr(program, 'name', program.id)}\n"
                        f"Nombre candidato: {form.candidate_name.data}\n"
                        f"Email: {form.candidate_email.data or '-'}\n"
                        f"Celular: {form.candidate_cellular.data or '-'}\n"
                    )
                    try:
                        send_simple_mail(emails, subject, body)
                    except Exception as exc:
                        current_app.logger.exception("Error enviando mail a comerciales: %s", exc)
                        flash("Lead creado pero no se pudo enviar correo a comerciales", "warning")

                    # generar notificaciones internas para usuarios con mismo email
                    Notification = getattr(Base.classes, "notifications", None)
                    User = getattr(Base.classes, "users", None)
                    if Notification is not None and User is not None:
                        user_rows = db.session.query(User).filter(User.email.in_(emails)).all()
                        if user_rows:
                            import datetime, uuid as _uuid
                            notif_objects = []
                            for u in user_rows:
                                notif_objects.append(Notification(
                                    id=str(_uuid.uuid4()),
                                    user_id=u.id,
                                    title=subject,
                                    body=body,
                                    notif_type="INFO",
                                    is_read=0,
                                    created_at=datetime.datetime.utcnow(),
                                ))
                            db.session.bulk_save_objects(notif_objects)
                            db.session.commit()

        flash("Lead creado", "success")
        return redirect(url_for("leads.leads_list"))

    # initial GET or validation errors
    return render_template("records/lead_form.html", form=form, action=url_for("leads.new_lead"), edit=False)


@leads_bp.post("/<lead_id>/delete")
@login_required
@require_perm("delete_leads")
def delete_lead(lead_id):
    """Eliminar leads cuyo estado sea 6."""

# ---------------------------------------------------------------------------
# Historial
# ---------------------------------------------------------------------------

@leads_bp.get("/<lead_id>/history")
@login_required
@require_perm("view_leads")
def lead_history(lead_id):
    LeadHistory = getattr(Base.classes, "lead_history", None)
    if LeadHistory is None:
        flash("Tabla lead_history no disponible", "danger")
        return redirect(url_for("leads.leads_list"))

    history = db.session.query(LeadHistory).filter(LeadHistory.lead_id == lead_id).order_by(LeadHistory.changed_at.desc()).all()

    # maps
    state_map = {}
    if StateLead is not None:
        srows = db.session.query(StateLead.id, StateLead.name).all()
        state_map = {s.id: s.name for s in srows}
    user_map = {}
    User = getattr(Base.classes, "users", None)
    if User is not None:
        urows = db.session.query(User.id, User.email).all()
        user_map = {u.id: u.email for u in urows}

    return render_template("list/lead_history.html", history=history, state_map=state_map, user_map=user_map)

# ---------------------------------------------------------------------------
# Actualizar estado
# ---------------------------------------------------------------------------

@leads_bp.route("/<lead_id>/status", methods=["GET", "POST"])
@login_required
@require_perm("update_leads")
def update_status(lead_id):
    if Lead is None:
        flash("Tabla leads no disponible", "danger")
        return redirect(url_for("leads.leads_list"))
    lead = db.session.get(Lead, lead_id)
    if not lead:
        flash("Lead no encontrado", "warning")
        return redirect(url_for("leads.leads_list"))
    # no permitir cambios si ya esta completado
    if lead.state_id == COMPLETADO_ID:
        flash("Lead completado: no se puede modificar", "warning")
        return redirect(url_for("leads.leads_list"))

    form = LeadStatusForm()
    # cargar choices estados
    if StateLead is not None:
        states = db.session.query(StateLead).order_by(StateLead.name).all()
        form.state_id.choices = [(s.id, s.name) for s in states]
    # cargar programas
    if Program is not None:
        prows = db.session.query(Program).order_by(Program.name).all()
        form.program_id.choices = [(p.id, getattr(p, "name", getattr(p, "nombre", p.id))) for p in prows]
    else:
        form.program_id.choices = []
    # Ediciones
    if Edition is not None:
        erows = db.session.query(Edition).order_by(Edition.name).all()
        form.edition_id.choices = [(e.id, e.name) for e in erows]
    else:
        form.edition_id.choices = []

    # inicial GET
    if request.method == "GET":
        form.state_id.data = lead.state_id
        form.observations.data = getattr(lead, "observations", "")
        form.program_id.data = lead.program_id if hasattr(lead, 'program_id') else lead.program_info_id
        form.installments.data = getattr(lead, "payment_fees", "")
        form.start_month.data = getattr(lead, "start_month", None)
        form.start_year.data = getattr(lead, "start_year", None)
        # Defaults if empty
        if not form.start_month.data or not form.start_year.data:
            from datetime import date
            today = date.today()
            if today.month < 3:
                form.start_month.data, form.start_year.data = "03", today.year
            elif today.month < 10:
                form.start_month.data, form.start_year.data = "10", today.year
            else:
                form.start_month.data, form.start_year.data = "03", today.year + 1

    if form.validate_on_submit():
        new_state = form.state_id.data
        obs = form.observations.data or ""
        if new_state == MATRICULADO_ID:
            if not form.installments.data or not form.installments.data.strip():
                flash("Debes indicar las cuotas del plan de pago", "warning")
                return render_template("records/lead_status_form.html", form=form, matriculado_id=MATRICULADO_ID)
            lead.program_id = form.program_id.data
            lead.edition_id = form.edition_id.data
            lead.payment_fees = form.installments.data
            lead.start_month = form.start_month.data
            lead.start_year = form.start_year.data
            # Obtener nombres legibles
            prog_name = str(lead.program_id)
            if Program is not None and lead.program_id:
                pr = db.session.get(Program, lead.program_id)
                if pr:
                    prog_name = getattr(pr, 'name', prog_name)
            ed_name = str(lead.edition_id) if lead.edition_id else "-"
            if Edition is not None and lead.edition_id:
                ed = db.session.get(Edition, lead.edition_id)
                if ed:
                    ed_name = getattr(ed, 'name', ed_name)
            obs = f"Matriculado en programa {prog_name} edición {ed_name} cuotas {lead.payment_fees or '-'} inicio {lead.start_month}/{lead.start_year}"
        else:
            lead.observations = obs
        lead.state_id = new_state
        # asignar comercial: sólo la primera vez que pasa a Matriculado
        if new_state == MATRICULADO_ID and not getattr(lead, 'commercial_id', None):
            try:
                lead.commercial_id = current_user.id
            except Exception:
                pass
        try:
            db.session.commit()
            from sigp.common.lead_utils import log_lead_change
            log_lead_change(lead.id, lead.state_id, obs)
            db.session.commit()
            flash("Estado actualizado", "success")
            # enviar mail y notificación al prescriptor
            Prescriptor = getattr(Base.classes, 'prescriptors', None)
            Notification = getattr(Base.classes, 'notifications', None)
            UserModel = getattr(Base.classes, 'users', None)
            if Prescriptor is not None:
                presc = db.session.get(Prescriptor, lead.prescriptor_id)
                presc_email = None
                if presc:
                    if getattr(presc, 'user_id', None) and UserModel is not None:
                        usr = db.session.get(UserModel, presc.user_id)
                        if usr:
                            presc_email = usr.email
                    presc_email = presc_email or getattr(presc, 'email', None)
                if presc_email:
                    # obtener nombre del estado
                    state_name = str(new_state)
                    if StateLead is not None:
                        st = db.session.get(StateLead, new_state)
                        if st:
                            state_name = getattr(st, 'name', state_name)
                    subject = f"Tu lead ha cambiado de estado a {state_name}"
                    body = f"El lead {lead.candidate_name or lead.id} ahora está en estado {state_name}. Observaciones: {obs}"
                    try:
                        from sigp.common.email_utils import send_simple_mail
                        send_simple_mail([presc_email], subject, body)
                    except Exception as exc:
                        current_app.logger.exception('Error enviando mail a prescriptor: %s', exc)
                    # notificación interna
                    if Notification is not None and UserModel is not None and usr:
                        import datetime, uuid as _uuid
                        notif = Notification(
                            id=str(_uuid.uuid4()),
                            user_id=usr.id,
                            title=subject,
                            body=body,
                            notif_type='INFO',
                            is_read=0,
                            created_at=datetime.datetime.utcnow(),
                        )
                        db.session.add(notif)
                        db.session.commit()
        except Exception as exc:
            db.session.rollback()
            current_app.logger.exception("Error actualizando estado lead: %s", exc)
            flash("Error actualizando estado", "danger")
        return redirect(url_for("leads.leads_list"))

    return render_template("records/lead_status_form.html", form=form, lead=lead, matriculado_id=MATRICULADO_ID)
    """Eliminar leads cuyo estado sea 6."""
    if Lead is None:
        flash("Tabla leads no disponible", "danger")
        return redirect(url_for("leads.leads_list"))
    lead = db.session.get(Lead, lead_id)
    if not lead:
        flash("Lead no encontrado", "warning")
    else:
        if lead.state_id == 6:
            db.session.delete(lead)
            db.session.commit()
            flash("Lead eliminado", "info")
        else:
            flash("Solo se pueden eliminar leads con estado 6", "danger")
    return redirect(url_for("leads.leads_list"))


@leads_bp.route("/<lead_id>/edit", methods=["GET", "POST"])
@login_required
@require_perm("update_leads")
def edit_lead(lead_id):
    lead = db.session.get(Lead, lead_id)
    if not lead:
        flash("Lead no encontrado", "warning")
        return redirect(url_for("leads.leads_list"))

    form = LeadForm(obj=lead)

    # --- Same choice population as in new_lead ---
    presc_choices = []
    if Prescriptor is not None:
        presc_rows = db.session.query(Prescriptor).all()
        presc_choices = [
            (p.id, _presc_label(p)) for p in presc_rows
        ]
    form.prescriptor_id.choices = presc_choices
    # Program choices
    if Program is not None:
        prog_rows = db.session.query(Program).all()
        form.program_info_id.choices = [(p.id, getattr(p, 'name', getattr(p, 'nombre', str(p.id)))) for p in prog_rows]
    else:
        form.program_info_id.choices = []

    if StateLead:
        form.state_id.choices = [(s.id, s.name) for s in db.session.query(StateLead).order_by(StateLead.id)]

    # Disable state field in form rendering
    form.state_id.render_kw = {"disabled": True}

    if form.validate_on_submit():
        lead.prescriptor_id = form.prescriptor_id.data
        lead.candidate_name = form.candidate_name.data
        lead.candidate_email = form.candidate_email.data
        lead.program_info_id = form.program_info_id.data or None
        lead.candidate_cellular = form.candidate_cellular.data
        db.session.commit()
        flash("Lead actualizado", "success")
        return redirect(url_for("leads.leads_list"))

    return render_template("records/lead_form.html", form=form, action=url_for("leads.edit_lead", lead_id=lead_id), edit=True)
