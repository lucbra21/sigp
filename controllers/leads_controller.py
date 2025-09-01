"""Leads management blueprint: simple listing of leads."""
from __future__ import annotations

from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, abort, make_response
import uuid
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, TextAreaField, IntegerField
from flask_wtf.file import FileField, FileAllowed
from werkzeug.utils import secure_filename
import os
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
    receipt = FileField("Comprobante pago", validators=[Optional(), FileAllowed(["jpg", "jpeg", "png", "pdf", "gif"], "Formatos permitidos: jpg, png, pdf, gif")])
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

    # Mapear comercial (usuario) id -> nombre completo
    commercial_map = {}
    if User is not None and leads:
        com_ids = {l.commercial_id for l in leads if l.commercial_id}
        if com_ids:
            user_rows = db.session.query(User).filter(User.id.in_(com_ids)).all()
            for u in user_rows:
                nombre = f"{getattr(u,'name','')} {getattr(u,'lastname','')}".strip() or getattr(u,'email',u.id)
                commercial_map[u.id] = nombre

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
        commercial_map=commercial_map,
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
                    subject = f"Nuevo lead para programa {getattr(program,'name',program.id)}"
                    plain_body=(
                        "Se ha generado un nuevo lead desde la gestión interna.\n\n"
                        f"Prescriptor ID: {form.prescriptor_id.data}\n"
                        f"Programa: {getattr(program,'name', program.id)}\n"
                        f"Nombre candidato: {form.candidate_name.data}\n"
                        f"Email: {form.candidate_email.data or '-'}\n"
                        f"Celular: {form.candidate_cellular.data or '-'}\n"
                        f"Observaciones: {form.observations.data or '-'}\n"
                    )
                    html_body = render_template('emails/new_lead.html',
                        origin='Gestión interna',
                        prescriptor=form.prescriptor_id.data,
                        program=getattr(program,'name', program.id),
                        candidate_name=form.candidate_name.data,
                        candidate_email=form.candidate_email.data,
                        candidate_cellular=form.candidate_cellular.data,
                        observations=form.observations.data)
                    
                    try:
                        send_simple_mail(emails, subject, html_body, html=True, text_body=plain_body)
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
    """Eliminar un lead solo si su estado es 6 (cerrado) para evitar borrar leads activos."""
    Lead = getattr(Base.classes, "leads", None)
    LeadHistory = getattr(Base.classes, "lead_history", None)
    Ledger = getattr(Base.classes, "ledger", None)
    if Lead is None:
        abort(404)

    lead = db.session.get(Lead, lead_id)
    if lead is None:
        flash("Lead no encontrado", "warning")
        return redirect(url_for("leads.leads_list"))

    # Solo permitir eliminar si state_id == 6
    if getattr(lead, "state_id", None) != 6:
        flash("Solo se pueden eliminar leads con estado 6", "warning")
        return redirect(url_for("leads.leads_list"))

    try:
        # Borrar ledger asociado
        if Ledger is not None:
            db.session.query(Ledger).filter(Ledger.lead_id == lead_id).delete()
        # Borrar historial
        if LeadHistory is not None:
            db.session.query(LeadHistory).filter(LeadHistory.lead_id == lead_id).delete()
        # Borrar lead
        db.session.delete(lead)
        db.session.commit()
        flash("Lead eliminado", "success")
    except Exception as exc:  # pylint: disable=broad-except
        db.session.rollback()
        current_app.logger.error("Error eliminando lead %s: %s", lead_id, exc)
        flash("No se pudo eliminar el lead", "danger")

    return redirect(url_for("leads.leads_list"))

# ---------------------------------------------------------------------------
# Historial
# ---------------------------------------------------------------------------

