from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from sigp import db
from sigp.models import Base
from sigp.services.contract_service import (
    generate_contract_pdf,
    sha256_file,
    sign_pades,
    stamp_signature_image,
    stamp_text_overlay,
    embed_pdf_metadata_xmp,
)
from sigp.common.email_utils import send_simple_mail
import uuid
from datetime import datetime
import os
from typing import Optional, Union

contracts_bp = Blueprint("contracts", __name__, url_prefix="/contracts")


def _sign_serializer():
    secret = current_app.config.get("SIGN_TOKEN_SECRET")
    return URLSafeTimedSerializer(secret_key=secret, salt="sigp.contracts")


def _make_token(contract_id: str, role: str) -> str:
    return _sign_serializer().dumps({"c": contract_id, "r": role})


def _read_token(token: str, max_age_min: int):
    try:
        data = _sign_serializer().loads(token, max_age=max_age_min * 60)
        return data
    except SignatureExpired:
        return None
    except BadSignature:
        return None


def _audit(event: str, prescriptor_id: Union[str, int], extra: Optional[dict] = None):
    """Inserta un registro en contract_audit_trail si la tabla existe."""
    try:
        Audit = getattr(Base.classes, "contract_audit_trail", None)
        if Audit is None:
            return
        row = Audit()
        setattr(row, "prescriptor_id", prescriptor_id)
        setattr(row, "event", event)
        setattr(row, "meta", (extra or {}))
        setattr(row, "created_at", datetime.utcnow())
        db.session.add(row)
        db.session.commit()
    except Exception:
        db.session.rollback()
        # no interrumpir flujo si la auditoría falla
        return


def _get_prescriptor_from_token_for_user(token: str, expected_role: str):
    """Lee el token y valida que el usuario logueado coincide con el prescriptor dueño.
    Devuelve (prescriptor, error_redirect) donde error_redirect es una respuesta redirect si falla.
    """
    data = _read_token(token, current_app.config.get("SIGN_LINK_EXP_MINUTES", 60))
    if not data or data.get("r") != expected_role:
        flash("Enlace inválido o expirado", "warning")
        return None, redirect("/")
    prescriptor_id = data.get("c")
    Prescriptor = getattr(Base.classes, "prescriptors", None)
    if not Prescriptor:
        flash("Modelo prescriptors no disponible", "danger")
        return None, redirect("/")
    prescriptor = db.session.get(Prescriptor, prescriptor_id)
    if not prescriptor:
        flash("Prescriptor no encontrado", "warning")
        return None, redirect("/")
    # Validar identidad: el usuario actual debe ser el owner del prescriptor
    owner_id = getattr(prescriptor, "user_id", None)
    if not owner_id or str(owner_id) != str(getattr(current_user, "id", None)):
        flash("Debes iniciar sesión como el prescriptor para firmar", "warning")
        next_url = url_for("contracts.sign_prescriptor", token=token)
        return None, redirect(url_for("auth.login_get", next=next_url, force=1))
    return prescriptor, None


@contracts_bp.route("/<prescriptor_id>/generate", methods=["GET", "POST"])
@login_required
def generate_for_prescriptor(prescriptor_id):
    Prescriptor = getattr(Base.classes, "prescriptors", None)
    if not Prescriptor:
        flash("Modelo prescriptors no disponible", "danger")
        return redirect("/")
    prescriptor = db.session.get(Prescriptor, prescriptor_id)
    if not prescriptor:
        flash("Prescriptor no encontrado", "warning")
        return redirect("/")

    # Permitir que url_for construya la URL durante una petición GET (render de formulario)
    # pero sólo ejecutar la generación en POST.
    if request.method == "GET":
        return redirect(url_for("prescriptors.edit_prescriptor", prescriptor_id=prescriptor_id))

    # Crear registro básico en memory (usaremos tabla luego con migración)
    # Por ahora solo generamos PDF base y mostramos link.
    pdf_path = generate_contract_pdf(prescriptor, filename=f"contract_{prescriptor.id}.pdf")
    pdf_hash = sha256_file(pdf_path)

    # Guardar URL en prescriptor para facilitar pruebas iniciales
    rel_url = url_for("static", filename=f"contracts/{os.path.basename(pdf_path)}")
    abs_url = url_for("static", filename=f"contracts/{os.path.basename(pdf_path)}", _external=True)
    if hasattr(prescriptor, "contract_url"):
        prescriptor.contract_url = rel_url
    try:
        db.session.commit()
    except Exception as exc:  # noqa
        db.session.rollback()
        current_app.logger.exception("Error guardando URL contrato: %s", exc)
        flash("Contrato generado pero no se pudo guardar la URL", "warning")
        return redirect(url_for("prescriptors.edit_prescriptor", prescriptor_id=prescriptor_id))

    # Token de firma del prescriptor (scaffolding)
    token_p = _make_token(contract_id=str(prescriptor.id), role="prescriptor")
    link = url_for("contracts.sign_prescriptor", token=token_p, _external=True)

    # Token de firma del presidente para pruebas
    token_pres = _make_token(contract_id=str(prescriptor.id), role="president")
    link_pres = url_for("contracts.sign_president_get", token=token_pres, _external=True)

    flash("Contrato generado", "success")
    # Enviar email al prescriptor con su enlace si tenemos correo
    presc_email = getattr(prescriptor, "email", None) or getattr(prescriptor, "squeeze_page_email", None)
    # Fallback: usar email del usuario asociado si no hay email en el prescriptor
    if not presc_email:
        try:
            UserModel = getattr(Base.classes, "users", None)
        except Exception:  # Base puede estar importado al inicio del módulo
            UserModel = None
        if UserModel is None:
            try:
                from sigp.models import Base as _Base
                UserModel = getattr(_Base.classes, "users", None)
            except Exception:
                UserModel = None
        if UserModel is not None and getattr(prescriptor, "user_id", None):
            u = db.session.get(UserModel, prescriptor.user_id)
            if u and getattr(u, "email", None):
                presc_email = u.email
    if not presc_email:
        flash("No se envió email: el prescriptor no tiene email cargado", "warning")
    else:
        # Verificar config de email para dar feedback al usuario
        mail_server = current_app.config.get("MAIL_SERVER")
        if not mail_server:
            flash("Email NO enviado: MAIL_SERVER no está configurado", "warning")
        try:
            # Cuerpo HTML usando template (igual que reset password)
            logo_url = url_for("static", filename="img/logos/SDC-logo.jpg", _external=True)
            html_body = render_template(
                "emails/contract_link.html",
                prescriptor=prescriptor,
                sign_link=link,
                contract_url=abs_url,
                logo_url=logo_url,
            )
            plain_body = (
                "Hola,\n\n"
                "Para firmar tu contrato ingresá al siguiente enlace:\n"
                f"{link}\n\n"
                "Si no solicitaste esto, ignorá este mensaje."
            )
            send_simple_mail(
                [presc_email],
                "Contrato disponible para firma",
                html_body,
                html=True,
                text_body=plain_body,
            )
            if mail_server:
                flash(f"Email enviado a {presc_email}", "info")
        except Exception as exc:  # noqa
            current_app.logger.exception("Error enviando correo de contrato: %s", exc)
            flash("No se pudo enviar el email al prescriptor", "warning")
    _audit("contract_generated", prescriptor.id, {"pdf": str(pdf_path), "sha256": pdf_hash})
    # Notificación in-app para el prescriptor con el link de firma
    try:
        Notification = getattr(Base.classes, "notifications", None)
        if Notification is not None and getattr(prescriptor, "user_id", None):
            import uuid as _uuid
            notif = Notification(
                id=str(_uuid.uuid4()),
                user_id=prescriptor.user_id,
                title="Contrato disponible para firma",
                body=f"Firmá tu contrato desde el enlace.",
                link_url=link,
                notif_type="ACTION",
                is_read=0,
                created_at=datetime.utcnow(),
            )
            db.session.add(notif)
            db.session.commit()
    except Exception as exc:  # noqa
        current_app.logger.error("Error creando notificación de contrato: %s", exc)
    # Volver a la página anterior (edición) y mostrar toasts
    ref = request.referrer
    fallback = url_for("prescriptors.edit_prescriptor", prescriptor_id=prescriptor_id)
    return redirect(ref or fallback)


