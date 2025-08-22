from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash
from flask_login import login_required
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from sigp import db
from sigp.models import Base
from sigp.services.contract_service import generate_contract_pdf, sha256_file
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
    token = _make_token(contract_id=str(prescriptor.id), role="prescriptor")
    link = url_for("contracts.sign_prescriptor", token=token, _external=True)

    flash("Contrato generado", "success")
    return render_template("contracts/generate_done.html", contract_url=rel_url, sha256=pdf_hash, sign_link=link)


@contracts_bp.get("/sign/prescriptor")
@login_required
def sign_prescriptor():
    token = request.args.get("token", "")
    data = _read_token(token, current_app.config.get("SIGN_LINK_EXP_MINUTES", 60))
    if not data or data.get("r") != "prescriptor":
        flash("Enlace inválido o expirado", "warning")
        return redirect("/")
    return render_template("contracts/sign_choice.html", token=token)
