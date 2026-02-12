from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length
from sigp import db
from sigp.models import Base
import uuid
import hashlib

# Creamos el Blueprint 'public'
public_bp = Blueprint("public", __name__, url_prefix="/public")

# Definimos el formulario aquí mismo para no depender de auth_controller
class PublicSignupForm(FlaskForm):
    name = StringField("Nombre y Apellido", validators=[DataRequired(), Length(max=255)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    cellular = StringField("Celular / WhatsApp", validators=[DataRequired(), Length(max=50)])
    is_student = BooleanField("Soy alumno de Sports Data Campus", default=True)
    observations = TextAreaField("Observaciones", validators=[DataRequired(), Length(max=1000)])
    submit = SubmitField("Enviar Solicitud")

@public_bp.get("/inscription")
def signup_get():
    # Renderizamos el mismo formulario que ya tenías
    form = PublicSignupForm()
    return render_template("layouts/signup.html", form=form)

@public_bp.post("/inscription")
def signup_post():
    form = PublicSignupForm(request.form)
    
    if not form.validate_on_submit():
        flash("Por favor verifica los datos ingresados.", "warning")
        return render_template("layouts/signup.html", form=form)

    # Lógica de guardado (Copiada y limpia)
    User = getattr(Base.classes, "users", None)
    if not User:
        flash("Error interno del sistema.", "danger")
        return render_template("layouts/signup.html", form=form)

    email_val = form.email.data.strip().lower()
    existing = db.session.query(User).filter_by(email=email_val).first()
    if existing:
        flash("Este correo ya está registrado. Por favor inicia sesión.", "warning")
        return redirect(url_for('auth.login_get'))

    try:
        # 1. Definir IDs y Tipos
        PRESCRIPTOR_ROLE_ID = "5e6e517e-584b-42be-a7a3-564ee14e8723"
        CAPTADOR_ID = "828f0ff2-c863-4dcf-b6b9-7b0baea68c72"
        
        if form.is_student.data:
            target_type = 5      # Alumno
            target_conf = 10     # Alta
            obs_prefix = "[ALUMNO] "
        else:
            target_type = 6      # Externo
            target_conf = 11     # Media
            obs_prefix = "[EXTERNO] "

        # 2. Crear Usuario
        new_user = User(id=str(uuid.uuid4()))
        new_user.name = form.name.data
        new_user.email = email_val
        new_user.cellular = form.cellular.data
        new_user.role_id = PRESCRIPTOR_ROLE_ID
        new_user.state_id = 1 
        new_user.password_hash = hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()
        
        db.session.add(new_user)
        db.session.flush()

        # 3. Crear Prescriptor
        Prescriptor = getattr(Base.classes, "prescriptors", None)
        new_presc = Prescriptor(
            id=str(uuid.uuid4()),
            user_id=new_user.id,
            squeeze_page_name=form.name.data,
            observations=f"{obs_prefix}{form.observations.data}",
            proposed_type_id=target_type,
            type_id=target_type,
            confidence_level_id=target_conf,
            user_getter_id=CAPTADOR_ID,
            state_id=1,
            sub_state_id=1,
            squeeze_page_status="TEST",
            created_at=db.func.now()
        )
        db.session.add(new_presc)
        db.session.commit()

        # 4. Notificar Admin
        try:
            admin_emails = current_app.config.get("ADMIN_EMAILS")
            if isinstance(admin_emails, str):
                admin_emails = [e.strip() for e in admin_emails.split(",") if e.strip()]
            if not admin_emails:
                fallback = current_app.config.get("MAIL_DEFAULT_SENDER")
                if fallback: admin_emails = [fallback]

            if admin_emails:
                base_url = (current_app.config.get('BASE_URL') or request.host_url).rstrip('/')
                edit_url = f"{base_url}{url_for('prescriptors.edit_prescriptor', prescriptor_id=new_presc.id)}"
                from sigp.common.email_utils import send_simple_mail

                label_alumno = "SÍ" if form.is_student.data else "NO"
                
                # Reutilizamos tu template de notificación existente
                html_body = render_template(
                    'emails/new_prescriptor_created.html',
                    name=new_presc.squeeze_page_name,
                    email=new_user.email,
                    cellular=new_user.cellular,
                    prescriptor_id=new_presc.id,
                    created_by="WEB PUBLICA",
                    edit_url=edit_url,
                    observations=f"Es Alumno: {label_alumno} | Motivo: {form.observations.data}" 
                )
                send_simple_mail(admin_emails, f"Nuevo Candidato ({label_alumno} es alumno): {new_presc.squeeze_page_name}", html_body, html=True)
        except Exception as e:
            current_app.logger.error(f"Error notificando admin: {e}")

        # 5. ÉXITO: Redirigir a la pantalla de agradecimiento
        return render_template("layouts/signup_success.html")

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Error en public signup: %s", e)
        flash("Hubo un error al procesar tu solicitud.", "danger")
        return render_template("layouts/signup.html", form=form)