@contracts_bp.get("/sign/prescriptor")
@login_required
def sign_prescriptor():
    token = request.args.get("token", "")
    prescriptor, err = _get_prescriptor_from_token_for_user(token, expected_role="prescriptor")
    if err:
        return err
    # Ir directo a la pantalla de dibujo de firma
    return redirect(url_for("contracts.sign_draw_get", token=token))


@contracts_bp.get("/sign/draw")
@login_required
def sign_draw_get():
    token = request.args.get("token", "")
    prescriptor, err = _get_prescriptor_from_token_for_user(token, expected_role="prescriptor")
    if err:
        return err
    return render_template("contracts/sign_draw.html", token=token, prescriptor=prescriptor)


@contracts_bp.post("/sign/draw")
@login_required
def sign_draw_post():
    token = request.form.get("token", "")
    prescriptor, err = _get_prescriptor_from_token_for_user(token, expected_role="prescriptor")
    if err:
        return err

    img_b64 = request.form.get("signature_data", "")
    if not img_b64.startswith("data:image/png;base64,"):
        flash("Firma inválida", "warning")
        return redirect(request.referrer or "/")

    prescriptor_id = getattr(prescriptor, "id", None)

    # Guardar PNG en static/contracts/signatures/
    from pathlib import Path
    import base64
    sig_dir = Path(current_app.root_path) / "static" / "contracts" / "signatures"
    sig_dir.mkdir(parents=True, exist_ok=True)
    sig_name = f"sig_prescriptor_{prescriptor_id}.png"
    sig_path = sig_dir / sig_name

    png_bytes = base64.b64decode(img_b64.split(",", 1)[1])
    sig_path.write_bytes(png_bytes)

    # Tomar contrato actual
    rel_url = getattr(prescriptor, "contract_url", None)
    if not rel_url:
        flash("No hay contrato base para firmar", "warning")
        return redirect("/")
    fname = os.path.basename(rel_url)
    input_pdf = Path(current_app.root_path) / "static" / "contracts" / fname
    if not input_pdf.exists():
        flash("Archivo de contrato no encontrado", "danger")
        return redirect("/")

    # Estampar firma manuscrita en el recuadro por defecto (x=200,y=120)
    stamped_name = f"presc_signed_{fname}"
    output_pdf = Path(current_app.root_path) / "static" / "contracts" / stamped_name
    try:
        # Estampar en la última página (6) - recuadro izquierdo (Prescriptor): x=80,y=160, w=200,h=40
        stamp_signature_image(input_pdf, sig_path, output_pdf, page=6, x=80, y=160, w=200, h=40)
    except Exception as exc:
        current_app.logger.exception("Error estampando firma manuscrita: %s", exc)
        flash("No se pudo estampar la firma", "danger")
        return redirect("/")

    # Sello visible informativo en el recuadro del prescriptor (texto y fecha)
    visible_name = f"presc_signed_visible_{fname}"
    visible_pdf = Path(current_app.root_path) / "static" / "contracts" / visible_name
    try:
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        presc_name = getattr(prescriptor, "squeeze_page_name", "") or getattr(prescriptor, "name", "Prescriptor")
        # Colocar el sello de texto por DEBAJO del recuadro del prescriptor (página 6)
        stamp_text_overlay(
            output_pdf,  # usar el PDF ya estampado con la imagen
            visible_pdf,
            [
                f"Firmado por {presc_name}",
                f"Fecha: {ts}",
                "con un certificado emitido por el SIGP",
            ],
            page=6,
            x=80,
            y=112,
            w=220,
            h=28,
        )
    except Exception as exc:
        current_app.logger.exception("Error creando sello visible para prescriptor: %s", exc)
        # si falla el sello visible, seguimos con el PDF con firma manuscrita
        prescriptor.contract_url = url_for("static", filename=f"contracts/{stamped_name}")
    else:
        prescriptor.contract_url = url_for("static", filename=f"contracts/{visible_name}")

    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception("Error guardando contrato con firma manuscrita: %s", exc)
        flash("Contrato firmado pero no se pudo guardar la URL", "warning")
        return redirect("/")

    # Generar link del presidente
    token_pres = _make_token(contract_id=str(prescriptor.id), role="president")
    link_pres = url_for("contracts.sign_president_get", token=token_pres, _external=True)
    # Notificar al presidente
    to_pres = current_app.config.get("PRESIDENT_EMAIL")
    if to_pres:
        try:
            # Cuerpo HTML a partir del template
            logo_url = url_for("static", filename="img/logos/SDC-logo.jpg", _external=True)
            html_body = render_template(
                "emails/president_sign_request.html",
                prescriptor=prescriptor,
                sign_link=link_pres,
                contract_url=getattr(prescriptor, "contract_url", None),
                logo_url=logo_url,
            )
            plain_body = (
                "Hola,\n\n"
                "Hay un contrato para firmar como Presidente. Accedé al siguiente enlace:\n"
                f"{link_pres}\n\n"
            )
            send_simple_mail(
                [to_pres],
                "Firma del Presidente requerida",
                html_body,
                html=True,
                text_body=plain_body,
            )
        except Exception:
            pass
    flash("Firma del prescriptor aplicada. Se notificó al presidente para su firma.", "success")
    _audit("prescriptor_signed", prescriptor.id, {"png": str(sig_path), "output": str(output_pdf)})
    # Mostrar una página de confirmación con próximos pasos
    return redirect(url_for("contracts.prescriptor_signed_confirmation"))


