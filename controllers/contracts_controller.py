from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash
from flask_login import login_required
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from sigp import db
from sigp.models import Base
from sigp.services.contract_service import generate_contract_pdf, sha256_file, sign_pades, stamp_signature_image
from sigp.common.email_utils import send_simple_mail
import uuid
from datetime import datetime
import os

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


def _audit(event: str, prescriptor_id: str | int, extra: dict | None = None):
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


@contracts_bp.post("/<prescriptor_id>/generate")
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

    # Crear registro básico en memory (usaremos tabla luego con migración)
    # Por ahora solo generamos PDF base y mostramos link.
    pdf_path = generate_contract_pdf(prescriptor, filename=f"contract_{prescriptor.id}.pdf")
    pdf_hash = sha256_file(pdf_path)

    # Guardar URL en prescriptor para facilitar pruebas iniciales
    rel_url = url_for("static", filename=f"contracts/{os.path.basename(pdf_path)}")
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
    if presc_email:
        try:
            send_simple_mail(
                [presc_email],
                "Contrato disponible para firma",
                f"Hola, podés firmar tu contrato en: {link}",
            )
        except Exception:
            pass
    _audit("contract_generated", prescriptor.id, {"pdf": str(pdf_path), "sha256": pdf_hash})
    return render_template(
        "contracts/generate_done.html",
        contract_url=rel_url,
        sha256=pdf_hash,
        sign_link=link,
        sign_link_president=link_pres,
    )


@contracts_bp.get("/sign/prescriptor")
@login_required
def sign_prescriptor():
    token = request.args.get("token", "")
    data = _read_token(token, current_app.config.get("SIGN_LINK_EXP_MINUTES", 60))
    if not data or data.get("r") != "prescriptor":
        flash("Enlace inválido o expirado", "warning")
        return redirect("/")
    return render_template("contracts/sign_choice.html", token=token)


@contracts_bp.get("/sign/draw")
@login_required
def sign_draw_get():
    token = request.args.get("token", "")
    data = _read_token(token, current_app.config.get("SIGN_LINK_EXP_MINUTES", 60))
    if not data or data.get("r") != "prescriptor":
        flash("Enlace inválido o expirado", "warning")
        return redirect("/")
    return render_template("contracts/sign_draw.html", token=token)


@contracts_bp.post("/sign/draw")
@login_required
def sign_draw_post():
    token = request.form.get("token", "")
    data = _read_token(token, current_app.config.get("SIGN_LINK_EXP_MINUTES", 60))
    if not data or data.get("r") != "prescriptor":
        flash("Enlace inválido o expirado", "warning")
        return redirect("/")

    img_b64 = request.form.get("signature_data", "")
    if not img_b64.startswith("data:image/png;base64,"):
        flash("Firma inválida", "warning")
        return redirect(request.referrer or "/")

    prescriptor_id = data.get("c")
    Prescriptor = getattr(Base.classes, "prescriptors", None)
    if not Prescriptor:
        flash("Modelo prescriptors no disponible", "danger")
        return redirect("/")
    prescriptor = db.session.get(Prescriptor, prescriptor_id)
    if not prescriptor:
        flash("Prescriptor no encontrado", "warning")
        return redirect("/")

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
        stamp_signature_image(input_pdf, sig_path, output_pdf, page=1, x=200, y=120, w=200, h=40)
    except Exception as exc:
        current_app.logger.exception("Error estampando firma manuscrita: %s", exc)
        flash("No se pudo estampar la firma", "danger")
        return redirect("/")

    prescriptor.contract_url = url_for("static", filename=f"contracts/{stamped_name}")

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
            send_simple_mail([to_pres], "Prescripción: firma del presidente requerida", f"Firmar en: {link_pres}")
        except Exception:
            pass
    flash("Firma del prescriptor aplicada", "success")
    _audit("prescriptor_signed", prescriptor.id, {"png": str(sig_path), "output": str(output_pdf)})
    return redirect(link_pres)


@contracts_bp.get("/sign/president")
@login_required
def sign_president_get():
    token = request.args.get("token", "")
    data = _read_token(token, current_app.config.get("SIGN_LINK_EXP_MINUTES", 60))
    if not data or data.get("r") != "president":
        flash("Enlace inválido o expirado", "warning")
        return redirect("/")
    return render_template("contracts/sign_president.html", token=token)


@contracts_bp.post("/sign/president")
@login_required
def sign_president_post():
    token = request.form.get("token", "")
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

    signed_name = f"signed_{fname}"
    output_pdf = Path(current_app.root_path) / "static" / "contracts" / signed_name

    try:
        sign_pades(input_pdf, output_pdf)
    except Exception as exc:  # noqa
        current_app.logger.exception("Error firmando PAdES: %s", exc)
        flash("Error firmando el contrato (PAdES)", "danger")
        return redirect("/")

    final_url = url_for("static", filename=f"contracts/{signed_name}")
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
        flash("Contrato firmado por el presidente", "success")
        # Notificar al prescriptor
        presc_email = getattr(prescriptor, "email", None) or getattr(prescriptor, "squeeze_page_email", None)
        if presc_email:
            try:
                send_simple_mail([presc_email], "Contrato firmado", f"Tu contrato firmado está disponible en: {final_url}")
            except Exception:
                pass
        _audit("president_signed", prescriptor.id, {"output": str(output_pdf)})
        return redirect(url_for("prescriptors.edit_prescriptor", prescriptor_id=prescriptor_id))
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception("Error guardando contrato firmado: %s", exc)
        flash("Contrato firmado pero ocurrió un error al guardar", "warning")
        return redirect("/")
