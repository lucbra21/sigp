import os
import hashlib
from datetime import datetime
from pathlib import Path
from flask import current_app
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from typing import Optional

# Importamos los constructores (Asegúrate de crear los archivos en el paso 3)
from sigp.services.builders import hibrida_builder_es
from sigp.services.builders import hibrida_builder_en
from sigp.services.builders import juridica_builder_es
from sigp.services.builders import juridica_builder_en
from sigp.services.builders import tutor_builder_es
from sigp.services.builders import tutor_builder_en
from sigp.services.builders import alumno_builder_es
from sigp.services.builders import alumno_builder_en
from sigp.services.builders import externo_builder_es
from sigp.services.builders import externo_builder_en

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

def generate_contract_pdf(prescriptor, filename: Optional[str] = None) -> Path:
    """Orquestador principal: Dirige el tráfico sin lógica comercial."""
    out_dir = _contracts_dir()
    if not filename:
        filename = f"contract_{getattr(prescriptor, 'id', 'unknown')}.pdf"
    out_path = out_dir / filename

    # 1. Variables de enrutamiento
    idioma = getattr(prescriptor, "language", "Español")
    categoria = getattr(prescriptor, "agreement_category", "Persona Hibrida")

    # 2. Datos básicos comunes (SIN lógica de comisiones ni programas)
    datos_contrato = {
        "idioma": idioma,
        "width": A4[0],
        "height": A4[1],
        "today": datetime.utcnow().strftime("%Y-%m-%d"),
        "name": getattr(prescriptor, "squeeze_page_name", "") or getattr(prescriptor, "name", "PRESCRIPTOR"),
        "email": getattr(prescriptor, "email", ""),
        "doc_type": (getattr(prescriptor, "document_type", None) or "DNI").strip(),
        "doc_num": (getattr(prescriptor, "document_number", None) or "__________").strip(),
        "domicile": (getattr(prescriptor, "domicile", None) or "__________________________").strip(),
        "ciudad": current_app.config.get("CONTRACT_CITY", "Valladolid")
    }

    c = canvas.Canvas(str(out_path), pagesize=A4)
    
    # Metadatos del PDF
    org_name = current_app.config.get("PRESIDENT_DISPLAY_NAME", "SIGP")
    title = f"Contrato - {datos_contrato['name']} - {datos_contrato['today']}"
    c.setTitle(title)
    c.setAuthor(org_name)
    c.setSubject(f"Contrato - {categoria}")
    c.setCreator("SIGP")

    # 3. Despachador (Routing)
    if categoria == 'Persona juridica - institucional':
        if idioma == 'Inglés':
            juridica_builder_en.build(c, prescriptor, datos_contrato)
        else:
            juridica_builder_es.build(c, prescriptor, datos_contrato)
    elif categoria == 'Persona Tutor':
        if idioma == 'Inglés':
            tutor_builder_en.build(c, prescriptor, datos_contrato)
        else:
            tutor_builder_es.build(c, prescriptor, datos_contrato)
    elif categoria == 'Persona Alumno':
        if idioma == 'Inglés':
            alumno_builder_en.build(c, prescriptor, datos_contrato)
        else:
            alumno_builder_es.build(c, prescriptor, datos_contrato)
    elif categoria == 'Prescriptor Externo':
        if idioma == 'Inglés':
            externo_builder_en.build(c, prescriptor, datos_contrato)
        else:
            externo_builder_es.build(c, prescriptor, datos_contrato)
    else:
        if idioma == 'Inglés':
            hibrida_builder_en.build(c, prescriptor, datos_contrato)
        else:
            hibrida_builder_es.build(c, prescriptor, datos_contrato)

    c.save()

    # 4. Metadatos XMP
    try:
        embed_pdf_metadata_xmp(
            out_path,
            title=title,
            author=org_name,
            subject=f"Contrato - {categoria}",
            keywords="contrato, prescripción, firma digital, PAdES",
            creator="SIGP",
            producer="SIGP (INNOVA TRAINING CONSULTORIA Y FORMACION S.L.)",
        )
    except Exception as e:
        current_app.logger.error(f"Error metadatos: {e}")

    return out_path