@contracts_bp.get("/sign/president")
@login_required
def sign_president_get():
    token = request.args.get("token", "")
    data = _read_token(token, current_app.config.get("SIGN_LINK_EXP_MINUTES", 60))
    if not data or data.get("r") != "president":
        flash("Enlace inválido o expirado", "warning")
        return redirect("/")
    prescriptor_id = data.get("c")
    Prescriptor = getattr(Base.classes, "prescriptors", None)
    if not Prescriptor:
        flash("Modelo prescriptors no disponible", "danger")
        return redirect("/")
    prescriptor = db.session.get(Prescriptor, prescriptor_id)
    if not prescriptor:
        flash("Prescriptor no encontrado", "warning")
        return redirect("/")
    # Mostrar página de dibujo de firma del presidente (flujo 1 paso)
    return render_template("contracts/sign_draw_president.html", token=token, prescriptor=prescriptor)


@contracts_bp.get("/signed/confirmation")
@login_required
def prescriptor_signed_confirmation():
    """Muestra una pantalla de confirmación tras la firma del prescriptor."""
    # Resolver URL de notificaciones si existe la ruta, para no depender de current_app en Jinja
    notifications_url = "/"
    try:
        notifications_url = url_for("list.my_notifications")
    except Exception:
        notifications_url = "/"
    return render_template("contracts/prescriptor_signed.html", notifications_url=notifications_url)


