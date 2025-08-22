import os
import hashlib
from datetime import datetime
from pathlib import Path
from flask import current_app
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def _contracts_dir() -> Path:
    base = current_app.config.get("CONTRACT_UPLOAD_FOLDER")
    if isinstance(base, str):
        base = Path(current_app.root_path) / base
    base.mkdir(parents=True, exist_ok=True)
    return base


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def generate_contract_pdf(prescriptor, filename: str | None = None) -> Path:
    """
    Genera un PDF base del contrato con datos mínimos del prescriptor.
    Devuelve la ruta absoluta del PDF.
    """
    out_dir = _contracts_dir()
    if not filename:
        filename = f"contract_{getattr(prescriptor, 'id', 'unknown')}.pdf"
    out_path = out_dir / filename

    # Datos básicos
    name = getattr(prescriptor, "squeeze_page_name", "") or getattr(prescriptor, "name", "")
    email = getattr(prescriptor, "email", "")
    today = datetime.utcnow().strftime("%Y-%m-%d")

    c = canvas.Canvas(str(out_path), pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, height - 72, "Contrato de Prescripción")

    c.setFont("Helvetica", 11)
    c.drawString(72, height - 110, f"Fecha: {today}")
    c.drawString(72, height - 130, f"Prescriptor: {name}")
    if email:
        c.drawString(72, height - 150, f"Email: {email}")

    # Clausulas simples (placeholder)
    text = c.beginText(72, height - 190)
    text.setFont("Helvetica", 10)
    text.textLines(
        """
El presente contrato vincula al Prescriptor con la entidad.\n\n
Cláusula 1: Objeto del contrato...\n\n
Cláusula 2: Obligaciones...\n\n
Cláusula 3: Confidencialidad...\n\n
Cláusula 4: Duración y terminación...\n\n
""".strip()
    )
    c.drawText(text)

    # Áreas de firma (visuales)
    c.setFont("Helvetica", 10)
    c.drawString(72, 140, "Firma del Prescriptor:")
    c.rect(200, 120, 200, 40)  # caja visible

    c.drawString(72, 80, "Firma del Presidente:")
    c.rect(200, 60, 200, 40)

    c.showPage()
    c.save()

    return out_path


def stamp_signature_image(input_pdf: Path, signature_png: Path, output_pdf: Path,
                           page: int = 1, x: int = 200, y: int = 120, w: int = 200, h: int = 40) -> None:
    """
    TODO: Estampar imagen de firma manuscrita sobre el PDF (overlay).
    Implementaremos con pypdf o reportlab+merge en iteración siguiente.
    Por ahora, dejaremos un NotImplementedError para evitar falsas expectativas.
    """
    raise NotImplementedError("stamp_signature_image aún no implementado")


def sign_pades(input_pdf: Path, output_pdf: Path) -> None:
    """
    TODO: Firmar PDF con pyHanko usando P12 o PKCS#11, configurable por env.
    """
    raise NotImplementedError("PAdES con pyHanko aún no implementado")