# =====================================================================
# CONSTRUCTORES ESPECÍFICOS DE CONTRATOS (PATRÓN STRATEGY)
# =====================================================================

def _build_hibrida_es(c, prescriptor, datos):
    """
    Constructor para el contrato estándar (Persona Híbrida / Español).
    Este contiene la lógica visual que ya tenías validada.
    """
    # Helpers locales de dibujo (puedes sacarlos a funciones globales si prefieres)
    def draw_paragraph(text, x, y, width_px, font="Helvetica", size=11, leading=16):
        c.setFont(font, size)
        # Lógica simplificada de envoltura para este ejemplo
        c.drawString(x, y, text[:100]) # Aquí iría tu función wrap_text completa
        return y - leading

    width = datos["width"]
    height = datos["height"]
    margin_x = 72
    monto_comision = datos["monto_comision"]
    nombre_prog = datos["nombre_prog"]
    
    # --- PÁGINA 1 ---
    y_cursor = height - 120
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin_x, y_cursor, "ACUERDO DE COLABORACIÓN (PERSONA HÍBRIDA)")
    
    y_clausulas = y_cursor - 60
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin_x, y_clausulas, "SEGUNDA. – Sistema de Comisiones")
    y_clausulas -= 20

    texto_comision = (
        f"EL COLABORADOR percibirá una comisión fija de {monto_comision} € por cada matrícula "
        f"confirmada en {nombre_prog}. Esta comisión es neta e incluye cualquier impuesto aplicable."
    )
    # Llama a tu helper draw_paragraph real aquí
    c.setFont("Helvetica", 11)
    c.drawString(margin_x, y_clausulas, texto_comision) 

    # --- PÁGINA 2 ---
    c.showPage()
    y = height - 130
    c.setFont("Helvetica-Bold", 13)
    c.drawString(margin_x, y, "Condiciones de Devengo y Pago")
    y -= 22
    
    c.setFont("Helvetica", 11)
    c.drawString(margin_x, y, f"• Pago Único: Se abonará el 100% de la comisión ({monto_comision} €).")
    y -= 16
    c.drawString(margin_x, y, "• Momento del Pago: La comisión se devengará íntegramente al momento")
    y -= 16
    c.drawString(margin_x + 10, y, "del pago efectivo de la MATRÍCULA por parte del alumno.")
    
    # ... (Resto de tu lógica de dibujo original para páginas 3 a 6) ...
    # Asegúrate de incluir los recuadros de firma en la última página
    y_sig_base = 150
    c.setFont("Helvetica", 10)
    c.drawString(80, y_sig_base + 65, "Firma del Prescriptor:")
    c.rect(80, y_sig_base, 220, 55)
    c.drawString(320, y_sig_base + 65, "Firma del Presidente:")
    c.rect(320, y_sig_base, 220, 55)

# --- SKELETONS PARA LOS DEMÁS CONTRATOS ---

def _build_hibrida_en(c, prescriptor, datos):
    """
    Constructor para el contrato estándar (Persona Híbrida / Español).
    Este contiene la lógica visual que ya tenías validada.
    """
    # Helpers locales de dibujo (puedes sacarlos a funciones globales si prefieres)
    def draw_paragraph(text, x, y, width_px, font="Helvetica", size=11, leading=16):
        c.setFont(font, size)
        # Lógica simplificada de envoltura para este ejemplo
        c.drawString(x, y, text[:100]) # Aquí iría tu función wrap_text completa
        return y - leading

    width = datos["width"]
    height = datos["height"]
    margin_x = 72
    monto_comision = datos["monto_comision"]
    nombre_prog = datos["nombre_prog"]
    
    # --- PÁGINA 1 ---
    y_cursor = height - 120
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 800, "COLLABORATION AGREEMENT (HYBRID PERSON)")
    
    # ... (Resto de tu lógica de dibujo original para páginas 3 a 6) ...
    # Asegúrate de incluir los recuadros de firma en la última página
    y_sig_base = 150
    c.setFont("Helvetica", 10)
    c.drawString(80, y_sig_base + 65, "Firma del Prescriptor:")
    c.rect(80, y_sig_base, 220, 55)
    c.drawString(320, y_sig_base + 65, "Firma del Presidente:")
    c.rect(320, y_sig_base, 220, 55)

