"""Utility to send simple emails using SMTP settings from Flask config.
Moved from sigp.email_utils to sigp.common.email_utils.
"""
from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Sequence
from flask import current_app


def send_simple_mail(to: Sequence[str], subject: str, body: str, *, html: bool=False, text_body: str | None=None) -> None:
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
            s.send_message(msg)
        current_app.logger.info("Sent lead notification email to %s", to)
    except Exception as exc:  # pylint: disable=broad-except
        current_app.logger.error("Failed to send email to %s: %s", to, exc)