@leads_bp.post("/<lead_id>/delete-test")
@login_required
@require_perm("delete_leads")
def delete_test_lead(lead_id):
    """Delete a test lead and its history/ledger."""
    Lead = getattr(Base.classes, "leads", None)
    LeadHistory = getattr(Base.classes, "lead_history", None)
    Ledger = getattr(Base.classes, "ledger", None)
    if Lead is None:
        abort(404)
    lead = db.session.get(Lead, lead_id)
    if not lead or not getattr(lead, "is_test", False):
        flash("Solo se pueden eliminar leads de prueba", "warning")
        return redirect(url_for("leads.list_leads"))
    # delete related
    if LeadHistory is not None:
        db.session.query(LeadHistory).filter(LeadHistory.lead_id == lead_id).delete()
    if Ledger is not None:
        db.session.query(Ledger).filter(Ledger.lead_id == lead_id).delete()
    db.session.delete(lead)
    db.session.commit()
    flash("Lead de prueba eliminado", "success")
    return redirect(url_for("leads.list_leads"))


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
    # guardar estado previo para detectar transiciones
    old_state_id = lead.state_id
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
                # ensure receipt optional but we can store
                pass
                flash("Debes indicar las cuotas del plan de pago", "warning")
                return render_template("records/lead_status_form.html", form=form, lead=lead, matriculado_id=MATRICULADO_ID)
            lead.program_id = form.program_id.data
            lead.edition_id = form.edition_id.data
            lead.payment_fees = form.installments.data
            # guardar archivo comprobante si viene
            if form.receipt.data:
                up_folder = current_app.config.get("RECEIPT_UPLOAD_FOLDER", os.path.join(current_app.static_folder, "uploads", "receipts"))
                os.makedirs(up_folder, exist_ok=True)
                filename = f"{uuid.uuid4().hex}_{secure_filename(form.receipt.data.filename)}"
                save_path = os.path.join(up_folder, filename)
                form.receipt.data.save(save_path)
                if hasattr(lead, "matricula_receipt"):
                    setattr(lead, "matricula_receipt", filename)
                else:
                    # fallback raw update when automap lacks column
                    db.session.execute(
                        db.text("UPDATE leads SET matricula_receipt = :fn WHERE id = :lid"),
                        {"fn": filename, "lid": lead.id},
                    )
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
        # Asignar comercial:
        # – Si el lead NO tiene comercial asignado y el estado previo era
        #   «Pendiente de contactar» (o equivalente) y el nuevo estado es
        #   diferente.
        # – Mantener lógica anterior para la transición a Matriculado.
        if not getattr(lead, 'commercial_id', None):
            try:
                asignar = False
                # Detectar si el estado previo es "Pendiente de contactar"
                if StateLead is not None and old_state_id is not None:
                    prev_state = db.session.get(StateLead, old_state_id)
                    if prev_state:
                        name_upper = prev_state.name.upper()
                        if "PENDIENTE" in name_upper and "CONTACT" in name_upper:
                            asignar = True
                # También asignar si pasa a Matriculado (compatibilidad lógica anterior)
                if asignar or new_state == MATRICULADO_ID:
                    lead.commercial_id = current_user.id
            except Exception:
                # Evitar que un fallo al asignar corte el flujo de actualización
                pass
        try:
            db.session.commit()
            # generar movimientos de libro mayor
            # generar movimientos solo si estado nuevo es MATRICULADO
            if new_state == MATRICULADO_ID:
                try:
                    from sigp.common.ledger_utils import create_commission_ledger
                    added = create_commission_ledger(lead)
                    if added == 0:
                        flash("No se generaron cuotas nuevas porque ya existían movimientos para este lead", "info")
                except Exception as exc:
                    current_app.logger.exception("Error creando ledger: %s", exc)
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
                    plain_body = f"El lead {lead.candidate_name or lead.id} ahora está en estado {state_name}. Observaciones: {obs}"
                    html_body = render_template('emails/lead_state_change.html',
                         candidate_name=lead.candidate_name or lead.id,
                         state_name=state_name,
                         observations=obs) 
                    try:
                        from sigp.common.email_utils import send_simple_mail
                        send_simple_mail([presc_email], subject, html_body, html=True, text_body=plain_body)
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

    # Deshabilitar el campo estado para todos excepto rol "Comercial"
    from flask_login import current_user
    role_obj = getattr(current_user, "role", None)
    if role_obj is None or not getattr(role_obj, "name", None):
        # fallback lookup by role_id
        RoleTbl = getattr(Base.classes, "roles", None)
        if RoleTbl is not None and getattr(current_user, "role_id", None):
            role_obj = db.session.get(RoleTbl, current_user.role_id)
    role_name = getattr(role_obj, "name", "").lower() if role_obj else ""
    if role_name != "comercial":
        form.state_id.render_kw = {"disabled": True}

    if form.validate_on_submit():
        lead.prescriptor_id = form.prescriptor_id.data
        lead.candidate_name = form.candidate_name.data
        lead.candidate_email = form.candidate_email.data
        lead.program_info_id = form.program_info_id.data or None
        lead.candidate_cellular = form.candidate_cellular.data
        # Si el campo estado está habilitado y vino un valor, actualizar
        if form.state_id.data:
            lead.state_id = form.state_id.data
        db.session.commit()
        flash("Lead actualizado", "success")
        return redirect(url_for("leads.leads_list"))

    return render_template("records/lead_form.html", form=form, action=url_for("leads.edit_lead", lead_id=lead_id), edit=True)