def _build_juridica_es(c, prescriptor, datos):
    """
    Constructor para el contrato estándar (Persona Híbrida / Español).
    Este contiene la lógica visual que ya tenías validada.
    """
    # Helpers locales de dibujo (puedes sacarlos a funciones globales si prefieres)
    def draw_paragraph(text, x, y, width_px, font="Helvetica", size=11, leading=16):
        c.setFont(font, size)
        # Lógica simplificada de envoltura para este ejemplo
        c.drawString(x, y, text[:100]) # Aquí iría tu función wrap_text completa
        return y - leading

    width = datos["width"]
    height = datos["height"]
    margin_x = 72
    monto_comision = datos["monto_comision"]
    nombre_prog = datos["nombre_prog"]
    
    # --- PÁGINA 1 ---
    y_cursor = height - 120
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 800, "ACUERDO DE COLABORACIÓN (PERSONA JURÍDICA)")
    
    # ... (Resto de tu lógica de dibujo original para páginas 3 a 6) ...
    # Asegúrate de incluir los recuadros de firma en la última página
    y_sig_base = 150
    c.setFont("Helvetica", 10)
    c.drawString(80, y_sig_base + 65, "Firma del Prescriptor:")
    c.rect(80, y_sig_base, 220, 55)
    c.drawString(320, y_sig_base + 65, "Firma del Presidente:")
    c.rect(320, y_sig_base, 220, 55)

def _build_juridica_en(c, prescriptor, datos):
    """
    Constructor para el contrato estándar (Persona Híbrida / Español).
    Este contiene la lógica visual que ya tenías validada.
    """
    # Helpers locales de dibujo (puedes sacarlos a funciones globales si prefieres)
    def draw_paragraph(text, x, y, width_px, font="Helvetica", size=11, leading=16):
        c.setFont(font, size)
        # Lógica simplificada de envoltura para este ejemplo
        c.drawString(x, y, text[:100]) # Aquí iría tu función wrap_text completa
        return y - leading

    width = datos["width"]
    height = datos["height"]
    margin_x = 72
    monto_comision = datos["monto_comision"]
    nombre_prog = datos["nombre_prog"]
    
    # --- PÁGINA 1 ---
    y_cursor = height - 120
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 800, "ACUERDO DE COLABORACIÓN (PERSONA JURÍDICA en)")
    
    # ... (Resto de tu lógica de dibujo original para páginas 3 a 6) ...
    # Asegúrate de incluir los recuadros de firma en la última página
    y_sig_base = 150
    c.setFont("Helvetica", 10)
    c.drawString(80, y_sig_base + 65, "Firma del Prescriptor:")
    c.rect(80, y_sig_base, 220, 55)
    c.drawString(320, y_sig_base + 65, "Firma del Presidente:")
    c.rect(320, y_sig_base, 220, 55)