@contracts_bp.post("/sign/president")
@login_required
def sign_president_post():
    token = request.form.get("token", "")
    img_b64 = request.form.get("signature_data", "")
    data = _read_token(token, current_app.config.get("SIGN_LINK_EXP_MINUTES", 60))
    if not data or data.get("r") != "president":
        flash("Enlace inválido o expirado", "warning")
        return redirect("/")

    prescriptor_id = data.get("c")
    Prescriptor = getattr(Base.classes, "prescriptors", None)
    if not Prescriptor:
        flash("Modelo prescriptors no disponible", "danger")
        return redirect("/")
    prescriptor = db.session.get(Prescriptor, prescriptor_id)
    if not prescriptor:
        flash("Prescriptor no encontrado", "warning")
        return redirect("/")

    # Determinar PDF base a firmar: usar contract_url actual
    rel_url = getattr(prescriptor, "contract_url", None)
    if not rel_url:
        flash("No hay contrato base para firmar", "warning")
        return redirect("/")
    # convertir URL estática a ruta absoluta
    # contract_url suele ser "/static/contracts/<file>" o "static/contracts/<file>"
    from pathlib import Path
    fname = os.path.basename(rel_url)
    input_pdf = Path(current_app.root_path) / "static" / "contracts" / fname
    if not input_pdf.exists():
        flash("Archivo de contrato no encontrado", "danger")
        return redirect("/")

    # Requiere dibujo del presidente y estampado + sello visible, luego PAdES
    if not img_b64.startswith("data:image/png;base64,"):
        flash("Firma inválida: por favor dibujá tu firma.", "warning")
        return redirect(url_for("contracts.sign_president_get", token=token))

    # Guardar PNG del presidente
    from pathlib import Path as _P
    import base64 as _b64
    sig_dir = _P(current_app.root_path) / "static" / "contracts" / "signatures"
    sig_dir.mkdir(parents=True, exist_ok=True)
    sig_path = sig_dir / f"sig_president_{prescriptor.id}.png"
    png_bytes = _b64.b64decode(img_b64.split(",", 1)[1])
    sig_path.write_bytes(png_bytes)

    # Estampar la firma dibujada en el recuadro del presidente
    stamped_img_name = f"president_img_signed_{fname}"
    stamped_img_pdf = Path(current_app.root_path) / "static" / "contracts" / stamped_img_name
    try:
        # Estampar en la última página (6) - recuadro derecho (Presidente): x=320,y=160, w=200,h=40
        stamp_signature_image(input_pdf, sig_path, stamped_img_pdf, page=6, x=320, y=160, w=200, h=40)
    except Exception as exc:
        current_app.logger.exception("Error estampando firma del presidente: %s", exc)
        flash("No se pudo estampar la firma dibujada del presidente", "warning")
        return redirect(url_for("contracts.sign_president_get", token=token))

    # Sello visible informativo encima del recuadro del presidente
    visible_name = f"visible_{fname}"
    visible_pdf = Path(current_app.root_path) / "static" / "contracts" / visible_name
    try:
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        pres_name = current_app.config.get("PRESIDENT_DISPLAY_NAME", "Jesús Serrano Sanz")
        # Colocar el sello de texto por DEBAJO del recuadro del presidente
        stamp_text_overlay(
            stamped_img_pdf,
            visible_pdf,
            [f"Firmado por {pres_name}", f"Fecha: {ts}", "con un certificado emitido por el SIGP",],
            page=6,
            x=320,
            y=112,
            w=220,
            h=28,
        )
    except Exception as exc:
        current_app.logger.exception("Error creando sello visible: %s", exc)
        flash("No se pudo crear el sello visible de la firma del presidente", "warning")
        return redirect(url_for("contracts.sign_president_get", token=token))

    # Luego, firmar con PAdES el PDF con sello visible
    signed_name = f"signed_{fname}"
    output_pdf = Path(current_app.root_path) / "static" / "contracts" / signed_name

    # Validaciones previas de cert
    cert_path_cfg = current_app.config.get("PRESIDENT_CERT_PATH")
    if not cert_path_cfg:
        flash("Falta configurar PRESIDENT_CERT_PATH para firma PAdES", "danger")
        return redirect(url_for("contracts.sign_president_get", token=token))
    from pathlib import Path as _P
    cert_path = _P(cert_path_cfg if cert_path_cfg.startswith("/") else str(_P(current_app.root_path) / cert_path_cfg))
    if not cert_path.exists():
        flash("El certificado configurado no existe en la ruta indicada (PRESIDENT_CERT_PATH)", "danger")
        return redirect(url_for("contracts.sign_president_get", token=token))

    try:
        # Asegurar XMP/Info en el PDF visible antes de firmar
        try:
            pres_name = current_app.config.get("PRESIDENT_DISPLAY_NAME", "SIGP")
            presc_name = getattr(prescriptor, "squeeze_page_name", "") or getattr(prescriptor, "name", "Prescriptor")
            today = datetime.utcnow().strftime("%Y-%m-%d")
            title = f"Contrato de Prescripción - {presc_name} - {today}"
            subject = "Contrato de Prescripción"
            keywords = "contrato, prescripción, firma digital, PAdES"
            embed_pdf_metadata_xmp(
                visible_pdf,
                title=title,
                author=pres_name,
                subject=subject,
                keywords=keywords,
                creator="SIGP",
                producer="SIGP (INNOVA TRAINING CONSULTORIA Y FORMACION S.L.)",
            )
        except Exception:
            pass
        sign_pades(visible_pdf, output_pdf)
    except Exception as exc:  # noqa
        # Log detallado con traceback
        current_app.logger.exception("Error firmando PAdES: %s", exc)
        # Mensaje más informativo en UI: clase + mensaje y causa si existe
        err_cls = exc.__class__.__name__
        cause = getattr(exc, "__cause__", None) or getattr(exc, "__context__", None)
        ui_msg = f"{err_cls}: {exc}"
        if cause:
            ui_msg += f" | causa: {cause.__class__.__name__}: {cause}"
        flash(f"Error firmando el contrato (PAdES): {ui_msg}", "danger")
        return redirect(url_for("contracts.sign_president_get", token=token))

    final_url = url_for("static", filename=f"contracts/{signed_name}")
    final_url_abs = url_for("static", filename=f"contracts/{signed_name}", _external=True)
    prescriptor.contract_url = final_url

    # Intentar mover subestado a CAPACITACIÓN si existe
    try:
        Substate = getattr(Base.classes, "substate_prescriptor", None)
        if Substate and hasattr(prescriptor, "sub_state_id"):
            row = (
                db.session.query(Substate)
                .filter((getattr(Substate, "name").ilike("%CAPAC%")) | (getattr(Substate, "code", getattr(Substate, "name")).ilike("%CAPAC%")))
                .first()
            )
            if row:
                prescriptor.sub_state_id = row.id
    except Exception:
        pass

    try:
        db.session.commit()
        flash("Contrato firmado por Jesús Serrano Sanz (Presidente y Administrador Único)", "success")
        # Notificar al prescriptor (email HTML y notificación in-app)
        presc_email = getattr(prescriptor, "email", None) or getattr(prescriptor, "squeeze_page_email", None)
        # Fallback: usar email del usuario asociado si no hay email en el prescriptor
        if not presc_email:
            try:
                UserModel = getattr(Base.classes, "users", None)
            except Exception:
                UserModel = None
            if UserModel is not None and getattr(prescriptor, "user_id", None):
                u = db.session.get(UserModel, prescriptor.user_id)
                if u and getattr(u, "email", None):
                    presc_email = u.email
        try:
            # In-app notification (usar campos válidos)
            Notification = getattr(Base.classes, "notifications", None)
            if Notification is not None and getattr(prescriptor, "user_id", None):
                import uuid as _uuid
                notif = Notification(
                    id=str(_uuid.uuid4()),
                    user_id=prescriptor.user_id,
                    title="Contrato firmado por Jesús Serrano Sanz (Presidente y Administrador Único)",
                    body=f"Tu contrato ya fue firmado por Jesús Serrano Sanz (Presidente y Administrador Único).",
                    link_url=final_url_abs,
                    notif_type="INFO",
                    is_read=0,
                    created_at=datetime.utcnow(),
                )
                db.session.add(notif)
                db.session.commit()
        except Exception:
            db.session.rollback()
            pass
        if presc_email:
            try:
                # Reusar el template de capacitación
                from sigp.controllers.auth_controller import _generate_token
                platform_url = "https://sigp.eniit.es/"
                token = _generate_token(presc_email)
                reset_path = url_for("auth.reset_password", token=token)
                reset_url = platform_url.rstrip("/") + reset_path

                logo_url = url_for("static", filename="img/logos/SDC-logo.jpg", _external=True)
                html_body = render_template(
                    "emails/prescriptor_training.html",
                    platform_url=platform_url,
                    email=presc_email,
                    reset_url=reset_url,
                    contract_url=final_url_abs,
                )
                plain_body = (
                    "Hola!\n\n"
                    "Tu contrato ya fue firmado por Jesús Serrano Sanz (Presidente y Administrador Único) y tu cuenta está habilitada para la fase de capacitación.\n\n"
                    f"Plataforma: {platform_url}\nUsuario: {presc_email}\nRestablecer contraseña: {reset_url}\n\n"
                    f"Descargar contrato firmado: {final_url_abs}\n\n"
                    "En el menú verás el módulo Multimedia > Mis archivos con los recursos de capacitación (videos, links y archivos).\n\n"
                    "¡Éxitos en tu formación!"
                )
                mail_server = current_app.config.get("MAIL_SERVER")
                if not mail_server:
                    flash("Email NO enviado: MAIL_SERVER no está configurado", "warning")
                send_simple_mail(
                    [presc_email],
                    "Acceso a plataforma de capacitación",
                    html_body,
                    html=True,
                    text_body=plain_body,
                )
                if mail_server:
                    flash(f"Email enviado a {presc_email}", "info")
            except Exception as exc:
                current_app.logger.exception("Error enviando correo de notificación de firma del presidente: %s", exc)
                flash("No se pudo enviar el email al prescriptor", "warning")
        else:
            flash("No se envió email: el prescriptor no tiene email cargado", "warning")
        _audit("president_signed", prescriptor.id, {"output": str(output_pdf)})
        return redirect(url_for("prescriptors.edit_prescriptor", prescriptor_id=prescriptor_id))
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception("Error guardando contrato firmado: %s", exc)
        flash("Contrato firmado pero ocurrió un error al guardar", "warning")
        return redirect("/")