# ---------------------------------------------------------------------------
# Public embeddable lead form (iframe)
# URL: GET/POST /leads/embed?prescriptor=<id>&title=&primary=&program=&success_url=
# ---------------------------------------------------------------------------

def _apply_frame_headers(resp):
    """Apply CSP to allow embedding from configured origins."""
    allow = current_app.config.get("EMBED_ALLOWED_ORIGINS")
    if isinstance(allow, str) and allow.strip():
        # Comma-separated to space-separated list for frame-ancestors
        origins = " ".join([o.strip() for o in allow.split(",") if o.strip()])
    else:
        origins = "*"  # fallback: allow anywhere (consider restricting in prod)
    resp.headers["Content-Security-Policy"] = f"frame-ancestors {origins}"
    # Avoid legacy X-Frame-Options that would block framing
    resp.headers.pop("X-Frame-Options", None)
    return resp


def _default_pending_state_id():
    """Try to find a 'Pendiente de contactar' like state, else fallback to 1."""
    try:
        if StateLead is not None:
            srows = db.session.query(StateLead).all()
            for s in srows:
                name = getattr(s, "name", "").upper()
                if "PENDIENTE" in name and "CONTACT" in name:
                    return s.id
    except Exception:
        pass
    return 1


@leads_bp.route("/embed", methods=["GET"])  # final URL: /leads/embed
def embed_lead_get():
    prescriptor_id = request.args.get("prescriptor", "").strip()
    if not prescriptor_id or Prescriptor is None:
        # Show simple error inside iframe
        html = render_template(
            "public/lead_embed.html",
            error="Prescriptor no especificado",
            title=request.args.get("title", "Quiero información"),
            primary=request.args.get("primary", "#0d6efd"),
        )
        return _apply_frame_headers(make_response(html))

    prescriptor = db.session.get(Prescriptor, prescriptor_id)
    if not prescriptor:
        html = render_template(
            "public/lead_embed.html",
            error="Prescriptor no válido",
            title=request.args.get("title", "Quiero información"),
            primary=request.args.get("primary", "#0d6efd"),
        )
        return _apply_frame_headers(make_response(html))

    # Optional preselect program
    program_id = request.args.get("program", "")
    programs = []
    if Program is not None:
        try:
            programs = db.session.query(Program).order_by(Program.name).all()
        except Exception:
            programs = []

    html = render_template(
        "public/lead_embed.html",
        prescriptor_id=prescriptor_id,
        title=request.args.get("title", "Quiero información"),
        primary=request.args.get("primary", "#0d6efd"),
        program_id=program_id,
        programs=programs,
        success=False,
        success_url=request.args.get("success_url", ""),
    )
    return _apply_frame_headers(make_response(html))


