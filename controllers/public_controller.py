from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, Length, Optional
from sigp import db
from sigp.models import Base
import uuid
import hashlib
import os
from datetime import datetime

# Creamos el Blueprint 'public'
public_bp = Blueprint("public", __name__, url_prefix="/public")

# Definimos el formulario aquí mismo para no depender de auth_controller
class PublicSignupForm(FlaskForm):
    name = StringField("Nombre y Apellido", validators=[DataRequired(), Length(max=255)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    cellular = StringField("Celular / WhatsApp", validators=[DataRequired(), Length(max=50)])
    language = SelectField(
        "Idioma de Convenio",
        choices=[("Español", "Español"), ("Inglés", "Inglés"), ("Portugués", "Portugués")],
        default="Español",
        validators=[DataRequired()],
    )
    is_student = BooleanField("Soy alumno de Sports Data Campus", default=True)
    
    # NUEVOS CAMPOS (Son opcionales para WTForms, los validamos a mano si tilda "Soy Alumno")
    document_type = SelectField("Tipo de Documento", choices=[("", "Tipo de Documento..."), ("DNI", "DNI"), ("NIE", "NIE"), ("Pasaporte", "Pasaporte"), ("Otro", "Otro")], validators=[Optional()])
    document_number = StringField("Número de Documento", validators=[Optional(), Length(max=50)])
    domicile = StringField("Domicilio Completo", validators=[Optional(), Length(max=255)])
    
    observations = TextAreaField("Observaciones", validators=[DataRequired(), Length(max=1000)])
    submit = SubmitField("Enviar Solicitud")

@public_bp.get("/inscription")
def signup_get():
    form = PublicSignupForm()
    return render_template("layouts/signup.html", form=form)

@public_bp.post("/inscription")
def signup_post():
    form = PublicSignupForm(request.form)
    
    # 1. Validación Condicional: Si es alumno, exigir datos legales
    if form.is_student.data:
        if not form.document_type.data or not form.document_number.data or not form.domicile.data:
            flash("Como eres alumno, el Tipo de Documento, Número y Domicilio son obligatorios para prepararte el convenio automáticamente.", "warning")
            return render_template("layouts/signup.html", form=form)

    if not form.validate_on_submit():
        flash("Por favor verifica los datos ingresados.", "warning")
        return render_template("layouts/signup.html", form=form)
    
    try:
        # 1. Verificar si el email ya existe
        User = getattr(Base.classes, "users", None)
        if not User:
            flash("Error interno del sistema (users no disponible).", "danger")
            return render_template("layouts/signup.html", form=form)

        email_val = form.email.data.strip().lower()
        existing_user = db.session.query(User).filter(User.email == email_val).first()
        if existing_user:
            flash("El email ingresado ya se encuentra registrado. Por favor, inicia sesión.", "warning")
            return redirect(url_for("auth.login_get"))

        # 2. Crear el Usuario base (Activo por defecto)
        new_user = User(id=str(uuid.uuid4()))
        new_user.name = form.name.data.strip()
        new_user.email = email_val
        new_user.cellular = form.cellular.data.strip()
        # Asignamos Rol Prescriptor (Ajusta este UUID si en tu BD es distinto)
        new_user.role_id = "5e6e517e-584b-42be-a7a3-564ee14e8723"
        new_user.state_id = 2
        
        temp_pass = str(uuid.uuid4())
        new_user.password_hash = hashlib.sha256(temp_pass.encode()).hexdigest()
        db.session.add(new_user)
        db.session.flush()

        # 3. Crear el Registro de Prescriptor
        Prescriptor = getattr(Base.classes, "prescriptors", None)
        if not Prescriptor:
            flash("Error interno (prescriptors no disponible).", "danger")
            return render_template("layouts/signup.html", form=form)

        new_presc = Prescriptor(id=str(uuid.uuid4()))
        new_presc.user_id = new_user.id
        new_presc.squeeze_page_name = form.name.data.strip()
        new_presc.observations = form.observations.data.strip()
        new_presc.language = form.language.data or "Español"
        
        # --- NUEVO: VALORES POR DEFECTO OBLIGATORIOS PARA LA BD ---
        new_presc.state_id = 1  # Estado: Activo / Candidato inicial
        new_presc.squeeze_page_status = "TEST"
        
        # Buscar dinámicamente el 'type_id' para que nunca sea Null
        TypeModel = getattr(Base.classes, "prescriptor_types", None)
        default_type_id = 1
        if TypeModel:
            tipo_buscado = "%alumno%" if form.is_student.data else "%externo%"
            t_row = db.session.query(TypeModel).filter(TypeModel.name.ilike(tipo_buscado)).first()
            if not t_row:
                t_row = db.session.query(TypeModel).first() # Fallback al primer tipo que exista
            if t_row:
                default_type_id = t_row.id
                
        new_presc.type_id = default_type_id
        new_presc.proposed_type_id = default_type_id
        # ----------------------------------------------------------

        # Guardar datos legales recogidos
        new_presc.document_type = form.document_type.data
        new_presc.document_number = form.document_number.data
        new_presc.domicile = form.domicile.data

        # --- LÓGICA DE ALUMNO ---
        if form.is_student.data:
            new_presc.agreement_category = "Persona Alumno"
            
            # Buscar el subestado "Firma de contrato"
            Substate = getattr(Base.classes, "substate_prescriptor", None)
            firma_id = 3 # ID por defecto como fallback
            if Substate:
                firma_row = db.session.query(Substate).filter(Substate.name.ilike("%firma%")).first()
                if firma_row:
                    firma_id = firma_row.id
            new_presc.sub_state_id = firma_id
        else:
            # Si NO es alumno, entra normal como Candidato
            new_presc.sub_state_id = 1

        db.session.add(new_presc)
        db.session.commit()

        try:
            from sigp.common.prescriptor_utils import sync_commissions_for_prescriptor
            sync_commissions_for_prescriptor(new_presc.id)
        except Exception as exc:
            current_app.logger.exception("Error sincronizando comisiones del prescriptor público: %s", exc)

        # ---------------------------------------------------------------------
        # 4. GENERACIÓN DE CONTRATO Y ENVÍO DE EMAIL AUTOMÁTICO (SOLO ALUMNOS)
        # ---------------------------------------------------------------------
        if form.is_student.data:
            from itsdangerous import URLSafeTimedSerializer
            from sigp.services.contract_service import generate_contract_pdf
            from sigp.common.email_utils import build_contract_signing_email_text, send_simple_mail
            from sigp.controllers.auth_controller import _generate_token

            try:
                current_app.logger.info(
                    "Public signup: generating contract for %s language=%s category=%s",
                    email_val,
                    getattr(new_presc, "language", None),
                    getattr(new_presc, "agreement_category", None),
                )
                # A) Generar PDF Base
                pdf_path = generate_contract_pdf(new_presc, filename=f"contract_{new_presc.id}.pdf")
                base_rel_url = url_for("static", filename=f"contracts/{os.path.basename(pdf_path)}")
                new_presc.contract_url = base_rel_url
                db.session.commit()
                current_app.logger.info("Public signup: contract generated at %s", pdf_path)

                # B) Generar Token y Enlaces
                rel_url = getattr(new_presc, "contract_url", None)
                abs_url = url_for("static", filename=f"contracts/{os.path.basename(rel_url)}", _external=True) if rel_url else ""
                
                secret = current_app.config.get("SIGN_TOKEN_SECRET")
                serializer = URLSafeTimedSerializer(secret_key=secret, salt="sigp.contracts")
                token_p = serializer.dumps({"c": str(new_presc.id), "r": "prescriptor"})
                link = url_for("contracts.sign_prescriptor", token=token_p, _external=True)

                platform_base = (current_app.config.get("BASE_URL") or request.host_url).rstrip("/")
                login_url = f"{platform_base}{url_for('auth.login_get')}"
                token_reset = _generate_token(email_val)
                reset_url = f"{platform_base}{url_for('auth.reset_password', token=token_reset)}"
                logo_url = "https://sportsdatacampus.com/wp-content/uploads/2021/07/SDC_Logo.png"

                # C) Enviar Email Automático para firmar
                html_body = render_template(
                    "emails/contract_link.html",
                    prescriptor=new_presc,
                    sign_link=link,
                    contract_url=abs_url,
                    logo_url=logo_url,
                    platform_url=platform_base + "/",
                    email=email_val,
                    login_url=login_url,
                    reset_url=reset_url,
                )
                subject, plain_body = build_contract_signing_email_text(
                    language=getattr(new_presc, "language", None),
                    name=new_presc.squeeze_page_name,
                    email=email_val,
                    platform_base=platform_base,
                    reset_url=reset_url,
                    sign_link=link,
                    contract_url=abs_url,
                )
                sent = send_simple_mail([email_val], subject, html_body, html=True, text_body=plain_body)
                if sent:
                    current_app.logger.info("Public signup: contract signing email sent to %s", email_val)
                else:
                    current_app.logger.warning("Public signup: contract signing email was not accepted by SMTP for %s", email_val)

                # D) Notificación In-App al candidato
                Notification = getattr(Base.classes, "notifications", None)
                if Notification:
                    notif = Notification(
                        id=str(uuid.uuid4()),
                        user_id=new_presc.user_id,
                        title="Contrato disponible para firma",
                        body=f"Firmá tu contrato: {link}",
                        link_url=link,
                        notif_type="ACTION",
                        is_read=0,
                        created_at=datetime.utcnow(),
                    )
                    db.session.add(notif)
                    db.session.commit()
            except Exception as e:
                current_app.logger.exception("Error generando/enviando contrato público para %s: %s", email_val, e)
        else:
            try:
                from sigp.common.email_utils import build_signup_received_email_text, send_simple_mail

                subject, plain_body = build_signup_received_email_text(
                    language=getattr(new_presc, "language", None),
                    name=new_presc.squeeze_page_name,
                )
                sent = send_simple_mail([email_val], subject, plain_body)
                if sent:
                    current_app.logger.info("Public signup: confirmation email sent to %s", email_val)
                else:
                    current_app.logger.warning("Public signup: confirmation email was not accepted by SMTP for %s", email_val)
            except Exception as e:
                current_app.logger.exception("Error enviando confirmación pública para %s: %s", email_val, e)

        # 5. Notificar a los administradores que alguien se registró (Aplica para ambos casos)
        try:
            from sigp.common.email_utils import internal_notification_recipients

            admin_emails = internal_notification_recipients()
            if admin_emails:
                base_url = (current_app.config.get('BASE_URL') or request.host_url).rstrip('/')
                edit_url = f"{base_url}{url_for('prescriptors.edit_prescriptor', prescriptor_id=new_presc.id)}"
                from sigp.common.email_utils import send_simple_mail

                label_alumno = "SÍ" if form.is_student.data else "NO"
                
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

        # 6. ÉXITO: Redirigir a la pantalla de agradecimiento
        return render_template("layouts/signup_success.html", language=form.language.data or "Español")

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Error en public signup: %s", e)
        flash("Hubo un error al procesar tu solicitud.", "danger")
        return render_template("layouts/signup.html", form=form)