# @contracts_bp.get("/pades/diagnostic")
# @login_required
# def pades_diagnostic():
#     """Página de diagnóstico para verificar configuración PAdES."""
#     results = []
#     ok = True
#     pres_name = current_app.config.get("PRESIDENT_DISPLAY_NAME", "Jesús Serrano Sanz")
#     ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
#     cfg_path = current_app.config.get("PRESIDENT_CERT_PATH")
#     cfg_pass = current_app.config.get("PRESIDENT_CERT_PASS", "")
#     results.append({"label": "PRESIDENT_CERT_PATH", "value": cfg_path or "(vacío)"})
#     results.append({"label": "PRESIDENT_CERT_PASS", "value": "(definido)" if cfg_pass else "(vacío)"})

#     if not cfg_path:
#         ok = False
#         results.append({"label": "Archivo", "value": "No configurado"})
#         return render_template("contracts/pades_diagnostic.html", results=results, ok=ok, pres_name=pres_name, ts=ts)

#     # Resolver ruta absoluta
#     from pathlib import Path as _P
#     abs_path = _P(cfg_path if cfg_path.startswith("/") else str(_P(current_app.root_path) / cfg_path))
#     exists = abs_path.exists()
#     results.append({"label": "Ruta resuelta", "value": str(abs_path)})
#     results.append({"label": "Existe", "value": "sí" if exists else "no"})
#     if not exists:
#         ok = False
#         return render_template("contracts/pades_diagnostic.html", results=results, ok=ok, pres_name=pres_name, ts=ts)

#     # Intentar cargar el PKCS#12 con pyHanko
#     try:
#         from pyhanko.sign import signers
#         signer = signers.SimpleSigner.load_pkcs12(str(abs_path), passphrase=cfg_pass.encode() if cfg_pass else None)
#         # Si llegó aquí, carga ok
#         results.append({"label": "Carga PKCS#12", "value": "ok"})
#     except Exception as exc:  # noqa
#         ok = False
#         results.append({"label": "Carga PKCS#12", "value": f"ERROR: {exc}"})

#     return render_template("contracts/pades_diagnostic.html", results=results, ok=ok, pres_name=pres_name, ts=ts)

# @contracts_bp.get("/pades/diagnostic")
# @login_required
# def pades_diagnostic():
#     """Página de diagnóstico para verificar configuración PAdES."""
#     results = []
#     ok = True
#     pres_name = current_app.config.get("PRESIDENT_DISPLAY_NAME", "Jesús Serrano Sanz")
#     ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
#     cfg_path = current_app.config.get("PRESIDENT_CERT_PATH")
#     cfg_pass = current_app.config.get("PRESIDENT_CERT_PASS", "")
    
#     results.append({"label": "PRESIDENT_CERT_PATH", "value": cfg_path or "(vacío)"})
#     results.append({"label": "PRESIDENT_CERT_PASS", "value": "(definido)" if cfg_pass else "(vacío)"})

#     # Verificar dependencias
#     try:
#         import pyhanko
#         results.append({"label": "pyHanko versión", "value": getattr(pyhanko, '__version__', 'desconocida')})
#     except ImportError as exc:
#         ok = False
#         results.append({"label": "pyHanko", "value": f"ERROR: No instalado - {exc}"})
#         return render_template("contracts/pades_diagnostic.html", results=results, ok=ok, pres_name=pres_name, ts=ts)

#     try:
#         from cryptography import __version__ as crypto_version
#         results.append({"label": "cryptography versión", "value": crypto_version})
#     except ImportError:
#         results.append({"label": "cryptography", "value": "No disponible"})

#     if not cfg_path:
#         ok = False
#         results.append({"label": "Archivo", "value": "No configurado"})
#         return render_template("contracts/pades_diagnostic.html", results=results, ok=ok, pres_name=pres_name, ts=ts)

#     # Resolver ruta absoluta
#     from pathlib import Path as _P
#     abs_path = _P(cfg_path if cfg_path.startswith("/") else str(_P(current_app.root_path) / cfg_path))
#     exists = abs_path.exists()
#     results.append({"label": "Ruta resuelta", "value": str(abs_path)})
#     results.append({"label": "Existe", "value": "sí" if exists else "no"})
    
#     if not exists:
#         ok = False
#         return render_template("contracts/pades_diagnostic.html", results=results, ok=ok, pres_name=pres_name, ts=ts)

#     # Verificar tamaño del archivo
#     try:
#         file_size = abs_path.stat().st_size
#         results.append({"label": "Tamaño archivo", "value": f"{file_size} bytes"})
#         if file_size < 100:
#             ok = False
#             results.append({"label": "Tamaño", "value": "ERROR: Archivo muy pequeño"})
#     except Exception as exc:
#         ok = False
#         results.append({"label": "Stat archivo", "value": f"ERROR: {exc}"})

#     # Intentar cargar el PKCS#12 con pyHanko
#     try:
#         from pyhanko.sign import signers
#         passphrase = cfg_pass.encode('utf-8') if cfg_pass else None
#         signer = signers.SimpleSigner.load_pkcs12(str(abs_path), passphrase=passphrase)
        
#         if signer is None:
#             ok = False
#             results.append({"label": "Carga PKCS#12", "value": "ERROR: signer es None"})
#         else:
#             results.append({"label": "Carga PKCS#12", "value": "OK"})
            