def _build_tutor_es(c, prescriptor, datos):
    """
    Constructor para el contrato estándar (Persona Híbrida / Español).
    Este contiene la lógica visual que ya tenías validada.
    """
    # Helpers locales de dibujo (puedes sacarlos a funciones globales si prefieres)
    def draw_paragraph(text, x, y, width_px, font="Helvetica", size=11, leading=16):
        c.setFont(font, size)
        # Lógica simplificada de envoltura para este ejemplo
        c.drawString(x, y, text[:100]) # Aquí iría tu función wrap_text completa
        return y - leading

    width = datos["width"]
    height = datos["height"]
    margin_x = 72
    monto_comision = datos["monto_comision"]
    nombre_prog = datos["nombre_prog"]
    
    # --- PÁGINA 1 ---
    y_cursor = height - 120
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 800, "ACUERDO DE COLABORACIÓN (TUTOR)")
    
    # ... (Resto de tu lógica de dibujo original para páginas 3 a 6) ...
    # Asegúrate de incluir los recuadros de firma en la última página
    y_sig_base = 150
    c.setFont("Helvetica", 10)
    c.drawString(80, y_sig_base + 65, "Firma del Prescriptor:")
    c.rect(80, y_sig_base, 220, 55)
    c.drawString(320, y_sig_base + 65, "Firma del Presidente:")
    c.rect(320, y_sig_base, 220, 55)

def _build_tutor_en(c, prescriptor, datos):
    """
    Constructor para el contrato estándar (Persona Híbrida / Español).
    Este contiene la lógica visual que ya tenías validada.
    """
    # Helpers locales de dibujo (puedes sacarlos a funciones globales si prefieres)
    def draw_paragraph(text, x, y, width_px, font="Helvetica", size=11, leading=16):
        c.setFont(font, size)
        # Lógica simplificada de envoltura para este ejemplo
        c.drawString(x, y, text[:100]) # Aquí iría tu función wrap_text completa
        return y - leading

    width = datos["width"]
    height = datos["height"]
    margin_x = 72
    monto_comision = datos["monto_comision"]
    nombre_prog = datos["nombre_prog"]
    
    # --- PÁGINA 1 ---
    y_cursor = height - 120
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 800, "ACUERDO DE COLABORACIÓN (TUTOR EN)")
    
    # ... (Resto de tu lógica de dibujo original para páginas 3 a 6) ...
    # Asegúrate de incluir los recuadros de firma en la última página
    y_sig_base = 150
    c.setFont("Helvetica", 10)
    c.drawString(80, y_sig_base + 65, "Firma del Prescriptor:")
    c.rect(80, y_sig_base, 220, 55)
    c.drawString(320, y_sig_base + 65, "Firma del Presidente:")
    c.rect(320, y_sig_base, 220, 55)

def _build_alumno_es(c, prescriptor, datos):
    
    """
    Constructor para el contrato estándar (Persona Híbrida / Español).
    Este contiene la lógica visual que ya tenías validada.
    """
    # Helpers locales de dibujo (puedes sacarlos a funciones globales si prefieres)
    def draw_paragraph(text, x, y, width_px, font="Helvetica", size=11, leading=16):
        c.setFont(font, size)
        # Lógica simplificada de envoltura para este ejemplo
        c.drawString(x, y, text[:100]) # Aquí iría tu función wrap_text completa
        return y - leading

    width = datos["width"]
    height = datos["height"]
    margin_x = 72
    monto_comision = datos["monto_comision"]
    nombre_prog = datos["nombre_prog"]
    
    # --- PÁGINA 1 ---
    y_cursor = height - 120
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 800, "ACUERDO DE COLABORACIÓN (ALUMNO)")
    
    # ... (Resto de tu lógica de dibujo original para páginas 3 a 6) ...
    # Asegúrate de incluir los recuadros de firma en la última página
    y_sig_base = 150
    c.setFont("Helvetica", 10)
    c.drawString(80, y_sig_base + 65, "Firma del Prescriptor:")
    c.rect(80, y_sig_base, 220, 55)
    c.drawString(320, y_sig_base + 65, "Firma del Presidente:")
    c.rect(320, y_sig_base, 220, 55)

