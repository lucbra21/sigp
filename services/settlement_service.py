from __future__ import annotations

from datetime import datetime
from typing import List, Sequence, Optional, Any
from pathlib import Path

from flask import current_app as app
from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError

import uuid
from sigp import db
from sigp.models import Base

# Tablas reflejadas
Invoice = getattr(Base.classes, "invoice", None)
Ledger = getattr(Base.classes, "ledger", None)
LeadHistory = getattr(Base.classes, "lead_history", None)
Notification = getattr(Base.classes, "notifications", None)
Prescriptor = getattr(Base.classes, "prescriptor", None) or getattr(Base.classes, "prescriptors", None)


class SettlementError(RuntimeError):
    """Errores de negocio o BD al rendir facturas."""


def _notify_prescriptor(prescriptor_id, text: str) -> None:
    """Crea una notificación interna para el prescriptor (si la tabla existe)."""
    if Notification is None:
        return
    # obtener user_id asociado al prescriptor
    user_id = prescriptor_id  # por si ya es user_id
    if Prescriptor is not None:
        pres = db.session.get(Prescriptor, prescriptor_id)
        if pres is not None and getattr(pres, "user_id", None):
            user_id = pres.user_id
        else:
            # si no hay usuario asociado, no crear notificación
            return

    notif = Notification(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title="Rendición de facturas",
        body=text,
        created_at=datetime.utcnow(),
        is_read=0,
        notif_type="INFO",
    )
    db.session.add(notif)


def _send_mail(prescriptor_email: str, subject: str, body: str, attachment: Optional[Path]) -> None:
    """Envía email mediante SMTP nativo. Si falla, registra error en log"""
    import smtplib
    from email.message import EmailMessage

    host = app.config.get("MAIL_SERVER")
    port = app.config.get("MAIL_PORT")
    username = app.config.get("MAIL_USERNAME")
    password = app.config.get("MAIL_PASSWORD")
    use_ssl = app.config.get("MAIL_USE_SSL", True)

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = app.config.get("MAIL_DEFAULT_SENDER", username)
    msg["To"] = prescriptor_email
    msg.set_content(body)
    if attachment and attachment.exists():
        maintype = "application"
        subtype = "octet-stream"
        if attachment.suffix.lower() in {".pdf"}:
            maintype, subtype = "application", "pdf"
        elif attachment.suffix.lower() in {".jpg", ".jpeg"}:
            maintype, subtype = "image", "jpeg"
        elif attachment.suffix.lower() == ".png":
            maintype, subtype = "image", "png"
        msg.add_attachment(attachment.read_bytes(), filename=attachment.name, maintype=maintype, subtype=subtype)
    try:
        if use_ssl:
            with smtplib.SMTP_SSL(host, port) as smtp:
                smtp.login(username, password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(host, port) as smtp:
                smtp.starttls()
                smtp.login(username, password)
                smtp.send_message(msg)
    except Exception as e:
        app.logger.warning("No se pudo enviar email a %s: %s", prescriptor_email, e)


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def settle_invoices(invoice_ids: Sequence[int], paid_amounts: Sequence[str | float], receipt_filename: Optional[str] = None) -> None:
    """Marca las facturas como rendidas.

    Args:
        invoice_ids: lista de ids de invoices a rendir.
        paid_amounts: importes pagados correspondientes (mismo orden).
        receipt_filename: nombre del archivo guardado en carpeta RECEIPT_UPLOAD_FOLDER.
    """
    if Invoice is None or Ledger is None:
        raise SettlementError("Tablas invoice / ledger no disponibles")

    now = datetime.utcnow()
    receipt_path = None
    if receipt_filename:
        receipt_path = str(receipt_filename)

    try:
        for inv_id, amt in zip(invoice_ids, paid_amounts):
            invoice: Any = db.session.get(Invoice, inv_id)
            if invoice is None:
                continue
            invoice.paid_at = now
            invoice.receipt_path = receipt_path
            invoice.paid_amount = amt or invoice.total

            # actualizar ledger(s) relacionados
            db.session.execute(
                update(Ledger).where(Ledger.invoice_id == invoice.id).values(state_id=4)
            )

            # lead_history
            if LeadHistory is not None and hasattr(invoice, "lead_id"):
                lh = LeadHistory(
                    id=None,
                    lead_id=invoice.lead_id,
                    ts=now,
                    action="STATE_CHANGE",
                    notes="Factura rendida",
                )
                db.session.add(lh)

        # notificación + email (usar primer invoice para info)
        first_invoice: Any = db.session.get(Invoice, invoice_ids[0])
        if first_invoice and hasattr(first_invoice, "prescriptor_id"):
            prescriptor_id = first_invoice.prescriptor_id
            prescriptor = db.session.get(Prescriptor, prescriptor_id) if Prescriptor else None
            email = getattr(prescriptor, "email", None) if prescriptor else None

            _notify_prescriptor(prescriptor_id, "Tus facturas han sido rendidas.")
            if email:
                _send_mail(
                    email,
                    "Rendición de facturas",
                    f"Se han rendido las facturas: {', '.join(map(str, invoice_ids))}.",
                    Path(receipt_path) if receipt_path else None,
                )
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        app.logger.exception("Fallo BD al rendir facturas")
        raise SettlementError("No se pudo completar la rendición") from e