#             # Verificar certificado de firma
#             if hasattr(signer, 'signing_cert') and signer.signing_cert:
#                 results.append({"label": "Certificado firma", "value": "OK"})
#                 try:
#                     subject = signer.signing_cert.subject
#                     results.append({"label": "Subject", "value": str(subject)})
#                 except Exception as exc:
#                     results.append({"label": "Subject", "value": f"ERROR: {exc}"})
                    
#                 try:
#                     not_after = signer.signing_cert.not_valid_after
#                     results.append({"label": "Válido hasta", "value": str(not_after)})
#                     if not_after < datetime.utcnow():
#                         ok = False
#                         results.append({"label": "Estado", "value": "ERROR: Certificado expirado"})
#                 except Exception as exc:
#                     results.append({"label": "Validez", "value": f"ERROR: {exc}"})
                    
#             else:
#                 ok = False
#                 results.append({"label": "Certificado firma", "value": "ERROR: signing_cert es None"})
            
#             # Verificar clave privada
#             if hasattr(signer, 'signing_key') and signer.signing_key:
#                 results.append({"label": "Clave privada", "value": "OK"})
#                 try:
#                     key_size = signer.signing_key.key_size
#                     results.append({"label": "Tamaño clave", "value": f"{key_size} bits"})
#                 except Exception as exc:
#                     results.append({"label": "Tamaño clave", "value": f"ERROR: {exc}"})
#             else:
#                 ok = False
#                 results.append({"label": "Clave privada", "value": "ERROR: signing_key es None"})
            
#             # Verificar registro de certificados
#             if hasattr(signer, 'cert_registry') and signer.cert_registry:
#                 results.append({"label": "Registro certificados", "value": "OK"})
#             else:
#                 results.append({"label": "Registro certificados", "value": "Advertencia: cert_registry es None"})
            
#     except Exception as exc:
#         ok = False
#         results.append({"label": "Carga PKCS#12", "value": f"ERROR: {exc}"})
#         # Debug adicional para errores específicos
#         if "invalid" in str(exc).lower():
#             results.append({"label": "Sugerencia", "value": "Verificar contraseña del certificado"})
#         elif "password" in str(exc).lower():
#             results.append({"label": "Sugerencia", "value": "Problema con la contraseña"})

#     return render_template("contracts/pades_diagnostic.html", results=results, ok=ok, pres_name=pres_name, ts=ts)

# @contracts_bp.get("/pades/diagnostic")
# @login_required
# def pades_diagnostic():
#     """Página de diagnóstico para verificar configuración PAdES."""
#     results = []
#     ok = True
#     pres_name = current_app.config.get("PRESIDENT_DISPLAY_NAME", "Jesús Serrano Sanz")
#     ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
#     cfg_path = current_app.config.get("PRESIDENT_CERT_PATH")
#     cfg_pass = current_app.config.get("PRESIDENT_CERT_PASS", "")
    
#     results.append({"label": "PRESIDENT_CERT_PATH", "value": cfg_path or "(vacío)"})
#     results.append({"label": "PRESIDENT_CERT_PASS", "value": "(definido)" if cfg_pass else "(vacío)"})

#     # Verificar dependencias
#     try:
#         import pyhanko
#         pyhanko_version = getattr(pyhanko, '__version__', 'desconocida')
#         results.append({"label": "pyHanko versión", "value": pyhanko_version})
        
#         # Verificar si es una versión conocida problemática
#         if pyhanko_version == 'desconocida':
#             results.append({"label": "Advertencia", "value": "Versión de pyHanko no detectable"})
#     except ImportError as exc:
#         ok = False
#         results.append({"label": "pyHanko", "value": f"ERROR: No instalado - {exc}"})
#         return render_template("contracts/pades_diagnostic.html", results=results, ok=ok, pres_name=pres_name, ts=ts)

#     try:
#         from cryptography import __version__ as crypto_version
#         results.append({"label": "cryptography versión", "value": crypto_version})
#     except ImportError:
#         results.append({"label": "cryptography", "value": "No disponible"})

#     if not cfg_path:
#         ok = False
#         results.append({"label": "Archivo", "value": "No configurado"})
#         return render_template("contracts/pades_diagnostic.html", results=results, ok=ok, pres_name=pres_name, ts=ts)

#     # Resolver ruta absoluta
#     from pathlib import Path as _P
#     abs_path = _P(cfg_path if cfg_path.startswith("/") else str(_P(current_app.root_path) / cfg_path))
#     exists = abs_path.exists()
#     results.append({"label": "Ruta resuelta", "value": str(abs_path)})
#     results.append({"label": "Existe", "value": "sí" if exists else "no"})
    
#     if not exists:
#         ok = False
#         return render_template("contracts/pades_diagnostic.html", results=results, ok=ok, pres_name=pres_name, ts=ts)

#     # Verificar tamaño del archivo
#     try:
#         file_size = abs_path.stat().st_size
#         results.append({"label": "Tamaño archivo", "value": f"{file_size} bytes"})
#         if file_size < 100:
#             ok = False
#             results.append({"label": "Tamaño", "value": "ERROR: Archivo muy pequeño"})
#     except Exception as exc:
#         ok = False
#         results.append({"label": "Stat archivo", "value": f"ERROR: {exc}"})

#     # Intentar cargar el PKCS#12 con pyHanko
#     try:
#         from pyhanko.sign import signers
#         passphrase = cfg_pass.encode('utf-8') if cfg_pass else None
#         results.append({"label": "Intentando carga con", "value": "contraseña definida" if passphrase else "sin contraseña"})
        
#         signer = signers.SimpleSigner.load_pkcs12(str(abs_path), passphrase=passphrase)
        
#         if signer is None:
#             # Intentar variaciones de contraseña
#             results.append({"label": "Primer intento", "value": "FALLÓ - signer es None"})
            
#             if passphrase is not None:
#                 results.append({"label": "Intentando sin contraseña", "value": "..."})
#                 signer = signers.SimpleSigner.load_pkcs12(str(abs_path), passphrase=None)
                
#             if signer is None and passphrase is None and cfg_pass:
#                 results.append({"label": "Intentando con cadena vacía", "value": "..."})
#                 signer = signers.SimpleSigner.load_pkcs12(str(abs_path), passphrase=b'')
                
