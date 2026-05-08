"""Utility to send simple emails using SMTP settings from Flask config.
Moved from sigp.email_utils to sigp.common.email_utils.
"""
from __future__ import annotations

import smtplib
from email.utils import formatdate, make_msgid
from email.message import EmailMessage
from typing import Sequence, Optional
from flask import current_app


def send_simple_mail(to: Sequence[str], subject: str, body: str, *, html: bool=False, text_body: Optional[str]=None) -> None:
    if not to:
        return
    cfg = current_app.config
    server = cfg.get("MAIL_SERVER")
    if not server:
        current_app.logger.warning("MAIL_SERVER not configured; email not sent to %s", to)
        return
    port = cfg.get("MAIL_PORT", 587)
    username = cfg.get("MAIL_USERNAME")
    password = cfg.get("MAIL_PASSWORD")
    use_tls = cfg.get("MAIL_USE_TLS", True)
    use_ssl = cfg.get("MAIL_USE_SSL", False)
    sender = cfg.get("MAIL_DEFAULT_SENDER", username)

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(to)
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=(sender or "sigp").split("@")[-1])
    if html:
        # plain text fallback
        msg.set_content(text_body or "Este email requiere un cliente compatible con HTML.")
        msg.add_alternative(body, subtype='html')
    else:
        msg.set_content(body)

    try:
        if use_ssl:
            smtp = smtplib.SMTP_SSL(server, port, timeout=10)
        else:
            smtp = smtplib.SMTP(server, port, timeout=10)
        with smtp as s:
            if use_tls and not use_ssl:
                s.starttls()
            if username and password:
                s.login(username, password)
            refused = s.send_message(msg)
        if refused:
            current_app.logger.warning("SMTP refused recipients for %r: %s", subject, refused)
        else:
            current_app.logger.info(
                "Sent email %r from %s to %s message_id=%s",
                subject,
                sender,
                to,
                msg["Message-ID"],
            )
    except Exception as exc:  # pylint: disable=broad-except
        current_app.logger.error("Failed to send email to %s: %s", to, exc)


def build_contract_signing_email_text(
    *,
    language: str,
    name: str,
    email: str,
    platform_base: str,
    reset_url: str | None,
    sign_link: str,
    contract_url: str | None,
) -> tuple[str, str]:
    lang = (language or "Español").strip().lower()
    is_en = lang in {"inglés", "ingles", "english"}
    is_pt = lang in {"portugués", "portugues", "portuguese"}

    if is_en:
        subject = "Welcome to the Prescriber Program - Next steps"
        body = (
            f"Hello {name},\n\n"
            "Welcome to the Prescriber Program!\n\n"
            "Step 1: Set your password\n"
            f"- Password setup link: {reset_url or '(not available)'}\n\n"
            "Step 2: Access your account\n"
            f"- URL: {platform_base}/\n"
            f"- User: {email}\n\n"
            "Step 3: Sign your prescriber agreement\n"
            f"- Signing link: {sign_link}\n"
            + (f"- Download agreement: {contract_url}\n\n" if contract_url else "\n\n") +
            "IMPORTANT:\n"
            "Please read the agreement carefully before signing it. If you have any questions, contact the prescription manager at sigp@sportsdatacampus.com before proceeding with the signature.\n\n"
            "Once you have signed the agreement, you will receive a new email with the instructions and next steps.\n\n"
            "Need help? Reply to this email and we will assist you.\n"
        )
    elif is_pt:
        subject = "Bem-vindo ao Programa de Prescritores - Próximos passos"
        body = (
            f"Olá {name},\n\n"
            "Bem-vindo ao Programa de Prescritores!\n\n"
            "Passo 1: Defina sua senha\n"
            f"- Link para definir a senha: {reset_url or '(não disponível)'}\n\n"
            "Passo 2: Acesse sua conta\n"
            f"- URL: {platform_base}/\n"
            f"- Usuário: {email}\n\n"
            "Passo 3: Assine seu acordo de prescritor\n"
            f"- Link para assinar: {sign_link}\n"
            + (f"- Baixar acordo: {contract_url}\n\n" if contract_url else "\n\n") +
            "IMPORTANTE:\n"
            "Leia atentamente o acordo antes de assiná-lo. Se tiver alguma dúvida, entre em contato com o responsável pela prescrição pelo email sigp@sportsdatacampus.com antes de prosseguir com a assinatura.\n\n"
            "Depois de assinar o acordo, você receberá um novo email com as instruções e os próximos passos.\n\n"
            "Precisa de ajuda? Responda este email e nós o ajudaremos.\n"
        )
    else:
        subject = "¡Bienvenido al Programa de Prescriptores - Demos los primeros pasos."
        body = (
            f"Hola {name},\n\n"
            "¡Te damos la bienvenida al Programa de Prescriptores!\n\n"
            "Paso 1: Establece tu contraseña\n"
            f"- Enlace para establecer contraseña: {reset_url or '(no disponible)'}\n\n"
            "Paso 2: Accede a tu cuenta\n"
            f"- URL: {platform_base}/\n"
            f"- Usuario: {email}\n\n"
            "Paso 3: Firma tu convenio de prescriptor\n"
            f"- Enlace para firmar: {sign_link}\n"
            + (f"- Descargar convenio: {contract_url}\n\n" if contract_url else "\n\n") +
            "IMPORTANTE:\n"
            "Te recomendamos leer atentamente el convenio antes de firmarlo. Si tienes alguna duda, por favor ponte en contacto con el responsable de prescripción escribiendo a sigp@sportsdatacampus.com antes de proceder con la firma.\n\n"
            "Una vez que hayas firmado el convenio, recibirás un nuevo correo electrónico con las instrucciones y los siguientes pasos.\n\n"
            "¿Necesitas ayuda adicional? Responde este correo y te asistiremos.\n"
        )

    return subject, body