@leads_bp.route("/embed/guide", methods=["GET"])  # final URL: /leads/embed/guide
def embed_lead_guide():
    # Public guide page for prescriptors
    try:
        programs = db.session.query(Program).order_by(Program.name).all() if Program is not None else []
    except Exception:
        programs = []
    html = render_template("public/lead_embed_guide.html", programs=programs)
    return make_response(html)

@leads_bp.route("/embed", methods=["POST"])  # final URL: /leads/embed
def embed_lead_post():
    prescriptor_id = request.form.get("prescriptor_id", "").strip()
    name = request.form.get("candidate_name", "").strip()
    email = request.form.get("candidate_email", "").strip()
    cellular = request.form.get("candidate_cellular", "").strip()
    observations = request.form.get("observations", "").strip()
    program_id = request.form.get("program_info_id", "").strip() or None
    title = request.args.get("title", "Quiero información")
    primary = request.args.get("primary", "#0d6efd")
    success_url = request.args.get("success_url", "")

    errors = []
    if not prescriptor_id:
        errors.append("Falta prescriptor")
    if not name:
        errors.append("El nombre es obligatorio")
    # email opcional, pero si viene, validación mínima
    if email and ("@" not in email or "." not in email.split("@")[-1]):
        errors.append("Email inválido")

    if errors or Prescriptor is None or Lead is None:
        html = render_template(
            "public/lead_embed.html",
            prescriptor_id=prescriptor_id,
            title=title,
            primary=primary,
            error=" | ".join(errors) if errors else "Modelo no disponible",
            candidate_name=name,
            candidate_email=email,
            candidate_cellular=cellular,
            observations=observations,
            program_id=program_id,
            programs=db.session.query(Program).order_by(Program.name).all() if Program is not None else [],
        )
        return _apply_frame_headers(make_response(html))

    # Create lead
    try:
        state_id = _default_pending_state_id()
        lead = Lead(
            id=str(uuid.uuid4()),
            prescriptor_id=prescriptor_id,
            program_info_id=program_id,
            state_id=state_id,
            candidate_name=name,
            candidate_email=email or None,
            candidate_cellular=cellular or None,
        )
        # Persist observations if the model supports it
        try:
            if hasattr(lead, "observations"):
                setattr(lead, "observations", observations)
        except Exception:
            pass
        db.session.add(lead)
        db.session.commit()
        # log history (best-effort)
        try:
            from sigp.common.lead_utils import log_lead_change
            note = "Alta de lead desde iframe público"
            if observations:
                note = f"{note}. Observaciones: {observations}"
            log_lead_change(lead.id, lead.state_id, note)
            db.session.commit()
        except Exception:
            pass

        # notify commercials if program has configured emails (best-effort)
        try:
            if Program is not None and program_id:
                program = db.session.get(Program, program_id)
                if program and getattr(program, "commercial_emails", None):
                    from sigp.common.email_utils import send_simple_mail
                    emails = [e.strip() for e in program.commercial_emails.split(',') if e.strip()]
                    if emails:
                        # resolve prescriptor display name similar to landing
                        try:
                            PrescriptorTbl = getattr(Base.classes, 'prescriptors', None)
                            presc_name = prescriptor_id
                            if PrescriptorTbl is not None:
                                presc = db.session.get(PrescriptorTbl, prescriptor_id)
                                if presc:
                                    presc_name = getattr(presc, 'squeeze_page_name', None) or getattr(presc, 'name', None) or presc_name
                        except Exception:
                            presc_name = prescriptor_id
                        subject = f"Nuevo lead para programa {getattr(program,'name', program.id)}"
                        plain_body = (
                            "Se ha generado un nuevo lead desde el formulario embebido.\n\n"
                            f"Prescriptor: {presc_name}\n"
                            f"Programa: {getattr(program,'name', program.id)}\n"
                            f"Nombre candidato: {name}\n"
                            f"Email: {email or '-'}\n"
                            f"Celular: {cellular or '-'}\n"
                            f"Observaciones: {observations or '-'}\n"
                        )
                        # absolute URL to edit/view lead in backoffice
                        try:
                            lead_url = url_for('leads.edit_lead', lead_id=lead.id, _external=True)
                        except Exception:
                            lead_url = None
                        html_body = render_template(
                            'emails/new_lead.html',
                            origin='Formulario embebido',
                            prescriptor=presc_name,
                            program=getattr(program,'name', program.id),
                            candidate_name=name,
                            candidate_email=email,
                            candidate_cellular=cellular,
                            observations=observations,
                            lead_url=lead_url,
                        )
                        send_simple_mail(emails, subject, html_body, html=True, text_body=plain_body)
        except Exception as exc:
            current_app.logger.exception("Error enviando mail a comerciales (iframe): %s", exc)

        # notify prescriptor (best-effort)
        try:
            PrescriptorTbl = getattr(Base.classes, 'prescriptors', None)
            UsersTbl = getattr(Base.classes, 'users', None)
            if PrescriptorTbl is not None:
                presc = db.session.get(PrescriptorTbl, prescriptor_id)
                presc_email = None
                presc_name = prescriptor_id
                if presc:
                    presc_name = getattr(presc, 'squeeze_page_name', None) or getattr(presc, 'name', None) or prescriptor_id
                    # prefer linked user email
                    if getattr(presc, 'user_id', None) and UsersTbl is not None:
                        u = db.session.get(UsersTbl, presc.user_id)
                        if u and getattr(u, 'email', None):
                            presc_email = u.email
                    presc_email = presc_email or getattr(presc, 'email', None)
                if presc_email:
                    subject = "Nuevo lead recibido"
                    # absolute URL
                    try:
                        lead_url = url_for('leads.edit_lead', lead_id=lead.id, _external=True)
                    except Exception:
                        lead_url = None
                    plain_body = (
                        f"Hola {presc_name}, se generó un nuevo lead desde tu formulario.\n\n"
                        f"Programa: {getattr(program,'name', program.id) if program_id and program else '-'}\n"
                        f"Nombre candidato: {name}\n"
                        f"Email: {email or '-'}\n"
                        f"Celular: {cellular or '-'}\n"
                        f"Observaciones: {observations or '-'}\n"
                        + (f"\nVer lead: {lead_url}\n" if lead_url else "")
                    )
                    html_body = render_template(
                        'emails/new_lead.html',
                        origin='Tu formulario embebido',
                        prescriptor=presc_name,
                        program=(getattr(program,'name', program.id) if program_id and program else '-'),
                        candidate_name=name,
                        candidate_email=email,
                        candidate_cellular=cellular,
                        observations=observations,
                        lead_url=lead_url,
                    )
                    from sigp.common.email_utils import send_simple_mail
                    send_simple_mail([presc_email], subject, html_body, html=True, text_body=plain_body)
        except Exception as exc:
            current_app.logger.exception("Error enviando mail a prescriptor (iframe): %s", exc)
    except Exception as exc:
        current_app.logger.exception("Error creando lead vía iframe: %s", exc)
        html = render_template(
            "public/lead_embed.html",
            prescriptor_id=prescriptor_id,
            title=title,
            primary=primary,
            error="No se pudo crear el lead. Intenta más tarde.",
            candidate_name=name,
            candidate_email=email,
            candidate_cellular=cellular,
            program_id=program_id,
            programs=db.session.query(Program).order_by(Program.name).all() if Program is not None else [],
        )
        return _apply_frame_headers(make_response(html))

    # Success: render thank-you or in-iframe redirect
    html = render_template(
        "public/lead_embed.html",
        success=True,
        success_url=success_url,
        title=title,
        primary=primary,
    )
    return _apply_frame_headers(make_response(html))
