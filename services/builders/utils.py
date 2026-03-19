# sigp/services/builders/utils.py
from datetime import datetime
from pathlib import Path
from flask import current_app

def draw_header(c, width, height):
    """Dibuja el logo en el encabezado si existe."""
    try:
        header_path = Path(current_app.root_path) / "static" / "img" / "head_contracts.png"
        if header_path.exists():
            img_w, img_h = 500, 80
            x = (width - img_w) / 2
            y = height - 100
            c.drawImage(str(header_path), x, y, width=img_w, height=img_h, preserveAspectRatio=True, mask='auto')
    except Exception:
        pass

def draw_centered(c, text: str, width: float, y: float, font="Helvetica-Bold", size=16):
    c.setFont(font, size)
    tw = c.stringWidth(text, font, size)
    c.drawString((width - tw) / 2, y, text)

def draw_right(c, text: str, width: float, y: float, font="Helvetica", size=12, margin_right=72):
    c.setFont(font, size)
    tw = c.stringWidth(text, font, size)
    x = max(0, width - margin_right - tw)
    c.drawString(x, y, text)

def wrap_text(c, text: str, max_width: float, font="Helvetica", size=11) -> list[str]:
    c.setFont(font, size)
    words = text.split()
    lines = []
    line = ""
    for w in words:
        candidate = (line + " " + w).strip()
        if c.stringWidth(candidate, font, size) <= max_width:
            line = candidate
        else:
            if line: lines.append(line)
            line = w
    if line: lines.append(line)
    return lines

def draw_paragraph(c, text: str, x: float, y: float, width_px: float, height: float, leading=16, font="Helvetica", size=11) -> float:
    c.setFont(font, size)
    for line in text.split("\n"):
        wrapped = wrap_text(c, line, width_px, font, size) if line else [""]
        for wl in wrapped:
            # Si llegamos al final de la página (margen inferior de 72)
            if y < 72:
                c.showPage()
                draw_header(c, width_px + 2*x, height) # Redibujamos el logo
                # AQUÍ ESTÁ LA MAGIA: Bajamos el cursor a 140 para saltarnos el logo
                y = height - 140 
                c.setFont(font, size)
            c.drawString(x, y, wl)
            y -= leading
    return y

def draw_bullets(c, items: list[str], x: float, y: float, width_px: float, height: float, bullet="•", leading=16, font="Helvetica", size=11) -> float:
    c.setFont(font, size)
    indent = 14
    for it in items:
        bullet_line = f"{bullet} " + it
        wrapped = wrap_text(c, bullet_line, width_px, font, size)
        for idx, wl in enumerate(wrapped):
            # Si llegamos al final de la página
            if y < 72:
                c.showPage()
                draw_header(c, width_px + 2*x, height)
                # AQUÍ EL MISMO AJUSTE
                y = height - 140
                c.setFont(font, size)
            draw_x = x if idx == 0 else x + indent
            c.drawString(draw_x + 15, y, wl)
            y -= leading
    return y

def spanish_long_date() -> str:
    dt = datetime.utcnow()
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    return f"a los {dt.day} días del mes de {meses[dt.month-1]} de {dt.year}"

def draw_signatures(c, width, height, datos, current_y):
    """Dibuja las cajas de firma bilingües, listas para ser estampadas posteriormente."""
    if current_y < 250:
        c.showPage()
        draw_header(c, width, height)
        
    idioma = datos.get("idioma", "Español")
    is_english = (idioma == "Inglés")

    txt_firma_prescriptor = "Prescriber's Signature:" if is_english else "Firma del Prescriptor:"
    txt_por_innova = "For Innova Training:" if is_english else "Por Innova Training:"
    # txt_cargo = "President and Sole Administrator" if is_english else "Presidente y Administrador Único"

    y_sig_base = 150
    c.setFont("Helvetica", 10)
    
    # 1. Caja Izquierda (Vacía para el Prescriptor)
    c.drawString(80, y_sig_base + 65, txt_firma_prescriptor)
    # nombre_prescriptor = datos.get("name", "EL COLABORADOR")
    # c.drawString(80, y_sig_base + 53, str(nombre_prescriptor)[:35])
    c.rect(80, y_sig_base, 220, 55)
    
    # 2. Caja Derecha (Vacía para Innova Training / Jesús)
    c.drawString(320, y_sig_base + 65, txt_por_innova)
    # c.drawString(320, y_sig_base + 53, "Jesús Serrano Sanz")
    # c.drawString(320, y_sig_base + 41, txt_cargo)
    c.rect(320, y_sig_base, 220, 55)