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
    """Superpone una imagen PNG de firma sobre el PDF en la página indicada.
    page es 1-based en este API; internamente se convierte a 0-based.
    Coordenadas x,y están en puntos PDF (origen inferior izquierdo).
    """
    from tempfile import NamedTemporaryFile
    from pypdf import PdfReader, PdfWriter

    # Crear un PDF de overlay con la imagen en la posición deseada
    with NamedTemporaryFile(suffix="_overlay.pdf", delete=False) as tmp:
        overlay_path = Path(tmp.name)
    try:
        # Determinar tamaño de página del input para el overlay
        reader = PdfReader(str(input_pdf))
        target_index = max(0, page - 1)
        target_index = min(target_index, len(reader.pages) - 1)
        mediabox = reader.pages[target_index].mediabox
        width = float(mediabox.width)
        height = float(mediabox.height)

        c = canvas.Canvas(str(overlay_path), pagesize=(width, height))
        # Dibujar la imagen (ajustar a w x h)
        c.drawImage(str(signature_png), x, y, width=w, height=h, mask='auto')
        c.showPage()
        c.save()

        # Fusionar overlay con la página destino
        overlay_reader = PdfReader(str(overlay_path))
        overlay_page = overlay_reader.pages[0]

        writer = PdfWriter()
        for i, pg in enumerate(reader.pages):
            new_page = pg
            if i == target_index:
                # merge_page modifica in place
                new_page.merge_page(overlay_page)
            writer.add_page(new_page)

        with open(output_pdf, "wb") as outf:
            writer.write(outf)
    finally:
        try:
            overlay_path.unlink(missing_ok=True)
        except Exception:
            pass


def sign_pades(input_pdf: Path, output_pdf: Path) -> None:
    """Firma el PDF con PAdES-BES usando el certificado P12 configurado.
    Si se configura PKCS#11 en el futuro, se puede ampliar.
    """
    from pyhanko.sign import signers
    from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter

    p12_path = current_app.config.get("PRESIDENT_CERT_PATH")
    p12_pass = current_app.config.get("PRESIDENT_CERT_PASS", "")
    if not p12_path:
        raise RuntimeError("PRESIDENT_CERT_PATH no configurado")

    p12_bytes = Path(current_app.root_path, p12_path).read_bytes() if not p12_path.startswith("/") else Path(p12_path).read_bytes()
    signer = signers.SimpleSigner.load_pkcs12(p12_bytes, passphrase=p12_pass.encode() if p12_pass else None)

    with open(input_pdf, "rb") as inf:
        w = IncrementalPdfFileWriter(inf)
        meta = signers.PdfSignatureMetadata()  # firma invisible
        with open(output_pdf, "wb") as outf:
            signers.PdfSigner(meta, signer=signer).sign_pdf(w, output=outf)