def _build_alumno_en(c, prescriptor, datos):
    """
    Constructor para el contrato estándar (Persona Híbrida / Español).
    Este contiene la lógica visual que ya tenías validada.
    """
    # Helpers locales de dibujo (puedes sacarlos a funciones globales si prefieres)
    def draw_paragraph(text, x, y, width_px, font="Helvetica", size=11, leading=16):
        c.setFont(font, size)
        # Lógica simplificada de envoltura para este ejemplo
        c.drawString(x, y, text[:100]) # Aquí iría tu función wrap_text completa
        return y - leading

    width = datos["width"]
    height = datos["height"]
    margin_x = 72
    monto_comision = datos["monto_comision"]
    nombre_prog = datos["nombre_prog"]
    
    # --- PÁGINA 1 ---
    y_cursor = height - 120
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 800, "ACUERDO DE COLABORACIÓN (ALUMNO EN)")
    
    # ... (Resto de tu lógica de dibujo original para páginas 3 a 6) ...
    # Asegúrate de incluir los recuadros de firma en la última página
    y_sig_base = 150
    c.setFont("Helvetica", 10)
    c.drawString(80, y_sig_base + 65, "Firma del Prescriptor:")
    c.rect(80, y_sig_base, 220, 55)
    c.drawString(320, y_sig_base + 65, "Firma del Presidente:")
    c.rect(320, y_sig_base, 220, 55)

def _build_externo_es(c, prescriptor, datos):
    
    """
    Constructor para el contrato estándar (Persona Híbrida / Español).
    Este contiene la lógica visual que ya tenías validada.
    """
    # Helpers locales de dibujo (puedes sacarlos a funciones globales si prefieres)
    def draw_paragraph(text, x, y, width_px, font="Helvetica", size=11, leading=16):
        c.setFont(font, size)
        # Lógica simplificada de envoltura para este ejemplo
        c.drawString(x, y, text[:100]) # Aquí iría tu función wrap_text completa
        return y - leading

    width = datos["width"]
    height = datos["height"]
    margin_x = 72
    monto_comision = datos["monto_comision"]
    nombre_prog = datos["nombre_prog"]
    
    # --- PÁGINA 1 ---
    y_cursor = height - 120
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 800, "ACUERDO DE COLABORACIÓN (PRESCRIPTOR EXTERNO)")
    
    # ... (Resto de tu lógica de dibujo original para páginas 3 a 6) ...
    # Asegúrate de incluir los recuadros de firma en la última página
    y_sig_base = 150
    c.setFont("Helvetica", 10)
    c.drawString(80, y_sig_base + 65, "Firma del Prescriptor:")
    c.rect(80, y_sig_base, 220, 55)
    c.drawString(320, y_sig_base + 65, "Firma del Presidente:")
    c.rect(320, y_sig_base, 220, 55)

def _build_externo_en(c, prescriptor, datos):
    """
    Constructor para el contrato estándar (Persona Híbrida / Español).
    Este contiene la lógica visual que ya tenías validada.
    """
    # Helpers locales de dibujo (puedes sacarlos a funciones globales si prefieres)
    def draw_paragraph(text, x, y, width_px, font="Helvetica", size=11, leading=16):
        c.setFont(font, size)
        # Lógica simplificada de envoltura para este ejemplo
        c.drawString(x, y, text[:100]) # Aquí iría tu función wrap_text completa
        return y - leading

    width = datos["width"]
    height = datos["height"]
    margin_x = 72
    monto_comision = datos["monto_comision"]
    nombre_prog = datos["nombre_prog"]
    
    # --- PÁGINA 1 ---
    y_cursor = height - 120
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, 800, "ACUERDO DE COLABORACIÓN (PRESCRIPTOR EXTERNO EN)")
    
    # ... (Resto de tu lógica de dibujo original para páginas 3 a 6) ...
    # Asegúrate de incluir los recuadros de firma en la última página
    y_sig_base = 150
    c.setFont("Helvetica", 10)
    c.drawString(80, y_sig_base + 65, "Firma del Prescriptor:")
    c.rect(80, y_sig_base, 220, 55)
    c.drawString(320, y_sig_base + 65, "Firma del Presidente:")
    c.rect(320, y_sig_base, 220, 55)

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

        # Conservar metadatos del documento original (Title, Author, etc.)
        try:
            if reader.metadata:
                writer.add_metadata(dict(reader.metadata))
        except Exception:
            pass

        with open(output_pdf, "wb") as outf:
            writer.write(outf)
    finally:
        try:
            overlay_path.unlink(missing_ok=True)
        except Exception:
            pass