#             if signer is None:
#                 ok = False
#                 results.append({"label": "Carga PKCS#12", "value": "ERROR: Todas las combinaciones de contraseña fallaron"})
#                 results.append({"label": "Sugerencias", "value": "1) Verificar contraseña, 2) Regenerar certificado, 3) Verificar formato P12"})
#                 return render_template("contracts/pades_diagnostic.html", results=results, ok=ok, pres_name=pres_name, ts=ts)
        
#         results.append({"label": "Carga PKCS#12", "value": "OK"})
        
#         # Verificar certificado de firma
#         if hasattr(signer, 'signing_cert') and signer.signing_cert:
#             results.append({"label": "Certificado firma", "value": "OK"})
#             try:
#                 subject = signer.signing_cert.subject
#                 results.append({"label": "Subject", "value": str(subject)})
                
#                 # Extraer nombre común si existe
#                 for attr in subject:
#                     if attr.oid._name == 'commonName':
#                         results.append({"label": "Nombre Común", "value": str(attr.value)})
#                         break
                        
#             except Exception as exc:
#                 results.append({"label": "Subject", "value": f"ERROR: {exc}"})
                
#             try:
#                 not_before = signer.signing_cert.not_valid_before
#                 not_after = signer.signing_cert.not_valid_after
#                 now = datetime.utcnow()
#                 results.append({"label": "Válido desde", "value": str(not_before)})
#                 results.append({"label": "Válido hasta", "value": str(not_after)})
                
#                 if now < not_before:
#                     ok = False
#                     results.append({"label": "Estado", "value": "ERROR: Certificado aún no válido"})
#                 elif now > not_after:
#                     ok = False
#                     results.append({"label": "Estado", "value": "ERROR: Certificado expirado"})
#                 else:
#                     days_left = (not_after - now).days
#                     results.append({"label": "Estado", "value": f"VÁLIDO ({days_left} días restantes)"})
                    
#             except Exception as exc:
#                 results.append({"label": "Validez", "value": f"ERROR: {exc}"})
                
#         else:
#             ok = False
#             results.append({"label": "Certificado firma", "value": "ERROR: signing_cert es None"})
        
#         # Verificar clave privada
#         if hasattr(signer, 'signing_key') and signer.signing_key:
#             results.append({"label": "Clave privada", "value": "OK"})
#             try:
#                 key_size = signer.signing_key.key_size
#                 results.append({"label": "Tamaño clave", "value": f"{key_size} bits"})
#                 if key_size < 2048:
#                     results.append({"label": "Advertencia", "value": "Clave menor a 2048 bits puede ser insegura"})
#             except Exception as exc:
#                 results.append({"label": "Tamaño clave", "value": f"ERROR: {exc}"})
#         else:
#             ok = False
#             results.append({"label": "Clave privada", "value": "ERROR: signing_key es None"})
        
#         # Verificar registro de certificados
#         if hasattr(signer, 'cert_registry') and signer.cert_registry:
#             try:
#                 cert_count = len(signer.cert_registry)
#                 results.append({"label": "Registro certificados", "value": f"OK ({cert_count} certificados)"})
#             except:
#                 results.append({"label": "Registro certificados", "value": "OK"})
#         else:
#             results.append({"label": "Registro certificados", "value": "Advertencia: cert_registry es None"})
        
#         # Test final: verificar método crítico
#         if hasattr(signer, 'get_signature_mechanism_for_digest'):
#             results.append({"label": "Método crítico", "value": "get_signature_mechanism_for_digest OK"})
#         else:
#             ok = False
#             results.append({"label": "Método crítico", "value": "ERROR: get_signature_mechanism_for_digest no existe"})
        
#     except Exception as exc:
#         ok = False
#         results.append({"label": "Carga PKCS#12", "value": f"ERROR: {exc}"})
#         # Debug adicional para errores específicos
#         exc_str = str(exc).lower()
#         if "invalid" in exc_str or "bad decrypt" in exc_str:
#             results.append({"label": "Causa probable", "value": "Contraseña incorrecta"})
#         elif "password" in exc_str:
#             results.append({"label": "Causa probable", "value": "Problema con la contraseña"})
#         elif "asn1" in exc_str or "der" in exc_str:
#             results.append({"label": "Causa probable", "value": "Formato de certificado inválido"})
#         else:
#             results.append({"label": "Causa probable", "value": "Certificado corrupto o incompatible"})

#     return render_template("contracts/pades_diagnostic.html", results=results, ok=ok, pres_name=pres_name, ts=ts)

