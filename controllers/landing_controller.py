"""Landing pública por prescriptor.

Proporciona una página pública (sin autenticación) que muestra la información básica
 del prescriptor y un formulario para que un interesado deje sus datos. Dicho
 formulario crea un registro en la tabla `leads` ligado al prescriptor.
"""
from __future__ import annotations

import uuid
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional

from sigp import db
from sigp.models import Base

# Tablas reflejadas
Prescriptor = getattr(Base.classes, "prescriptors", None)
Lead = getattr(Base.classes, "leads", None)
Program = getattr(Base.classes, "programs", None)
# En la mayoría de los despliegues el estado "NUEVO" suele tener id=1. Si no
# existiera dicha tabla o el id fuese distinto, simplemente se insertará el id
# declarado a continuación sin romper la inserción.
DEFAULT_LEAD_STATE_ID = 1

landing_bp = Blueprint("landing", __name__, url_prefix="/p")


class PublicLeadForm(FlaskForm):
    """Formulario de captación visible en la landing."""

    name = StringField("Nombre", validators=[DataRequired(), Length(max=100)])
    email = StringField("Email", validators=[Optional(), Email(), Length(max=255)])
    cellular = StringField("Celular", validators=[Optional(), Length(max=50)])
    program_info_id = SelectField("Programa", coerce=str, validators=[Optional()])
    submit = SubmitField("Me interesa")

    class Meta:
        csrf = True


@landing_bp.route("/<prescriptor_id>", methods=["GET", "POST"])
def landing_page(prescriptor_id: str):
    """Renderiza la landing y procesa la generación de un lead."""

    if Prescriptor is None:
        flash("Módulo de prescriptores no disponible", "danger")
        return redirect("/")

    prescriptor = db.session.get(Prescriptor, prescriptor_id)
    if prescriptor is None:
        flash("Página no encontrada", "warning")
        return redirect("/")

    form = PublicLeadForm()
    # Poblar choices de programas
    if Program is not None:
        prog_rows = db.session.query(Program).all()
        prog_choices = [("", "Seleccione programa")] + [
            (p.id, getattr(p, "name", getattr(p, "nombre", str(p.id)))) for p in prog_rows
        ]
        form.program_info_id.choices = prog_choices
    else:
        form.program_info_id.choices = [("", "-")]

    if form.validate_on_submit():
        if Lead is None:
            flash("Módulo de leads no disponible", "danger")
            return redirect(request.url)
        # Crear lead ligado al prescriptor
        # Determinar estado del lead: si la squeeze está en TEST utilizar estado 'TEST' si existe.
        state_id = DEFAULT_LEAD_STATE_ID
        StateLead = getattr(Base.classes, "state_lead", None)
        if prescriptor.squeeze_page_status == "TEST" and StateLead is not None:
            test_state = (
                db.session.query(StateLead)
                .filter(StateLead.name.ilike("test"))
                .first()
            )
            if test_state:
                state_id = test_state.id
        new_lead = Lead(
            id=str(uuid.uuid4()),
            prescriptor_id=prescriptor_id,
            candidate_name=form.name.data,
            candidate_email=form.email.data or None,
            candidate_cellular=form.cellular.data or None,
            program_info_id=form.program_info_id.data or None,
            state_id=state_id,
        )
        db.session.add(new_lead)
        db.session.commit()
        current_app.logger.info("Nuevo lead captado para prescriptor %s", prescriptor_id)
        return render_template("public/thanks.html", prescriptor=prescriptor)

    # Reunir imágenes para el carrusel
    images = []
    for attr in ("squeeze_page_image_1", "squeeze_page_image_2", "squeeze_page_image_3"):
        img_url = getattr(prescriptor, attr, None)
        if img_url:
            images.append(img_url)

    return render_template(
        "public/landing_prescriptor.html",
        prescriptor=prescriptor,
        images=images,
        form=form,
    )