def embed_pdf_metadata_xmp(pdf_path: Path, *, title: str, author: str, subject: str, keywords: str,
                           creator: str, producer: str) -> None:
    """Escribe metadatos en DocInfo y XMP para máxima compatibilidad."""
    from pikepdf import Pdf, Name, Dictionary
    from pikepdf import String as _Str
    from datetime import datetime as _dt

    def _pdf_date(dt: _dt) -> str:
        return dt.strftime("D:%Y%m%d%H%M%SZ")

    now = _dt.utcnow()
    with Pdf.open(str(pdf_path)) as pdf:
        info = pdf.docinfo or Dictionary()
        info[Name('/Title')] = _Str(title)
        info[Name('/Author')] = _Str(author)
        info[Name('/Subject')] = _Str(subject)
        info[Name('/Keywords')] = _Str(keywords)
        info[Name('/Creator')] = _Str(creator)
        info[Name('/Producer')] = _Str(producer)
        info[Name('/CreationDate')] = _Str(_pdf_date(now))
        info[Name('/ModDate')] = _Str(_pdf_date(now))
        pdf.docinfo = info

        # XMP básico (Dublin Core + xmp:CreateDate/ModifyDate)
        xmp = f"""
<?xpacket begin='﻿' id='W5M0MpCehiHzreSzNTczkc9d'?>
<x:xmpmeta xmlns:x='adobe:ns:meta/'>
  <rdf:RDF xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'
           xmlns:dc='http://purl.org/dc/elements/1.1/'
           xmlns:xmp='http://ns.adobe.com/xap/1.0/'
           xmlns:pdf='http://ns.adobe.com/pdf/1.3/'>
    <rdf:Description rdf:about=''
      dc:title='{title}'
      dc:creator='{author}'
      dc:description='{subject}'
      pdf:Keywords='{keywords}'
      xmp:CreatorTool='{creator}'>
      <xmp:CreateDate>{now.isoformat()}Z</xmp:CreateDate>
      <xmp:ModifyDate>{now.isoformat()}Z</xmp:ModifyDate>
      <pdf:Producer>{producer}</pdf:Producer>
    </rdf:Description>
  </rdf:RDF>
 </x:xmpmeta>
<?xpacket end='w'?>
""".strip()
        pdf.Root.Metadata = pdf.make_stream(xmp.encode('utf-8'))
        pdf.save(str(pdf_path))


