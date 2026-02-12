"""Controlador de autenticación.

Define un Blueprint llamado ``auth`` con rutas para login y logout.
"""
import uuid
from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
    current_app,
    session,
)
from flask_login import login_user, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import EqualTo
from wtforms.validators import DataRequired, Email, Length
from werkzeug.middleware.proxy_fix import ProxyFix  

import hashlib
from sigp import db, bcrypt
from sigp.models import Base


# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# ---------------------------------------------------------------------------
# Formulario de Alta Rápida (Signup)
# ---------------------------------------------------------------------------
class SignupForm(FlaskForm):
    name = StringField("Nombre y Apellido", validators=[DataRequired(), Length(max=255)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    cellular = StringField("Celular / WhatsApp", validators=[DataRequired(), Length(max=50)])
    is_student = BooleanField("Soy alumno de Sports Data Campus", default=True)
    observations = TextAreaField("Observaciones", validators=[DataRequired(), Length(max=1000)]) # Campo obligatorio para que cuenten por qué quieren entrar
    submit = SubmitField("Enviar Solicitud")

# ---------------------------------------------------------------------------
# Formulario de Login
# ---------------------------------------------------------------------------


class LoginForm(FlaskForm):
    email = StringField(
        "Correo electrónico",
        validators=[DataRequired(), Email(), Length(max=255)],
        render_kw={"placeholder": "email@example.com"},
    )
    password = PasswordField(
        "Contraseña", validators=[DataRequired(), Length(min=4, max=255)]
    )
    remember = BooleanField("Recordarme")
    submit = SubmitField("Ingresar")

    class Meta:
        csrf = True


# ---------------------------------------------------------------------------
# Form Forgot / Reset
# ---------------------------------------------------------------------------

class ForgotForm(FlaskForm):
    email = StringField("Correo electrónico", validators=[DataRequired(), Email()], render_kw={"placeholder":"email@example.com"})
    submit = SubmitField("Enviar enlace")

class ContactForm(FlaskForm):
    name = StringField("Nombre", validators=[DataRequired(), Length(max=255)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    message = TextAreaField("Mensaje", validators=[DataRequired(), Length(max=2000)])
    submit = SubmitField("Enviar")

class ResetForm(FlaskForm):
    password = PasswordField("Nueva contraseña", validators=[DataRequired(), Length(min=4,max=255)])
    confirm = PasswordField("Confirmar contraseña", validators=[DataRequired(), EqualTo('password', message='Las contraseñas no coinciden')])
    submit = SubmitField("Restablecer")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

def _serializer():
    from flask import current_app
    return URLSafeTimedSerializer(current_app.config.get('SECRET_KEY','sigp-secret'))

def _generate_token(email:str):
    return _serializer().dumps(email, salt='pwd-reset')

def _confirm_token(token, max_age=5184000):
    try:
        email = _serializer().loads(token, salt='pwd-reset', max_age=max_age)
        return email
    except (BadSignature, SignatureExpired):
        return None

def _get_user_class():
    """Obtiene la clase de usuario reflejada, asumiendo tabla ``users``."""
    return getattr(Base.classes, "users", None)


# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------


@auth_bp.get("/forgot")
def forgot_get():
    form = ForgotForm()
    return render_template("layouts/forgot_password.html", form=form)

@auth_bp.post("/forgot")
def forgot_post():
    form = ForgotForm()
    if not form.validate_on_submit():
        flash("Email inválido", "danger");return redirect(url_for('auth.forgot_get'))
    User=_get_user_class();user=db.session.query(User).filter_by(email=form.email.data.lower().strip()).first() if User else None
    if user:
        token=_generate_token(user.email.strip().lower())
        reset_url=url_for('auth.reset_password', token=token, _external=True)
        plain_body=f"Hola,\n\nPara restablecer tu contraseña haz clic en el siguiente enlace:\n{reset_url}\n\nSi no solicitaste esto ignora el mensaje."
        html_body=render_template('emails/reset_password.html', reset_url=reset_url, user=user)
        from sigp.common.email_utils import send_simple_mail
        send_simple_mail([user.email],"Restablecer contraseña",html_body, html=True, text_body=plain_body)
    flash("Si el email existe se envió un enlace de recuperación", "info")
    return redirect(url_for('auth.login_get'))

@auth_bp.get("/reset/<token>")
def reset_password(token):
    email=_confirm_token(token)
    if not email:
        flash("Enlace inválido o expirado", "danger");return redirect(url_for('auth.login_get'))
    form=ResetForm()
    return render_template('layouts/reset_password.html', form=form)

@auth_bp.post("/reset/<token>")
def reset_password_post(token):
    email=_confirm_token(token)
    if not email:
        flash("Enlace inválido o expirado", "danger");return redirect(url_for('auth.login_get'))
    form=ResetForm()
    if not form.validate_on_submit():
        flash("Revisa el formulario", "danger");return render_template('layouts/reset_password.html', form=form)
    User=_get_user_class();user=db.session.query(User).filter_by(email=email).first() if User else None
    if not user:
        flash("Usuario no encontrado", "danger");return redirect(url_for('auth.login_get'))
    import hashlib;user.password_hash=hashlib.sha256(form.password.data.encode()).hexdigest();db.session.commit()
    flash("Contraseña actualizada, inicia sesión", "success")
    return redirect(url_for('auth.login_get'))


@auth_bp.get("/login")
def login_get():
    # Si ya está logueado redirigimos
    if current_user.is_authenticated:
        # Permitir forzar pantalla de login (p.ej. para firmar como otro usuario)
        if request.args.get("force") == "1":
            logout_user()
        else:
            return redirect(url_for("index"))

    # Guardar next en sesión si viene como parámetro
    nxt = request.args.get("next")
    if nxt:
        session["next_url"] = nxt

    form = LoginForm()
    return render_template("layouts/login.html", form=form)

# ---------------------------------------------------------------------------
# Rutas de Registro (Signup) Independiente
# ---------------------------------------------------------------------------

@auth_bp.get("/signup")
def signup_get():
    # Si ya está logueado, lo mandamos al dashboard
    if current_user.is_authenticated:
        return redirect("/")
    
    form = SignupForm()
    return render_template("layouts/signup.html", form=form)

@auth_bp.post("/signup")
def signup_post():
    form = SignupForm(request.form)
    
    # Si falla la validación, volvemos a mostrar el template de signup con los errores
    if not form.validate_on_submit():
        flash("Por favor verifica los datos ingresados.", "warning")
        return render_template("layouts/signup.html", form=form)

    # 1. Verificar si el email ya existe en Usuarios
    User = getattr(Base.classes, "users", None)
    if not User:
        flash("Error interno: Modelo User no disponible", "danger")
        return redirect(url_for('auth.login_get'))

    email_val = form.email.data.strip().lower()
    existing = db.session.query(User).filter_by(email=email_val).first()
    if existing:
        flash("Ese correo ya está registrado en el sistema. Intenta iniciar sesión.", "warning")
        return redirect(url_for('auth.login_get'))

    try:
        # --- LÓGICA DE ALUMNO VS EXTERNO ---
        if form.is_student.data:
            target_type = 5      # Alumno
            target_conf = 10     # Confianza Alta
            obs_prefix = "[ALUMNO] "
        else:
            target_type = 6      # Externo
            target_conf = 11     # Confianza Media/Baja
            obs_prefix = "[EXTERNO] "
        
        # 2. Crear USUARIO
        PRESCRIPTOR_ROLE_ID = "5e6e517e-584b-42be-a7a3-564ee14e8723" 
        new_user = User(id=str(uuid.uuid4()))
        new_user.name = form.name.data
        new_user.email = email_val
        new_user.cellular = form.cellular.data
        new_user.role_id = PRESCRIPTOR_ROLE_ID
        new_user.state_id = 1 
        temp_pass = str(uuid.uuid4())
        new_user.password_hash = hashlib.sha256(temp_pass.encode()).hexdigest()
        
        db.session.add(new_user)
        db.session.flush()

        # 3. Crear PRESCRIPTOR
        Prescriptor = getattr(Base.classes, "prescriptors", None)
        if not Prescriptor: raise Exception("Modelo Prescriptor no encontrado")

        CAPTADOR_ID = "828f0ff2-c863-4dcf-b6b9-7b0baea68c72"

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

        # 4. Notificar
        try:
            admin_emails = current_app.config.get("ADMIN_EMAILS") or []
            if isinstance(admin_emails, str):
                admin_emails = [e.strip() for e in admin_emails.split(",") if e.strip()]
            if not admin_emails:
                fallback = current_app.config.get("MAIL_DEFAULT_SENDER") or current_app.config.get("MAIL_USERNAME")
                if fallback: admin_emails = [fallback]

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
                    created_by="SOLICITUD WEB (QR/Link)",
                    edit_url=edit_url,
                    observations=f"Es Alumno: {label_alumno} | Motivo: {form.observations.data}" 
                )
                
                text_body = (
                    f"Nueva solicitud de prescriptor (Web):\n\n"
                    f"Candidato: {new_presc.squeeze_page_name}\n"
                    f"Es Alumno: {label_alumno}\n"
                    f"Email: {new_user.email}\n"
                    f"Motivo: {form.observations.data}\n\n"
                    f"Aprobar: {edit_url}\n"
                )
                send_simple_mail(admin_emails, f"Solicitud Prescriptor ({label_alumno} es alumno): {new_presc.squeeze_page_name}", html_body, html=True, text_body=text_body)
        except Exception as exc:
            current_app.logger.exception("Error notif: %s", exc)

        flash("¡Solicitud recibida! Te contactaremos pronto.", "success")
        # Al finalizar con éxito, SÍ mandamos al login
        return redirect(url_for('auth.login_get'))

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Error signup: %s", e)
        flash("Ocurrió un error al procesar tu solicitud.", "danger")
        return render_template("layouts/signup.html", form=form)

def _client_ip():
    fwd = request.headers.get("X-Forwarded-For")
    return fwd.split(",")[0].strip() if fwd else request.remote_addr

def _audit_event(user_id, success: bool, event_type: str):
    """Inserta un registro en login_audit."""
    Audit = getattr(Base.classes, "login_audit", None)
    if not Audit:
        return
    try:
        record = Audit(
            user_id=user_id,  # si es None no grabamos (ver logout)
            success=1 if success else 0,
            ip_addr=_client_ip(),
            event_type=event_type,
        )
        db.session.add(record)
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Audit failed")


@auth_bp.post("/contact")
def contact_post():
    form = ContactForm(request.form)
    if not form.validate_on_submit():
        flash("Completa todos los campos", "danger");return redirect(url_for('auth.login_get')+"#contact")
    cfg=current_app.config
    admin = cfg.get('CONTACT_EMAIL', cfg.get('MAIL_DEFAULT_SENDER'))
    subject="Contacto SIGP"
    plain_body=f"Nombre: {form.name.data}\nEmail: {form.email.data}\nMensaje:\n{form.message.data}"
    html_body=render_template('emails/contact_message.html', name=form.name.data, email=form.email.data, message=form.message.data)
    from sigp.common.email_utils import send_simple_mail
    send_simple_mail([admin], subject, html_body, html=True, text_body=plain_body)
    flash("Mensaje enviado, te responderemos pronto", "success")
    return redirect(url_for('auth.login_get'))


@auth_bp.post("/login")
def login_post():
    form = LoginForm(request.form)

    if not form.validate_on_submit():
        flash("Datos de formulario inválidos", "danger")
        return redirect(url_for("auth.login_get"))

    User = _get_user_class()
    if not User:
        flash("Modelo de usuario no disponible", "danger")
        return redirect(url_for("auth.login_get"))

    user = db.session.query(User).filter_by(email=form.email.data).first()

    if user and user.password_hash and user.password_hash.lower() == hashlib.sha256(form.password.data.encode()).hexdigest():
        _audit_event(user.id, True, "LOGIN")
        login_user(user, remember=form.remember.data)
        # Redirigir a next si existe y es relativo (simple check)
        nxt = session.pop("next_url", None) or request.args.get("next")
        if nxt and isinstance(nxt, str) and nxt.startswith("/"):
            return redirect(nxt)
        return redirect("/")

    if user:
        _audit_event(user.id, False, "LOGIN")

    flash("Credenciales incorrectas", "danger")
    return redirect(url_for("auth.login_get"))


@auth_bp.get("/logout")
def logout():
    _audit_event(current_user.id if current_user.is_authenticated else None, True, "LOGOUT")
    logout_user()
    # Cierra la sesión del contexto actual
    db.session.remove()
    # Fuerza cierre del pool completo
    try:
        db.engine.dispose(close=True)
    except Exception:
        current_app.logger.exception("Error disposing engine on logout")
    # flash("Sesión finalizada", "info")
    return redirect(url_for("auth.login_get"))