@contracts_bp.get("/pades/diagnostic")
@login_required
def pades_diagnostic():
    """Página de diagnóstico para verificar configuración PAdES."""
    results = []
    ok = True
    pres_name = current_app.config.get("PRESIDENT_DISPLAY_NAME", "Jesús Serrano Sanz")
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    cfg_path = current_app.config.get("PRESIDENT_CERT_PATH")
    cfg_pass = current_app.config.get("PRESIDENT_CERT_PASS", "")
    
    results.append({"label": "PRESIDENT_CERT_PATH", "value": cfg_path or "(vacío)"})
    results.append({"label": "PRESIDENT_CERT_PASS", "value": "(definido)" if cfg_pass else "(vacío)"})

    # Verificar dependencias
    try:
        import pyhanko
        pyhanko_version = getattr(pyhanko, '__version__', 'desconocida')
        results.append({"label": "pyHanko versión", "value": pyhanko_version})
        
        # Verificar si es una versión conocida problemática
        if pyhanko_version == 'desconocida':
            results.append({"label": "Advertencia", "value": "Versión de pyHanko no detectable"})
    except ImportError as exc:
        ok = False
        results.append({"label": "pyHanko", "value": f"ERROR: No instalado - {exc}"})
        return render_template("contracts/pades_diagnostic.html", results=results, ok=ok, pres_name=pres_name, ts=ts)

    try:
        from cryptography import __version__ as crypto_version
        results.append({"label": "cryptography versión", "value": crypto_version})
    except ImportError:
        results.append({"label": "cryptography", "value": "No disponible"})

    if not cfg_path:
        ok = False
        results.append({"label": "Archivo", "value": "No configurado"})
        return render_template("contracts/pades_diagnostic.html", results=results, ok=ok, pres_name=pres_name, ts=ts)

    # Resolver ruta absoluta
    from pathlib import Path as _P
    abs_path = _P(cfg_path if cfg_path.startswith("/") else str(_P(current_app.root_path) / cfg_path))
    exists = abs_path.exists()
    results.append({"label": "Ruta resuelta", "value": str(abs_path)})
    results.append({"label": "Existe", "value": "sí" if exists else "no"})
    
    if not exists:
        ok = False
        return render_template("contracts/pades_diagnostic.html", results=results, ok=ok, pres_name=pres_name, ts=ts)

    # Verificar tamaño del archivo
    try:
        file_size = abs_path.stat().st_size
        results.append({"label": "Tamaño archivo", "value": f"{file_size} bytes"})
        if file_size < 100:
            ok = False
            results.append({"label": "Tamaño", "value": "ERROR: Archivo muy pequeño"})
    except Exception as exc:
        ok = False
        results.append({"label": "Stat archivo", "value": f"ERROR: {exc}"})

    # Intentar cargar el PKCS#12 con pyHanko
    try:
        from pyhanko.sign import signers
        passphrase = cfg_pass.encode('utf-8') if cfg_pass else None
        results.append({"label": "Intentando carga con", "value": "contraseña definida" if passphrase else "sin contraseña"})
        
        signer = signers.SimpleSigner.load_pkcs12(str(abs_path), passphrase=passphrase)
        
        if signer is None:
            # Intentar variaciones de contraseña
            results.append({"label": "Primer intento", "value": "FALLÓ - signer es None"})
            
            if passphrase is not None:
                results.append({"label": "Intentando sin contraseña", "value": "..."})
                signer = signers.SimpleSigner.load_pkcs12(str(abs_path), passphrase=None)
                
            if signer is None and passphrase is None and cfg_pass:
                results.append({"label": "Intentando con cadena vacía", "value": "..."})
                signer = signers.SimpleSigner.load_pkcs12(str(abs_path), passphrase=b'')
                
            if signer is None:
                ok = False
                results.append({"label": "Carga PKCS#12", "value": "ERROR: Todas las combinaciones de contraseña fallaron"})
                results.append({"label": "Sugerencias", "value": "1) Verificar contraseña, 2) Regenerar certificado, 3) Verificar formato P12"})
                return render_template("contracts/pades_diagnostic.html", results=results, ok=ok, pres_name=pres_name, ts=ts)
        
        results.append({"label": "Carga PKCS#12", "value": "OK"})
        
        # Verificar certificado de firma
        if hasattr(signer, 'signing_cert') and signer.signing_cert:
            results.append({"label": "Certificado firma", "value": "OK"})
            try:
                subject = signer.signing_cert.subject
                results.append({"label": "Subject", "value": str(subject)})
                
                # Extraer nombre común si existe
                for attr in subject:
                    if attr.oid._name == 'commonName':
                        results.append({"label": "Nombre Común", "value": str(attr.value)})
                        break
                        
            except Exception as exc:
                results.append({"label": "Subject", "value": f"ERROR: {exc}"})
                
            try:
                not_before = signer.signing_cert.not_valid_before
                not_after = signer.signing_cert.not_valid_after
                now = datetime.utcnow()
                results.append({"label": "Válido desde", "value": str(not_before)})
                results.append({"label": "Válido hasta", "value": str(not_after)})
                
                if now < not_before:
                    ok = False
                    results.append({"label": "Estado", "value": "ERROR: Certificado aún no válido"})
                elif now > not_after:
                    ok = False
                    results.append({"label": "Estado", "value": "ERROR: Certificado expirado"})
                else:
                    days_left = (not_after - now).days
                    results.append({"label": "Estado", "value": f"VÁLIDO ({days_left} días restantes)"})
                    
            except Exception as exc:
                results.append({"label": "Validez", "value": f"ERROR: {exc}"})
                
        else:
            ok = False
            results.append({"label": "Certificado firma", "value": "ERROR: signing_cert es None"})
        
        # Verificar clave privada
        if hasattr(signer, 'signing_key') and signer.signing_key:
            results.append({"label": "Clave privada", "value": "OK"})
            try:
                key_size = signer.signing_key.key_size
                results.append({"label": "Tamaño clave", "value": f"{key_size} bits"})
                if key_size < 2048:
                    results.append({"label": "Advertencia", "value": "Clave menor a 2048 bits puede ser insegura"})
            except Exception as exc:
                results.append({"label": "Tamaño clave", "value": f"ERROR: {exc}"})
        else:
            ok = False
            results.append({"label": "Clave privada", "value": "ERROR: signing_key es None"})
        
        # Verificar registro de certificados
        if hasattr(signer, 'cert_registry') and signer.cert_registry:
            try:
                cert_count = len(signer.cert_registry)
                results.append({"label": "Registro certificados", "value": f"OK ({cert_count} certificados)"})
            except:
                results.append({"label": "Registro certificados", "value": "OK"})
        else:
            results.append({"label": "Registro certificados", "value": "Advertencia: cert_registry es None"})
        
        # Test final: verificar método crítico
        if hasattr(signer, 'get_signature_mechanism_for_digest'):
            results.append({"label": "Método crítico", "value": "get_signature_mechanism_for_digest OK"})
        else:
            ok = False
            results.append({"label": "Método crítico", "value": "ERROR: get_signature_mechanism_for_digest no existe"})
        
    except Exception as exc:
        ok = False
        results.append({"label": "Carga PKCS#12", "value": f"ERROR: {exc}"})
        # Debug adicional para errores específicos
        exc_str = str(exc).lower()
        if "invalid" in exc_str or "bad decrypt" in exc_str:
            results.append({"label": "Causa probable", "value": "Contraseña incorrecta"})
        elif "password" in exc_str:
            results.append({"label": "Causa probable", "value": "Problema con la contraseña"})
        elif "asn1" in exc_str or "der" in exc_str:
            results.append({"label": "Causa probable", "value": "Formato de certificado inválido"})
        else:
            results.append({"label": "Causa probable", "value": "Certificado corrupto o incompatible"})

    return render_template("contracts/pades_diagnostic.html", results=results, ok=ok, pres_name=pres_name, ts=ts)