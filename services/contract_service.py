import os
import hashlib
from datetime import datetime
from pathlib import Path
from flask import current_app
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from typing import Optional


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
    # Datos de documento/domicilio dinámicos con fallbacks legibles
    _doc_type = (getattr(prescriptor, "document_type", None) or "DNI").strip()
    _doc_num = (getattr(prescriptor, "document_number", None) or "__________").strip()
    _domicile = (getattr(prescriptor, "domicile", None) or "__________________________").strip()

    c = canvas.Canvas(str(out_path), pagesize=A4)
    width, height = A4

    # Helper: fecha larga en español ("a los 24 días del mes de julio de 2025")
    def _spanish_long_date(dt: datetime) -> str:
        meses = [
            "enero", "febrero", "marzo", "abril", "mayo", "junio",
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
        ]
        return f"a los {dt.day} días del mes de {meses[dt.month-1]} de {dt.year}"

    # Metadatos básicos vía ReportLab (algunos visores los leen directamente)
    org_name = current_app.config.get("PRESIDENT_DISPLAY_NAME", "SIGP")
    title = f"Contrato de Prescripción - {name or 'Prescriptor'} - {today}"
    subject = "Contrato de Prescripción"
    keywords = "contrato, prescripción, firma digital, PAdES"
    c.setTitle(title)
    c.setAuthor(org_name)
    c.setSubject(subject)
    c.setKeywords(keywords)
    c.setCreator("SIGP")

    # Encabezado con imagen proporcionada (si existe)
    try:
        header_path = Path(current_app.root_path) / "static" / "img" / "head_contracts.png"
        if header_path.exists():
            # Escalar para ocupar ancho razonable
            img_w, img_h = 500, 80
            x = (width - img_w) / 2
            y = height - 100
            c.drawImage(str(header_path), x, y, width=img_w, height=img_h, preserveAspectRatio=True, mask='auto')
    except Exception:
        pass

    # Títulos centrados como el modelo
    def draw_centered(text: str, y: float, font="Helvetica-Bold", size=16):
        c.setFont(font, size)
        tw = c.stringWidth(text, font, size)
        c.drawString((width - tw) / 2, y, text)

    # Helpers de maquetación
    def wrap_text(text: str, max_width: float, font: str = "Helvetica", size: int = 11) -> list[str]:
        """Rompe texto por palabras para que no exceda max_width."""
        c.setFont(font, size)
        words = text.split()
        lines = []
        line = ""
        for w in words:
            candidate = (line + " " + w).strip()
            if c.stringWidth(candidate, font, size) <= max_width:
                line = candidate
            else:
                if line:
                    lines.append(line)
                line = w
        if line:
            lines.append(line)
        return lines

    def draw_paragraph(text: str, x: float, y: float, width_px: float, leading: int = 16, font: str = "Helvetica", size: int = 11) -> float:
        """Dibuja párrafo con salto de línea automático. Devuelve nuevo y (siguiente línea base)."""
        c.setFont(font, size)
        for line in text.split("\n"):
            wrapped = wrap_text(line, width_px, font, size) if line else [""]
            for wl in wrapped:
                if y < 72:  # salto de página si se acaba el espacio
                    c.showPage()
                    y = height - 72
                    c.setFont(font, size)
                c.drawString(x, y, wl)
                y -= leading
        return y

    def draw_bullets(items: list[str], x: float, y: float, width_px: float, bullet: str = "•", leading: int = 16, font: str = "Helvetica", size: int = 11) -> float:
        c.setFont(font, size)
        indent = 14  # sangría para líneas envueltas
        for it in items:
            # primera línea con viñeta
            bullet_line = f"{bullet} " + it
            wrapped = wrap_text(bullet_line, width_px, font, size)
            for idx, wl in enumerate(wrapped):
                if y < 72:
                    c.showPage()
                    y = height - 72
                    c.setFont(font, size)
                draw_x = x if idx == 0 else x + indent
                c.drawString(draw_x + 15, y, wl)
                y -= leading
        return y

    y_cursor = height - 120
    draw_centered("ACUERDO DE COLABORACIÓN COMERCIAL EXTERNA ENTRE", y_cursor, size=14)
    y_cursor -= 24
    draw_centered("INNOVA TRAINING CYF SL (SPORTS DATA CAMPUS)", y_cursor, size=14)
    y_cursor -= 24
    nombre_prescriptor = name or "PRESCRIPTOR"
    draw_centered(f"Y {nombre_prescriptor.upper()}", y_cursor, size=14)

    # Línea de lugar/fecha centrada
    y_cursor -= 36
    ciudad = current_app.config.get("CONTRACT_CITY", "Valladolid")
    fecha_larga = _spanish_long_date(datetime.utcnow())
    draw_centered(f"En {ciudad}, {fecha_larga}.", y_cursor, font="Helvetica", size=12)

    # Separador hacia el bloque REUNIDOS
    y_cursor -= 28
    c.setFont("Helvetica-Bold", 12)
    draw_centered("REUNIDOS", y_cursor,size=14)

    # Párrafos REUNIDOS (con nombre dinámico del prescriptor y placeholders de DNI/domicilio)
    y_clausulas = y_cursor - 20
    margin_x = 72
    y_clausulas = draw_paragraph(
        "Don Jesús Serrano Sanz, con D.N.I. N.º 09.303.401-Q, como administrador único y en nombre y representación de INNOVA TRAINING CONSULTORIA Y FORMACION S.L., propietaria de la Marca Comercial Registrada “SPORTS DATA CAMPUS”, con C.I.F. N.º B19456128, y con el domicilio social en C/ del Campo de Gomara, 4, CP. 47008, Valladolid, ESPAÑA. " ,
        margin_x, y_clausulas, width - 2 * margin_x
    )
    y_clausulas -= 20
    # Bloque de datos del prescriptor con datos reales si están disponibles
    y_clausulas = draw_paragraph(
        f"Y, de otra parte, {nombre_prescriptor.upper()}, con {_doc_type} N.º {_doc_num}, con domicilio real en {_domicile}. ",
        margin_x, y_clausulas, width - 2 * margin_x
    )
    y_clausulas -= 20
    y_clausulas = draw_paragraph(
        " Actuando en función de sus respectivos cargos y en el ejercicio de las facultades que para convenir en nombre de las entidades que representan tienen conferidas se acuerdan las siguientes:" ,
        margin_x, y_clausulas, width - 2 * margin_x
    )
    

    # Encabezado CLÁUSULAS al final de la página 1 y salto de página
    y_clausulas -= 15
    c.setFont("Helvetica-Bold", 12)
    draw_centered("CLÁUSULAS", y_clausulas, size=14)

    y_clausulas -= 20
    margin_x = 72
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin_x, y_clausulas, "PRIMERA. – Objeto del Acuerdo")
    y_clausulas -= 20
    y_clausulas = draw_paragraph(
        "El  presente  acuerdo  tiene  por  objeto  regular  la  colaboración  comercial  entre  LA  EMPRESA  y  EL COLABORADOR  para  la  generación  de  leads  y  la  promoción  y  venta  de  los  programas  formativos que  imparte  LA  EMPRESA.  EL  COLABORADOR  desempeñará  su  actividad  de  manera  autónoma  y bajo su propia responsabilidad, sin que exista relación laboral entre las partes.",
        margin_x, y_clausulas, width - 2 * margin_x
    )
    y_clausulas -= 20

    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin_x, y_clausulas, "SEGUNDA. – Sistema de Comisiones por Categorías")
    y_clausulas -= 20

    y_clausulas = draw_paragraph(
        "Las comisiones se calcularán aplicando un porcentaje sobre el precio becado del programa según la categorización establecida por LA EMPRESA basada en el valor del precio becado: ",
        margin_x, y_clausulas, width - 2 * margin_x
    )
    
    y_clausulas -= 10
    econ_bullets = [
        "Categoría TITANIO: Precio becado mayor a €15.000 - la comisión es de €1000.",
        "Categoría PLATINO: Precio becado entre €10.000 y €14.999 - la comisión es de €600.",
        "Categoría ORO: Precio becado entre €5.200 y €9.999 - la comisión es de €520.",
        "Categoría PLATA: Precio becado entre €3.200 y €5.199 - la comisión es de €250.",
        "Categoría BRONCE: Precio becado entre €900 y €3.199 - la comisión es de €200.",
        "Categoría BASE: Precio becado menor a €899 - la comisión es de €80.",
    ]
    y_clausulas = draw_bullets(econ_bullets, margin_x, y_clausulas, width - 2 * margin_x)

    c.showPage()

    # =====================
    # Página 2
    # =====================
    # Encabezado con imagen proporcionada (si existe)
    try:
        header_path = Path(current_app.root_path) / "static" / "img" / "head_contracts.png"
        if header_path.exists():
            # Escalar para ocupar ancho razonable
            img_w, img_h = 500, 80
            x = (width - img_w) / 2
            y = height - 100
            c.drawImage(str(header_path), x, y, width=img_w, height=img_h, preserveAspectRatio=True, mask='auto')
    except Exception:
        pass

    margin_x = 72
    y = height - 130
    
    c.setFont("Helvetica-Bold", 13)
    c.drawString(margin_x, y, "Condiciones Económicas de las Comisiones")
    y -= 22
    econ_bullets = [
        "Importes netos: Todas las comisiones establecidas son importes NETOS, con impuestos incluidos",
        "Facturación con IVA: Si EL COLABORADOR requiere facturar con IVA, el importe total (IVA incluido) será igual a la suma de sus comisiones establecidas",
        "Gastos asociados: Cualquier gasto derivado de las transacciones monetarias (comisiones bancarias, transferencias, cambio de divisa, etc.) será exclusivamente por cuenta y a cargo de EL COLABORADOR",
    ]
    y = draw_bullets(econ_bullets, margin_x, y, width - 2 * margin_x)
    y -= 6
    y = draw_paragraph(
        "Ejemplo: Si la comisión establecida es €1.000, este será el importe final que recibirá EL COLABORADOR, independientemente de su situación fiscal o costos bancarios",
        margin_x, y, width - 2 * margin_x
    )

    y -= 10
    c.setFont("Helvetica-Bold", 13)
    c.drawString(margin_x, y, "Cronograma de Pagos")
    y -= 22
    y = draw_bullets([
        "50% de la comisión: Se abonará en la liquidación del mes siguiente a la confirmación de matrícula.",
        "50% restante: Se distribuirá en cuotas mensuales comenzando el segundo mes posterior a la confirmación de matrícula.",
    ], margin_x, y, width - 2 * margin_x)

    y -= 10
    y = draw_paragraph(
        "Calendario Específico de Cuotas por Edición LA EMPRESA imparte programas en dos (2) ediciones anuales con cronogramas específicos de pago:",
        margin_x, y, width - 2 * margin_x, font="Helvetica-Bold", size=11
    )
    y = draw_paragraph("\nEdiciones de MARZO:", margin_x, y, width - 2 * margin_x, font="Helvetica-Bold", size=12)
    y = draw_bullets([
        "50% de comisión: Al mes siguiente de la confirmación de matrícula",
        "50% restante: Primera cuota en mayo, continuando mensualmente según la cantidad de cuotas registradas en el Sistema Integral de Prescriptores, en adelante SIGP",
    ], margin_x, y, width - 2 * margin_x)
    y = draw_paragraph("\nEdiciones de OCTUBRE:", margin_x, y, width - 2 * margin_x, font="Helvetica-Bold", size=12)
    y = draw_bullets([
        "50% de comisión: Al mes siguiente de la confirmación de matrícula",
        "50% restante: Primera cuota en diciembre, continuando mensualmente según la cantidad de cuotas registradas en el SIGP.",
    ], margin_x, y, width - 2 * margin_x)
    y = draw_paragraph("\nAsignación de Edición:", margin_x, y, width - 2 * margin_x, font="Helvetica-Bold", size=12)
    y = draw_bullets([
        "Edición MARZO: Matrículas desde enero hasta mayo",
        "Edición OCTUBRE: Matrículas desde junio hasta diciembre",
    ], margin_x, y, width - 2 * margin_x)
    y = draw_paragraph("\nProceso de Registro", margin_x, y, width - 2 * margin_x, font="Helvetica-Bold", size=12)
    y = draw_paragraph(
        "Al momento de convertir el lead en matrícula, el comercial registrará en el SIGP:",
        margin_x, y, width - 2 * margin_x
    )
    y = draw_paragraph("1. Confirmación de matrícula y pago de prematrícula  \n2. Cantidad de cuotas del programa  \n3. El sistema generará automáticamente el cronograma de comisiones correspondiente", margin_x + 15, y, width - 2 * margin_x)

    c.showPage()

    # =====================
    # Página 3
    # =====================
    # Encabezado con imagen proporcionada (si existe)
    try:
        header_path = Path(current_app.root_path) / "static" / "img" / "head_contracts.png"
        if header_path.exists():
            # Escalar para ocupar ancho razonable
            img_w, img_h = 500, 80
            x = (width - img_w) / 2
            y = height - 100
            c.drawImage(str(header_path), x, y, width=img_w, height=img_h, preserveAspectRatio=True, mask='auto')
    except Exception:
        pass

    margin_x = 72
    y = height - 130
    c.setFont("Helvetica-Bold", 13)
    c.drawString(margin_x, y, "TERCERA. – Bonus por Volumen")
    y -= 20
    y = draw_paragraph(
        "EL COLABORADOR recibirá un bonus adicional de €50 por cada matrícula confirmada y pagada, que supere las diez (10) matriculaciones confirmadas en un mismo mes calendario, por lo que cada inicio de mes los contadores correspondientes para aplicar a dicho Bonus se reiniciaran desde cero, por consiguiente, el mismo nunca será acumulativo.",
        margin_x, y, width - 2 * margin_x
    )
    y -= 8
    y = draw_paragraph("Condiciones del Bonus:", margin_x, y, width - 2 * margin_x, font="Helvetica-Bold", size=12)
    y = draw_bullets([
        "Se aplica a partir de la matrícula número once (11) en adelante del mismo mes.",
        "Solo se contabilizan matrículas efectivamente confirmadas y con pago de prematrícula realizado en término.",
    ], margin_x, y, width - 2 * margin_x)

    y -= 10
    c.setFont("Helvetica-Bold", 13)
    c.drawString(margin_x, y, "CUARTA. – Gestión de Bajas y Ajustes")
    y -= 18
    y = draw_paragraph("Se realizarán los correspondientes ajustes en las comisiones del prescriptor en los siguientes casos:", margin_x, y, width - 2 * margin_x)
    y = draw_paragraph("1. Programa no impartido: Cuando un programa no se imparta por no alcanzar el número mínimo de alumnos.", margin_x + 15, y, width - 2 * margin_x)
    y = draw_paragraph("2. Abandono del estudiante: Cuando un estudiante deja de cursar el programa por cualquier motivo.", margin_x + 15, y, width - 2 * margin_x)
    y = draw_paragraph("3. Impago: Cuando un estudiante deje de abonar las cuotas del programa.", margin_x + 15, y, width - 2 * margin_x)
    y = draw_paragraph("4. Baja voluntaria: Cuando un estudiante solicita formalmente la baja del programa.", margin_x + 15, y, width - 2 * margin_x)
    y = draw_paragraph(
        "\nEn todos estos casos, los importes de comisión ya abonados se ajustarán proporcionalmente en sucesivas liquidaciones, mientras que los tiempos de aviso para dichos casos serán los mismos que se comunican al alumnado en función del estatuto vigente.",
        margin_x + 15, y, width - 2 * margin_x
    )

    y -= 10
    c.setFont("Helvetica-Bold", 13)
    c.drawString(margin_x, y, "Sistema de Cuenta Corriente")
    y -= 20
    y = draw_bullets([
        "Débitos: Comisiones a favor del prescriptor por matrículas confirmadas.",
        "Créditos: Ajustes por bajas de estudiantes o programas no impartidos.",
    ], margin_x, y, width - 2 * margin_x)

    y -= 10
    c.setFont("Helvetica-Bold", 13)
    c.drawString(margin_x, y, "Sistema de Autorización y Pago de Comisiones")
    y -= 20
    y = draw_paragraph("Cronograma Mensual de Procesamiento:", margin_x, y, width - 2 * margin_x, font="Helvetica-Bold", size=11)
    y = draw_bullets([
        "Hasta el último día del mes: Se procesan todas las comisiones generadas por matrículas y cuotas del mes.",
        "Los primeros 7 días hábiles: El departamento de Finanzas/Administración de LA EMPRESA realiza la autorización de pago/s según corresponda.",
    ], margin_x, y, width - 2 * margin_x)
    y = draw_paragraph("Proceso de Autorización:", margin_x, y, width - 2 * margin_x, font="Helvetica-Bold", size=11)
    y = draw_paragraph("1. El SIGP genera automáticamente la lista de todas las comisiones a rendir por cada mes.", margin_x + 15, y, width - 2 * margin_x)
    y = draw_paragraph("2. Finanzas verifica el estado de pago de cada estudiante asociado a las comisiones.", margin_x + 15, y, width - 2 * margin_x)
    y = draw_paragraph("3. Se autorizan únicamente las comisiones de estudiantes que estén al día con sus pagos.", margin_x + 15, y, width - 2 * margin_x)
    y = draw_paragraph("4. Las comisiones no autorizadas por impago del estudiante quedan registradas en el SIGP.", margin_x + 15, y, width - 2 * margin_x)

    c.showPage()

    # =====================
    # Página 4
    # =====================
    # Encabezado con imagen proporcionada (si existe)
    try:
        header_path = Path(current_app.root_path) / "static" / "img" / "head_contracts.png"
        if header_path.exists():
            # Escalar para ocupar ancho razonable
            img_w, img_h = 500, 80
            x = (width - img_w) / 2
            y = height - 100
            c.drawImage(str(header_path), x, y, width=img_w, height=img_h, preserveAspectRatio=True, mask='auto')
    except Exception:
        pass

    margin_x = 72
    y = height - 105
    
    c.setFont("Helvetica-Bold", 13)
    c.drawString(margin_x, y, "Gestión de Comisiones No Autorizadas:")
    y -= 20
    y = draw_bullets([
        "EL COLABORADOR podrá visualizar en el SIGP la lista detallada de comisiones no autorizadas por impago.",
        "Será responsabilidad de EL COLABORADOR gestionar con el estudiante la regularización de su situación de pago.",
        "Una vez que el estudiante regularice su situación, la comisión será autorizada en la siguiente liquidación mensual.",
        "No existe caducidad para las comisiones pendientes de autorización por impago.",
    ], margin_x, y, width - 2 * margin_x)
    y -= 5
    c.setFont("Helvetica-Bold", 13)
    c.drawString(margin_x, y, "Liquidación Final.")
    y -= 15
    y = draw_paragraph(
        "Las comisiones autorizadas se abonarán en los primeros diez (10) días hábiles del mes siguiente, conforme al cronograma establecido (50% primera liquidación + 50% en cuotas mensuales iguales).",
        margin_x, y, width - 2 * margin_x
    )

    y -= 10
    c.setFont("Helvetica-Bold", 13)
    c.drawString(margin_x, y, "QUINTA. – Control de Calidad y Gestión de Leads")
    y -= 18
    y = draw_paragraph("Definición de Lead Válido", margin_x, y, width - 2 * margin_x, font="Helvetica-Bold", size=12)
    y = draw_paragraph("Se considera lead válido aquel prospecto que:", margin_x, y, width - 2 * margin_x)

    y = draw_paragraph("1. Proporciona datos de contacto completos y verificables.", margin_x + 15, y, width - 2 * margin_x)
    y = draw_paragraph("2. Manifiesta interés genuino en los programas formativos de LA EMPRESA.", margin_x + 15, y, width - 2 * margin_x)
    y = draw_paragraph("3. Cumple con los requisitos mínimos de acceso al programa.", margin_x + 15, y, width - 2 * margin_x)
    y = draw_paragraph("4. No constituye información duplicada o fraudulenta.", margin_x + 15, y, width - 2 * margin_x)

    y -= 6
    y = draw_paragraph("Asignación y Propiedad de Leads", margin_x, y, width - 2 * margin_x, font="Helvetica-Bold", size=12)
    y = draw_bullets([
        "Todo lead registrado en el SIGP queda asignado al prescriptor que lo registró por un período de doce (12) meses.",
        "Transcurridos doce (12) meses sin conversión, el lead queda \"huérfano\" y puede ser trabajado por cualquier prescriptor.",
        "La antigüedad y propiedad de leads se determina exclusivamente por el registro en el SIGP, que cuenta con sistema de auditoría y bitácora.",
        "El SIGP es desarrollado, gestionado y auditado exclusivamente por LA EMPRESA y constituye la única fuente válida para determinar la propiedad de leads.",
    ], margin_x, y, width - 2 * margin_x)
    y = draw_paragraph("Territorialidad y Exclusividad", margin_x, y, width - 2 * margin_x, font="Helvetica-Bold", size=12)
    y = draw_bullets([
        "Al tratarse de formación online, no existe exclusividad territorial.",
        "Cualquier prescriptor puede comercializar en cualquier ubicación geográfica.",
        "La comisión corresponde al prescriptor que primero registró el lead en el SIGP, respetando el período de doce (12) meses establecidos.",
        "En caso de cualquier tipo de disputas sobre la propiedad de un lead, el Comité de Dirección de Sports Data Campus actuará como tribunal único de asignación.",
    ], margin_x, y, width - 2 * margin_x)
    y -= 10
    y = draw_paragraph("SEXTA. – Propiedad de Base de Datos", margin_x, y, width - 2 * margin_x, font="Helvetica-Bold", size=13)
    y = draw_paragraph(
        "Todos los leads, datos de contacto e información de prospectos generados durante la vigencia de este acuerdo son propiedad exclusiva de LA EMPRESA y se gestionan a través del SIGP. EL COLABORADOR no adquiere derechos de propiedad sobre dicha información y se compromete a no utilizarla para fines distintos a los establecidos en este contrato.",
        margin_x, y, width - 2 * margin_x
    )

    c.showPage()

    # =====================
    # Página 5
    # =====================
    # Encabezado con imagen proporcionada (si existe)
    try:
        header_path = Path(current_app.root_path) / "static" / "img" / "head_contracts.png"
        if header_path.exists():
            # Escalar para ocupar ancho razonable
            img_w, img_h = 500, 80
            x = (width - img_w) / 2
            y = height - 100
            c.drawImage(str(header_path), x, y, width=img_w, height=img_h, preserveAspectRatio=True, mask='auto')
    except Exception:
        pass

    margin_x = 72
    y = height - 120

    c.setFont("Helvetica-Bold", 13)
    c.drawString(margin_x, y, "SÉPTIMA. – Obligaciones de las Partes")
    y -= 18
    y = draw_paragraph("De LA EMPRESA:", margin_x, y, width - 2 * margin_x, font="Helvetica-Bold", size=12)
    
    y = draw_paragraph("1. Proporcionar a EL COLABORADOR toda la información y materiales necesarios para la comercialización de los programas.", margin_x + 15, y, width - 2 * margin_x)
    y = draw_paragraph("2. Facilitar el acceso a plataformas y herramientas necesarias para la gestión de leads.", margin_x + 15, y, width - 2 * margin_x)
    y = draw_paragraph("3. Realizar el pago de las comisiones conforme a lo estipulado en las cláusulas anteriores.", margin_x + 15, y, width - 2 * margin_x)
    y = draw_paragraph("4. Mantener actualizada la categorización de programas y comunicar cualquier cambio con 30 días de antelación.", margin_x + 15, y, width - 2 * margin_x)

    y -= 6
    y = draw_paragraph("De EL COLABORADOR:", margin_x, y, width - 2 * margin_x, font="Helvetica-Bold", size=12)
    
    y = draw_paragraph("1. Realizar la promoción de los programas de forma profesional y ética, respetando la imagen y las premisas facilitadas por LA EMPRESA.", margin_x + 15, y, width - 2 * margin_x)
    y = draw_paragraph("2. Presentar informes periódicos sobre el avance de la actividad comercial.", margin_x + 15, y, width - 2 * margin_x)
    y = draw_paragraph("3. Cumplir con la normativa vigente, especialmente en materia de protección de datos y comunicaciones comerciales.", margin_x + 15, y, width - 2 * margin_x)
    y = draw_paragraph("4. Informar inmediatamente a LA EMPRESA sobre cualquier baja o incidencia con los estudiantes gestionados.", margin_x + 15, y, width - 2 * margin_x)

    y -= 6
    c.setFont("Helvetica-Bold", 13)
    c.drawString(margin_x, y, "OCTAVA. – Duración y Resolución")
    y -= 18
    y = draw_paragraph(
        "Este acuerdo tiene una duración inicial de un (1) año, renovable automáticamente por iguales períodos salvo notificación previa de alguna de las partes con al menos treinta (30) días de antelación. El acuerdo podrá resolverse por incumplimiento grave de las obligaciones establecidas, mutuo acuerdo o decisión unilateral de cualquiera de las partes, con un preaviso de 30 días.",
        margin_x, y, width - 2 * margin_x
    )
    y -= 8
    c.setFont("Helvetica-Bold", 13)
    c.drawString(margin_x, y, "NOVENA. – Confidencialidad")
    y -= 18
    y = draw_paragraph(
        "EL COLABORADOR se compromete a no divulgar información confidencial relacionada con LA EMPRESA, los programas formativos o sus clientes, tanto durante la vigencia del contrato como después de su finalización.",
        margin_x, y, width - 2 * margin_x
    )
    y -= 8
    c.setFont("Helvetica-Bold", 13)
    c.drawString(margin_x, y, "DÉCIMA. – Protección de Datos")
    y -= 18

    y = draw_paragraph("1. EL COLABORADOR tratará los datos personales proporcionados por LA EMPRESA y los adquiridos durante el periodo de vigencia de este acuerdo, exclusivamente, para los fines establecidos en este contrato, no pudiendo utilizarlos para ningún otro fin personal o profesional.", margin_x + 15, y, width - 2 * margin_x)
    y = draw_paragraph("2. EL COLABORADOR implementará las medidas de seguridad necesarias para garantizar la protección de los datos personales tratados.", margin_x + 15, y, width - 2 * margin_x)
    y = draw_paragraph("3. Una vez finalizada la relación contractual, EL COLABORADOR se compromete a eliminar o devolver los datos personales que le hayan sido proporcionados.", margin_x + 15, y, width - 2 * margin_x)
    y = draw_paragraph("4. EL COLABORADOR informará inmediatamente a LA EMPRESA en caso de cualquier incidente que comprometa la seguridad de los datos personales.", margin_x + 15, y, width - 2 * margin_x)


    c.showPage()

    # =====================
    # Página 6
    # =====================
    # Encabezado con imagen proporcionada (si existe)
    try:
        header_path = Path(current_app.root_path) / "static" / "img" / "head_contracts.png"
        if header_path.exists():
            # Escalar para ocupar ancho razonable
            img_w, img_h = 500, 80
            x = (width - img_w) / 2
            y = height - 100
            c.drawImage(str(header_path), x, y, width=img_w, height=img_h, preserveAspectRatio=True, mask='auto')
    except Exception:
        pass

    margin_x = 72
    y = height - 130

    c.setFont("Helvetica-Bold", 13)
    c.drawString(margin_x, y, "UNDÉCIMA. – Jurisdicción y Legislación Aplicable")
    y -= 18
    y = draw_paragraph(
        "El presente contrato se regirá por la legislación española. Para la resolución de cualquier conflicto derivado del presente contrato, ambas partes se someten a la jurisdicción de los juzgados y tribunales de Valladolid, España.",
        margin_x, y, width - 2 * margin_x
    )

    # Espacio y cajas de firma en la última página
    y_sig_base = 150
    c.setFont("Helvetica", 10)
    c.drawString(80, y_sig_base + 65, "Firma del Prescriptor:")
    c.rect(80, y_sig_base, 220, 55)
    c.drawString(320, y_sig_base + 65, "Firma del Presidente:")
    c.rect(320, y_sig_base, 220, 55)

    # No hacer showPage() aquí para evitar una página en blanco final
    c.save()

    # Post-proceso para asegurar metadatos extendidos (Producer, CreationDate, ModDate)
    try:
        from pypdf import PdfReader, PdfWriter

        def _pdf_date(dt: datetime) -> str:
            return dt.strftime("D:%Y%m%d%H%M%SZ")

        reader = PdfReader(str(out_path))
        writer = PdfWriter()
        for p in reader.pages:
            writer.add_page(p)

        now = datetime.utcnow()
        writer.add_metadata(
            {
                "/Title": title,
                "/Author": org_name,
                "/Subject": subject,
                "/Keywords": keywords,
                "/Creator": "SIGP",
                "/Producer": "SIGP (INNOVA TRAINING CONSULTORIA Y FORMACION S.L.)",
                "/CreationDate": _pdf_date(now),
                "/ModDate": _pdf_date(now),
            }
        )

        with open(out_path, "wb") as outf:
            writer.write(outf)
    except Exception:
        # Si algo falla en el post-proceso de metadatos, dejamos el PDF base igualmente
        pass

    # Escribir XMP + DocInfo coherentes (mejor compatibilidad con visores)
    try:
        embed_pdf_metadata_xmp(
            out_path,
            title=title,
            author=org_name,
            subject=subject,
            keywords=keywords,
            creator="SIGP",
            producer="SIGP (INNOVA TRAINING CONSULTORIA Y FORMACION S.L.)",
        )
    except Exception:
        pass

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
    """Firma el PDF con PAdES-BES usando el certificado P12 configurado.
    Si se configura PKCS#11 en el futuro, se puede ampliar.
    """
    from pyhanko.sign import signers
    from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter

    p12_path = current_app.config.get("PRESIDENT_CERT_PATH")
    p12_pass = current_app.config.get("PRESIDENT_CERT_PASS", "")
    if not p12_path:
        raise RuntimeError("PRESIDENT_CERT_PATH no configurado")

    p12_abs = Path(current_app.root_path, p12_path) if not p12_path.startswith("/") else Path(p12_path)
    signer = signers.SimpleSigner.load_pkcs12(str(p12_abs), passphrase=p12_pass.encode() if p12_pass else None)

    with open(input_pdf, "rb") as inf:
        w = IncrementalPdfFileWriter(inf)
        # Definimos un nombre de campo para permitir crear el campo de firma si no existe
        # Forzamos SHA-256 para evitar problemas de selección automática del mecanismo
        meta = signers.PdfSignatureMetadata(
            field_name="PresidentSignature",
            md_algorithm="sha256",
        )  # firma invisible
        with open(output_pdf, "wb") as outf:
            signers.PdfSigner(meta, signer=signer).sign_pdf(w, output=outf)