def stamp_text_overlay(input_pdf: Path, output_pdf: Path, text_lines: list[str],
                       page: int = 1, x: int = 200, y: int = 60, w: int = 200, h: int = 40) -> None:
    """Dibuja texto dentro del recuadro indicado y lo fusiona sobre el PDF.
    Ideal para indicar "Firmado digitalmente" en el recuadro del presidente.
    """
    from tempfile import NamedTemporaryFile
    from pypdf import PdfReader, PdfWriter

    # Crear overlay con el texto, ajustado al ancho del recuadro
    with NamedTemporaryFile(suffix="_overlay.pdf", delete=False) as tmp:
        overlay_path = Path(tmp.name)
    try:
        reader = PdfReader(str(input_pdf))
        target_index = max(0, page - 1)
        target_index = min(target_index, len(reader.pages) - 1)
        mediabox = reader.pages[target_index].mediabox
        width = float(mediabox.width)
        height = float(mediabox.height)

        c = canvas.Canvas(str(overlay_path), pagesize=(width, height))
        # Dibujar un marco tenue opcional
        c.setStrokeColorRGB(0.4, 0.4, 0.4)
        # c.rect(x, y, w, h, stroke=1, fill=0)

        # Escribir texto centrado en el recuadro
        c.setFont("Helvetica", 9)
        line_height = 12
        total_text_height = line_height * len(text_lines)
        start_y = y + (h - total_text_height) / 2 + (len(text_lines) - 1) * line_height
        for i, line in enumerate(text_lines):
            tw = c.stringWidth(line, "Helvetica", 9)
            tx = x + (w - tw) / 2
            ty = start_y - i * line_height
            c.drawString(tx, ty, line)

        c.showPage()
        c.save()

        overlay_reader = PdfReader(str(overlay_path))
        overlay_page = overlay_reader.pages[0]

        writer = PdfWriter()
        for i, pg in enumerate(reader.pages):
            new_page = pg
            if i == target_index:
                new_page.merge_page(overlay_page)
            writer.add_page(new_page)

        # Conservar metadatos del documento original (Title, Author, etc.)
        try:
            if reader.metadata:
                writer.add_metadata(dict(reader.metadata))
        except Exception:
            pass

        with open(output_pdf, "wb") as outf:
            writer.write(outf)
    finally:
        try:
            overlay_path.unlink(missing_ok=True)
        except Exception:
            pass

