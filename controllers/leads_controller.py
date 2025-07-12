"""Leads management blueprint: simple listing of leads."""
from __future__ import annotations

from flask import Blueprint, render_template, request, flash, redirect, url_for
import uuid
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
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


# Helper to get display label for a prescriptor

def _presc_label(p):
    """Return readable label for a prescriptor: user's full_name/name/email else squeeze/name."""
    if p is None:
        return ""
    # Try linked user
    if User is not None and hasattr(p, "user_id") and p.user_id:
        u = db.session.get(User, p.user_id)
        if u:
            return getattr(u, "full_name", None) or getattr(u, "name", None) or getattr(u, "email", None) or str(u.id)
    # Fallback to prescriptor fields
    for attr in ("squeeze_page_name", "name", "nombre", "email"):
        val = getattr(p, attr, None)
        if val:
            return val
    return str(getattr(p, "id", "?"))

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

        flash("Lead creado", "success")
        return redirect(url_for("leads.leads_list"))

    # initial GET or validation errors
    return render_template("records/lead_form.html", form=form, action=url_for("leads.new_lead"), edit=False)


@leads_bp.post("/<lead_id>/delete")
@login_required
@require_perm("delete_leads")
def delete_lead(lead_id):
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