def sign_pades(input_pdf: Path, output_pdf: Path) -> None:
    """Firma el PDF con PAdES-BES usando el certificado P12 configurado."""
    from pyhanko.sign import signers
    from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
    from pyhanko.sign.general import SigningError
    import traceback

    p12_path = current_app.config.get("PRESIDENT_CERT_PATH")
    p12_pass = current_app.config.get("PRESIDENT_CERT_PASS", "")
    
    if not p12_path:
        raise RuntimeError("PRESIDENT_CERT_PATH no configurado")

    # Resolver ruta absoluta
    if p12_path.startswith("/"):
        p12_abs = Path(p12_path)
    else:
        p12_abs = Path(current_app.root_path) / p12_path
    
    if not p12_abs.exists():
        raise RuntimeError(f"Certificado P12 no encontrado en: {p12_abs}")
    
    current_app.logger.info(f"Cargando certificado desde: {p12_abs}")
    
    # Debug información antes de cargar
    current_app.logger.info(f"=== DEBUG CERTIFICADO ===")
    current_app.logger.info(f"Ruta configurada: {p12_path}")
    current_app.logger.info(f"Ruta resuelta: {p12_abs}")
    current_app.logger.info(f"Archivo existe: {p12_abs.exists()}")
    current_app.logger.info(f"Tamaño archivo: {p12_abs.stat().st_size if p12_abs.exists() else 'N/A'} bytes")
    current_app.logger.info(f"Contraseña configurada: {'SÍ' if p12_pass else 'NO'}")
    
    # Cargar certificado con validaciones exhaustivas
    signer = None
    try:
        passphrase = p12_pass.encode('utf-8') if p12_pass else None
        current_app.logger.info(f"Intentando cargar P12 con passphrase: {'DEFINIDA' if passphrase else 'NONE'}")
        
        signer = signers.SimpleSigner.load_pkcs12(str(p12_abs), passphrase=passphrase)
        
        if signer is None:
            # Intentar sin contraseña si falló con contraseña
            if passphrase is not None:
                current_app.logger.warning("Fallo con contraseña, intentando sin contraseña")
                signer = signers.SimpleSigner.load_pkcs12(str(p12_abs), passphrase=None)
            
            # Intentar con contraseña vacía si falló sin contraseña
            if signer is None and passphrase is None and p12_pass:
                current_app.logger.warning("Fallo sin contraseña, intentando con string vacío")
                signer = signers.SimpleSigner.load_pkcs12(str(p12_abs), passphrase=b'')
            
            if signer is None:
                raise RuntimeError(
                    f"SimpleSigner.load_pkcs12 retornó None. "
                    f"Archivo: {p12_abs} "
                    f"(existe: {p12_abs.exists()}, tamaño: {p12_abs.stat().st_size if p12_abs.exists() else 0} bytes). "
                    f"Contraseña: {'configurada' if p12_pass else 'no configurada'}. "
                    f"Posibles causas: contraseña incorrecta, certificado corrupto o formato inválido."
                )
        
        # Validaciones críticas
        if not hasattr(signer, 'signing_cert') or signer.signing_cert is None:
            raise RuntimeError(f"El certificado {p12_abs} no tiene signing_cert válido")
            
        if not hasattr(signer, 'signing_key') or signer.signing_key is None:
            raise RuntimeError(f"El certificado {p12_abs} no tiene signing_key válida")
        
        current_app.logger.info(f"Certificado cargado exitosamente - Subject: {signer.signing_cert.subject}")
        
    except Exception as exc:
        current_app.logger.error(f"Error detallado cargando P12 desde {p12_abs}: {exc}")
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        raise RuntimeError(f"Fallo cargando certificado desde {p12_abs}: {exc}")

    # Intentar firma con manejo robusto de errores
    try:
        current_app.logger.info("Abriendo PDF para firma")
        with open(input_pdf, "rb") as inf:
            w = IncrementalPdfFileWriter(inf)
            
            # Metadatos más básicos para evitar problemas
            meta = signers.PdfSignatureMetadata(
                field_name="PresidentSignature",
                md_algorithm="sha256",
                location="Valladolid, España",
                reason="Firma del Presidente",
            )
            
            current_app.logger.info("Creando PdfSigner")
            
            # Validar antes de crear PdfSigner
            if not hasattr(signer, 'get_signature_mechanism_for_digest'):
                current_app.logger.error("El signer no tiene el método get_signature_mechanism_for_digest")
                # Intentar recrear el signer con parámetros explícitos
                try:
                    from pyhanko.sign.signers import SimpleSigner
                    from pyhanko.sign.signers.pdf_signer import PdfSigner
                    current_app.logger.info("Intentando recrear signer con parámetros explícitos")
                    # Forzar creación con algoritmo explícito
                    pdf_signer = PdfSigner(
                        meta, 
                        signer=signer,
                        timestamper=None,
                        new_field_spec=None
                    )
                except Exception as fallback_exc:
                    current_app.logger.error(f"Fallo en fallback: {fallback_exc}")
                    raise RuntimeError(f"No se puede crear PdfSigner: {fallback_exc}")
            else:
                pdf_signer = signers.PdfSigner(meta, signer=signer)
            
            current_app.logger.info("Ejecutando firma")
            with open(output_pdf, "wb") as outf:
                pdf_signer.sign_pdf(w, output=outf)
                
        current_app.logger.info("Firma PAdES completada")
        
    except Exception as exc:
        current_app.logger.error(f"Error en proceso de firma: {exc}")
        current_app.logger.error(f"Tipo de error: {type(exc).__name__}")
        current_app.logger.error(f"Traceback completo: {traceback.format_exc()}")
        
        # Debug específico para el error NoneType
        if "'NoneType' object has no attribute 'get_signature_mechanism_for_digest'" in str(exc):
            current_app.logger.error("=== DEBUG DETALLADO ===")
            current_app.logger.error(f"signer type: {type(signer)}")
            current_app.logger.error(f"signer dir: {dir(signer)}")
            if hasattr(signer, '__dict__'):
                current_app.logger.error(f"signer __dict__: {signer.__dict__}")
        
        raise RuntimeError(f"Error firmando PDF: {exc}")



