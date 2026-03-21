# sigp/services/builders/alumno_builder_es.py

from sigp.services.builders.utils import (
    draw_header, draw_centered, draw_right, 
    draw_paragraph, draw_bullets, spanish_long_date
)

def build(c, prescriptor, datos):
    width, height = datos["width"], datos["height"]
    margin_x = 72
    
    # Extraemos datos, adaptando para Persona Jurídica
    # Asumimos que "name" es el representante y podemos usar un campo "company" si existe, 
    # o usar "name" para la entidad si así lo cargan en el formulario.
    nombre_entidad = getattr(prescriptor, "company_name", datos["name"]) 
    nombre_representante = datos["name"]
    doc_type, doc_num, domicile = datos["doc_type"], datos["doc_num"], datos["domicile"]
    
    # DIBUJO DEL ENCABEZADO Y TÍTULOS
    draw_header(c, width, height)
    y = height - 120
    
    draw_centered(c, "ACUERDO DE COLABORACIÓN COMERCIAL - PROGRAMA DE PRESCRIPTORES", width, y, size=13) [cite: 5]
    y -= 20
    draw_centered(c, "entre", width, y, font="Helvetica", size=11) [cite: 6]
    y -= 20
    draw_centered(c, "INNOVA TRAINING CONSULTORIA Y FORMACION S.L.\nSPORTS DATA CAMPUS", width, y, size=12) [cite: 7]
    y -= 20
    draw_centered(c, "y", width, y, font="Helvetica", size=11) [cite: 8]
    y -= 20
    draw_centered(c, nombre_entidad.upper(), width, y, size=12) [cite: 9]

    y -= 40
    fecha_larga = spanish_long_date()
    draw_right(c, f"En Valladolid, a {fecha_larga}.", width, y) [cite: 11]

    y -= 40
    draw_centered(c, "REUNIDOS", width, y, size=12) [cite: 10]
    y -= 30

    y = draw_paragraph(c, "De una parte,", margin_x, y, width - 2*margin_x, height, font="Helvetica-Oblique") [cite: 12]
    y = draw_paragraph(c, "Don Jesús Serrano Sanz, con D.N.I. nº 09.303.401-Q, actuando en su condición de Administrador Único y en nombre y representación de INNOVA TRAINING CONSULTORIA Y FORMACION S.L., propietaria de la marca comercial “Sports Data Campus”, con C.I.F. nº B19456128 y domicilio social en C/ del Campo de Gomara, 4, CP 47008, Valladolid, España (en adelante, LA EMPRESA).", margin_x, y, width - 2*margin_x, height) [cite: 13, 14]
    
    y -= 10
    y = draw_paragraph(c, "Y de otra parte,", margin_x, y, width - 2*margin_x, height, font="Helvetica-Oblique") [cite: 15]
    y = draw_paragraph(c, f"Don/Doña {nombre_representante.upper()}, con {doc_type} nº {doc_num}, con domicilio en {domicile}, quien actúa en su propio nombre y derecho, y que participa o ha participado como alumno en uno de los programas formativos impartidos por Sports Data Campus (en adelante, EL COLABORADOR).", margin_x, y, width - 2*margin_x, height) [cite: 16, 17]

    y -= 10
    y = draw_paragraph(c, "Ambas partes, reconociéndose mutuamente la capacidad legal necesaria para obligarse en el presente acuerdo,", margin_x, y, width - 2*margin_x, height) [cite: 18]

    y -= 20
    draw_centered(c, "EXPONEN", width, y, size=12) [cite: 19]
    y -= 30
    
    y = draw_paragraph(c, "Que dicho programa tiene como objetivo fomentar la participación de la comunidad académica de Sports Data Campus en la difusión de sus programas formativos, reconociendo dicha colaboración mediante un sistema de bonificaciones formativas o beneficios equivalentes.", margin_x, y, width - 2*margin_x, height) [cite: 20]
    y = draw_paragraph(c, "En virtud de lo anterior, las partes acuerdan formalizar el presente Acuerdo de Colaboración dentro del Programa de Prescriptores, que se regirá por las siguientes:", margin_x, y, width - 2*margin_x, height) [cite: 21]

    y -= 20
    draw_centered(c, "CLÁUSULAS", width, y, size=12) [cite: 23]
    y -= 30

    # CLÁUSULA 1 - OBJETO DEL ACUERDO
    y = draw_paragraph(c, "PRIMERA.- OBJETO DEL ACUERDO", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    
    y = draw_paragraph(c, "El presente acuerdo tiene por objeto regular la participación de EL COLABORADOR en el Programa de Prescriptores de Sports Data Campus, mediante el cual, en su condición de alumno, podrá recomendar y difundir los programas formativos impartidos por LA EMPRESA entre potenciales interesados, contribuyendo al crecimiento y fortalecimiento de la comunidad académica de Sports Data Campus.", margin_x, y, width - 2*margin_x, height) [cite: 27]

    y = draw_paragraph(c, "En el marco de este acuerdo, EL COLABORADOR podrá identificar y referir potenciales interesados (en adelante, leads), que serán gestionados y registrados a través del SIGP (Sistema Integral de Gestión de Prescriptores) o de las plataformas oficiales que LA EMPRESA determine.", margin_x, y, width - 2*margin_x, height) [cite: 28]

    y = draw_paragraph(c, "El presente acuerdo regula exclusivamente la participación de EL COLABORADOR en el Programa de Prescriptores de Sports Data Campus y es independiente de cualquier otra relación académica, profesional o institucional que pudiera existir entre las partes.", margin_x, y, width - 2*margin_x, height) [cite: 29]

    y = draw_paragraph(c, "La actividad desarrollada por EL COLABORADOR se realizará de forma voluntaria y con plena autonomía, sin que exista en ningún caso relación laboral, mercantil o de dependencia entre las partes.", margin_x, y, width - 2*margin_x, height) [cite: 30]

    y = draw_paragraph(c, "En ningún caso EL COLABORADOR estará facultado para actuar en nombre o representación de LA EMPRESA, ni para asumir compromisos, formalizar acuerdos o modificar condiciones comerciales en nombre de Sports Data Campus frente a terceros.", margin_x, y, width - 2*margin_x, height) [cite: 31]

    y = draw_paragraph(c, "La participación de EL COLABORADOR en el Programa de Prescriptores se limita exclusivamente a la identificación, recomendación y derivación cualificada de potenciales interesados en los programas formativos de LA EMPRESA.", margin_x, y, width - 2*margin_x, height) [cite: 32]

    y = draw_paragraph(c, "En ningún caso EL COLABORADOR realizará actividades de venta, negociación, cierre comercial o formalización de matrículas, funciones que corresponden de forma exclusiva al Departamento Comercial de LA EMPRESA.", margin_x, y, width - 2*margin_x, height) [cite: 33]

    y = draw_paragraph(c, "Asimismo, EL COLABORADOR no estará autorizado a establecer condiciones económicas, ofrecer descuentos, comprometer plazas ni realizar promesas comerciales en nombre de LA EMPRESA frente a terceros.", margin_x, y, width - 2*margin_x, height) [cite: 34]

    y -= 10

    # CLÁUSULA 2.- SISTEMA DE BONIFICACIONES POR MATRÍCULA CONVERTIDA
    y = draw_paragraph(c, "SEGUNDA.- SISTEMA DE BONIFICACIONES POR MATRÍCULA CONVERTIDA", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    
    y = draw_paragraph(c, "\n2.1 Bonificación por Matrícula Convertida", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    y = draw_paragraph(c, "EL COLABORADOR tendrá derecho a recibir una bonificación dentro del Programa de Prescriptores por cada matrícula convertida que provenga de un lead válido previamente registrado en el SIGP (Sistema Integral de Gestión de Prescriptores) y asignado conforme a las reglas establecidas en el presente acuerdo.", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "A efectos del presente acuerdo, se entenderá por matrícula convertida aquella en la que el alumno referido por EL COLABORADOR haya formalizado su inscripción en un programa formativo impartido por LA EMPRESA y haya realizado el pago efectivo que activa el reconocimiento de la bonificación correspondiente.", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "Las bonificaciones generadas podrán materializarse mediante beneficios formativos, créditos académicos o reducción de costes en programas impartidos por Sports Data Campus, conforme a las condiciones establecidas en las siguientes cláusulas del presente acuerdo.", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "\n2.2 Valor de las bonificaciones", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    y = draw_paragraph(c, "Las bonificaciones generadas por matrículas de recomendados del EL COLABORADOR convertidas se asignan conforme al siguiente valor equivalente dentro del sistema de beneficios formativos de Sports Data Campus:", margin_x, y, width - 2*margin_x, height)

    bonificaciones_list = [
        "Másteres impartidos en inglés: 300€ por matrícula convertida.",
        "Másteres impartidos en español o portugués: 150€ por matrícula convertida.",
        "Diplomados y cursos de más corta duración: 50€ por matrícula convertida."
    ]
    y = draw_bullets(c, bonificaciones_list, margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "Dichos valores se acumularán en la cuenta del colaborador dentro del Programa de Prescriptores y podrán aplicarse como créditos formativos, reducción de matrícula u otros beneficios académicos ofrecidos por LA EMPRESA.", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "LA EMPRESA podrá actualizar el presente sistema de bonificaciones cuando existan cambios en su política académica o en su estructura de programas formativos, comprometiéndose a comunicar dichas modificaciones con una antelación mínima de treinta (30) días naturales.", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "\n2.3 Aplicación de las bonificaciones", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    y = draw_paragraph(c, "Las bonificaciones generadas en el marco del Programa de Prescriptores se acumularán como créditos formativos dentro del sistema de beneficios de Sports Data Campus. Dichos créditos podrán ser aplicados por EL COLABORADOR como reducción de costes en programas formativos, acceso a otros cursos o beneficios académicos ofrecidos por LA EMPRESA.", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "Cada conversión a matrícula de un recomendado por EL COLABORADOR generará el importe correspondiente detallado en el apartado 2.2 del presente acuerdo, el cual podrá ser aplicado de la siguiente forma:", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "a) Bolsa de estudios:", margin_x, y, width - 2*margin_x, height)
    y = draw_paragraph(c, "Acumulado para poder ser descontado del precio a abonar por EL COLABORADOR en cualquiera de los programas formativos de Sports Data Campus en los que desee matricularse.", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "b) Abonos de Másteres en curso:", margin_x, y, width - 2*margin_x, height)
    y = draw_paragraph(c, "En caso de que EL COLABORADOR se encuentre matriculado en un programa formativo de Sports Data Campus y disponga de cuotas pendientes de abono, podrá:", margin_x, y, width - 2*margin_x, height)

    opciones_abono = [
        "Reducir la cuantía de las cuotas pendientes, de forma proporcional.",
        "Reducir el número de cuotas, de forma proporcional."
    ]
    y = draw_bullets(c, opciones_abono, margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "\n2.4 Registro y Determinación de bonificaciones", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    y = draw_paragraph(c, "Todas las matrículas convertidas, así como las bonificaciones correspondientes, serán registradas en el SIGP, que constituirá la única fuente válida para la determinación de:", margin_x, y, width - 2*margin_x, height)
    
    puntos_registro = [
        "Asignación del lead",
        "Conversión en matrícula",
        "Valor de la bonificación aplicable",
        "Estado de reconocimiento y aplicación de la bonificación."
    ]
    y = draw_bullets(c, puntos_registro, margin_x, y, width - 2*margin_x, height)

    y -= 10

    # CLÁUSULA 3.- DEVENGO Y LIQUIDACIÓN DE LAS BONIFICACIONES
    y = draw_paragraph(c, "TERCERA.- DEVENGO Y LIQUIDACIÓN DE LAS BONIFICACIONES", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    
    y = draw_paragraph(c, "\n3.1 Reconocimiento de la bonificación", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    y = draw_paragraph(c, "La bonificación correspondiente a una matrícula convertida será reconocida en el momento en que el alumno referido por EL COLABORADOR haya realizado el pago efectivo de la matrícula del programa formativo correspondiente y dicho pago haya sido recibido y validado por LA EMPRESA conforme a sus sistemas internos de cobro.", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "A efectos del presente acuerdo, se entenderá por pago efectivo de matrícula aquel pago inicial o confirmación de inscripción que permita formalizar la incorporación del alumno al programa formativo correspondiente conforme a los procedimientos administrativos de LA EMPRESA.", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "\n3.2 Validación de las bonificaciones", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    y = draw_paragraph(c, "Las bonificaciones generadas serán verificadas por el departamento de Administración de LA EMPRESA, quien confirmará la validez de la matrícula, la asignación del lead y la inexistencia de incidencias financieras asociadas al pago realizado por el alumno.", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "Una vez validada la información correspondiente, la bonificación quedará registrada y disponible para su aplicación dentro del sistema de beneficios del Programa de Prescriptores.", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "\n3.3 Registro y Aplicación de las bonificaciones", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    y = draw_paragraph(c, "Las bonificaciones reconocidas serán registradas en el sistema del Programa de Prescriptores de Sports Data Campus y se acumularán en la cuenta correspondiente a EL COLABORADOR.", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "Dichas bonificaciones podrán ser aplicadas por EL COLABORADOR como créditos formativos, reducción de matrícula u otros beneficios académicos ofrecidos por LA EMPRESA conforme a las condiciones vigentes del programa.", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "\n3.4 Condiciones para el Reconocimiento o Aplicación de la bonificación", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    y = draw_paragraph(c, "La aplicación o reconocimiento de las bonificaciones estará sujeta a las siguientes condiciones:", margin_x, y, width - 2*margin_x, height)

    condiciones_reconocimiento = [
        "Que la matrícula haya sido validada conforme a los sistemas de LA EMPRESA;",
        "Que el pago del alumno no haya sido objeto de devolución, retrocesión bancaria o incidencia financiera;",
        "Que la asignación del lead figure correctamente registrada en el SIGP."
    ]
    y = draw_bullets(c, condiciones_reconocimiento, margin_x, y, width - 2*margin_x, height)

    y -= 10

    # CLÁUSULA 4.- GESTIÓN DE BAJAS Y AJUSTES
    y = draw_paragraph(c, "CUARTA.- GESTIÓN DE BAJAS Y AJUSTES", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    
    y = draw_paragraph(c, "\n4.1 Supuestos de Regularización", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    y = draw_paragraph(c, "Las bonificaciones reconocidas conforme a la Cláusula Segunda podrán estar sujetas a regularización en los siguientes supuestos:", margin_x, y, width - 2*margin_x, height)
    
    supuestos_reg = [
        "a) Cuando el programa formativo no sea finalmente impartido por causas organizativas o por no alcanzarse el número mínimo de alumnos.",
        "b) Cuando el alumno ejerza su derecho de desistimiento o solicite la baja dentro de los plazos legal o contractualmente establecidos por LA EMPRESA.",
        "c) Cuando se produzca la devolución total o parcial del importe abonado por el alumno por cualquier causa debidamente justificada.",
        "d) Cuando exista impago, retrocesión bancaria, chargeback o cualquier incidencia financiera que implique la anulación total o parcial del pago que dio origen al reconocimiento de la bonificación."
    ]
    y = draw_bullets(c, supuestos_reg, margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "\n4.2 Efectos de la Regularización", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    y = draw_paragraph(c, "En los supuestos descritos en el apartado anterior:", margin_x, y, width - 2*margin_x, height)
    
    efectos_reg = [
        "En caso de que la bonificación hubiera sido generada a partir de una matrícula que posteriormente incurra en baja, impago, abandono o cualquier incidencia que implique la no continuidad del alumno en el programa formativo, LA EMPRESA podrá anular o ajustar dicha bonificación dentro del sistema de beneficios del Programa de Prescriptores.",
        "Si la bonificación hubiera sido aplicada total o parcialmente a EL COLABORADOR, el importe correspondiente podrá ser revertido, compensado o ajustado dentro del sistema de beneficios del Programa de Prescriptores gestionado a través del SIGP.",
        "En caso de que la bonificación haya sido utilizada para la reducción de cuotas o costes de un programa formativo en curso, LA EMPRESA podrá reimputar el importe correspondiente a EL COLABORADOR, quien deberá asumir la diferencia resultante en las condiciones económicas originalmente aplicables a su programa."
    ]
    y = draw_bullets(c, efectos_reg, margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "\n4.3 Sistema de Registro y Ajuste de bonificaciones", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    y = draw_paragraph(c, "A efectos de gestión y control del Programa de Prescriptores, LA EMPRESA mantendrá un registro interno de las bonificaciones generadas, aplicadas o ajustadas correspondientes a EL COLABORADOR. En dicho registro se reflejarán:", margin_x, y, width - 2*margin_x, height)
    
    puntos_registro_ajuste = [
        "bonificaciones reconocidas a favor de EL COLABORADOR derivadas de matrículas convertidas.",
        "Ajustes derivados de cancelaciones, devoluciones o incidencias financieras relacionadas con las matrículas correspondientes."
    ]
    y = draw_bullets(c, puntos_registro_ajuste, margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "En aquellos casos en los que alguna bonificación hubiera sido aplicada dentro del sistema de beneficios del Programa de Prescriptores, LA EMPRESA podrá compensar los importes correspondientes en registros posteriores o solicitar su reintegro conforme a lo establecido en el presente acuerdo.", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "\n4.4 Registro y Transparencia", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    y = draw_paragraph(c, "Todas las incidencias, cancelaciones, devoluciones o ajustes relacionados con matrículas convertidas serán registradas en el SIGP, que constituirá la única fuente válida para la determinación del estado de cada matrícula y de las bonificaciones asociadas.", margin_x, y, width - 2*margin_x, height)

    y -= 10

    # CLÁUSULA 5.- CONTROL DE CALIDAD Y GESTIÓN DE LEADS
    y = draw_paragraph(c, "QUINTA.- CONTROL DE CALIDAD Y GESTIÓN DE LEADS", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    
    y = draw_paragraph(c, "\n5.1 Definición de Lead Válido", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    y = draw_paragraph(c, "A efectos del presente acuerdo, se considerará lead válido aquel prospecto que cumpla simultáneamente con las siguientes condiciones:", margin_x, y, width - 2*margin_x, height)
    
    condiciones_lead = [
        "a) Proporcione datos de contacto completos, veraces y verificables. [cite: 113]",
        "b) Manifieste un interés real en los programas formativos de LA EMPRESA. [cite: 114]",
        "c) Cumpla con los requisitos mínimos de acceso al programa formativo correspondiente. [cite: 115]",
        "d) No constituya información duplicada, fraudulenta o previamente registrada en el SIGP por otro prescriptor dentro del período de asignación vigente. [cite: 116]"
    ]
    y = draw_bullets(c, condiciones_lead, margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "LA EMPRESA se reserva el derecho de validar la condición de lead válido conforme a los criterios internos establecidos en el SIGP. [cite: 117]", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "\n5.2 Registro y Asignación de Leads", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    y = draw_paragraph(c, "Para que un lead pueda generar derecho a bonificación dentro del Programa de Prescriptores, deberá ser registrado previamente en el SIGP (Sistema Integral de Gestión de Prescriptores) o en las plataformas oficiales que LA EMPRESA determine. [cite: 119]", margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "La asignación del lead corresponderá al prescriptor que lo haya registrado correctamente en el SIGP en primer lugar. [cite: 120] Dicha asignación permanecerá vigente durante un período de seis (6) meses desde la fecha de registro. [cite: 121]", margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "Transcurrido dicho plazo sin que se haya producido una matrícula convertida, el lead podrá ser trabajado por otros prescriptores, perdiendo el primero la exclusividad sobre el mismo. [cite: 122]", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "\n5.3 Trazabilidad y Determinación de la Titularidad", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    y = draw_paragraph(c, "La antigüedad, titularidad y estado de los leads se determinarán exclusivamente mediante el registro efectuado en el SIGP, el cual dispone de sistema de auditoría y registro interno de actividad. [cite: 124]", margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "El SIGP constituirá la única fuente válida y vinculante para la determinación de: [cite: 125]", margin_x, y, width - 2*margin_x, height)
    
    puntos_sigp = [
        "La titularidad del lead [cite: 127]",
        "La fecha de registro [cite: 128]",
        "La conversión en matrícula [cite: 129]",
        "El reconocimiento y estado de la bonificación correspondiente. [cite: 132]"
    ]
    y = draw_bullets(c, puntos_sigp, margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "\n5.4 Territorialidad y Exclusividad", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    y = draw_paragraph(c, "Dado que la actividad formativa de LA EMPRESA se desarrolla principalmente en modalidad online, el presente acuerdo no establece exclusividad territorial. [cite: 134]", margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "EL COLABORADOR podrá promover los programas formativos en cualquier ámbito geográfico. [cite: 135]", margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "La bonificación corresponderá exclusivamente al prescriptor que haya registrado válidamente el lead en el SIGP dentro del período de asignación establecido. [cite: 136]", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "\n5.5 Resolución de Controversias", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    y = draw_paragraph(c, "En caso de controversia sobre la titularidad de un lead o sobre la asignación de una matrícula convertida, LA EMPRESA resolverá la incidencia tomando como referencia la información registrada en el SIGP y los criterios internos de validación del Programa de Prescriptores. [cite: 138]", margin_x, y, width - 2*margin_x, height)

    y -= 10

    # CLÁUSULA 6.- PROPIEDAD DE LA BASE DE DATOS Y USO DE LA INFORMACIÓN
    y = draw_paragraph(c, "SEXTA.- PROPIEDAD DE LA BASE DE DATOS Y USO DE LA INFORMACIÓN", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    
    y = draw_paragraph(c, "\n6.1 Titularidad de los Datos", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    y = draw_paragraph(c, "Todos los leads, datos de contacto, información comercial y cualquier otro dato generado, captado o gestionado en el marco del presente acuerdo serán propiedad exclusiva de LA EMPRESA[cite: 141]. Dicha información será gestionada a través del SIGP (Sistema Integral de Gestión de Prescriptores) o de las plataformas oficiales que LA EMPRESA determine[cite: 142].", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "\n6.2 Limitación de Uso", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    limitaciones_uso = [
        "EL COLABORADOR no adquiere ningún derecho de propiedad, titularidad o explotación sobre los datos generados en el marco del presente acuerdo[cite: 145].",
        "EL COLABORADOR se compromete a utilizar dicha información exclusivamente para los fines establecidos en el presente acuerdo y conforme a las instrucciones y directrices de LA EMPRESA, respetando en todo momento la legislación vigente de Protección de Datos de cada territorio[cite: 146]."
    ]
    y = draw_bullets(c, limitaciones_uso, margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "\n6.3 Prohibición de Uso Externo", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    y = draw_paragraph(c, "Queda expresamente prohibido que EL COLABORADOR[cite: 148]:", margin_x, y, width - 2*margin_x, height)
    
    prohibiciones_ext = [
        "Utilice los datos obtenidos en el marco del presente acuerdo para fines distintos a la promoción de los programas formativos de LA EMPRESA[cite: 149];",
        "Incorpore los datos a bases de datos propias o de terceros[cite: 150];",
        "Comercialice productos o servicios ajenos a LA EMPRESA utilizando la información obtenida durante la vigencia del presente acuerdo[cite: 151]."
    ]
    y = draw_bullets(c, prohibiciones_ext, margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "\n6.4 Finalización del Acuerdo", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    y = draw_paragraph(c, "A la finalización del presente acuerdo, cualquiera que sea la causa, EL COLABORADOR deberá[cite: 153, 156]:", margin_x, y, width - 2*margin_x, height)
    
    obligaciones_fin = [
        "Cesar inmediatamente en el uso de los datos y de cualquier información obtenida a través del Programa de Prescriptores[cite: 157];",
        "Eliminar o destruir cualquier copia o registro de datos que obre en su poder[cite: 158];",
        "Abstenerse de contactar nuevamente a los leads generados en el marco del presente acuerdo, salvo autorización expresa y por escrito de LA EMPRESA[cite: 159]."
    ]
    y = draw_bullets(c, obligaciones_fin, margin_x, y, width - 2*margin_x, height)

    y -= 10

    # CLÁUSULA 7.- OBLIGACIONES DE LAS PARTES
    y = draw_paragraph(c, "SÉPTIMA – OBLIGACIONES DE LAS PARTES", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    
    y = draw_paragraph(c, "\n7.1 Obligaciones de LA EMPRESA", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    y = draw_paragraph(c, "LA EMPRESA se compromete a:", margin_x, y, width - 2*margin_x, height)
    
    obligaciones_empresa = [
        "A. Proporcionar a EL COLABORADOR la información comercial, materiales promocionales y documentación necesaria para la correcta promoción de los programas formativos.",
        "B. Facilitar el acceso al SIGP (Sistema Integral de Gestión de Prescriptores) como única herramienta oficial para el registro y seguimiento de leads.",
        "C. Registrar y procesar correctamente las matrículas convertidas y las bonificaciones generadas conforme a lo establecido en el presente acuerdo.",
        "D. Proceder al reconocimiento o aplicación de las bonificaciones que correspondan en los plazos y condiciones establecidos en el presente acuerdo.",
        "E. Mantener actualizado el sistema de bonificaciones vigente y comunicar por escrito cualquier modificación con una antelación mínima de treinta (30) días naturales, salvo que dicha modificación derive de obligaciones legales o regulatorias de aplicación inmediata."
    ]
    y = draw_bullets(c, obligaciones_empresa, margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "\n7.2 Obligaciones de EL COLABORADOR", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    y = draw_paragraph(c, "EL COLABORADOR se compromete a:", margin_x, y, width - 2*margin_x, height)
    
    obligaciones_colaborador = [
        "A. Promover, recomendar y difundir los programas formativos de LA EMPRESA de forma profesional, ética y conforme a la imagen, valores y directrices comerciales establecidas por Sports Data Campus.",
        "B. Registrar todos los leads exclusivamente a través del SIGP o de los canales oficiales establecidos por LA EMPRESA.",
        "C. Cumplir con la normativa vigente en materia de protección de datos, comunicaciones comerciales y cualquier otra regulación aplicable a su actividad.",
        "D. No ofrecer condiciones económicas, descuentos, becas, garantías o promesas que no estén expresamente autorizadas por LA EMPRESA.",
        "E. Informar a LA EMPRESA de cualquier incidencia relevante relacionada con los leads o alumnos gestionados.",
        "F. Actuar en todo momento como colaborador independiente, sin ostentar representación legal ni capacidad para obligar contractualmente a LA EMPRESA frente a terceros."
    ]
    y = draw_bullets(c, obligaciones_colaborador, margin_x, y, width - 2*margin_x, height)

    y -= 10

    # CLÁUSULA 8.- DURACIÓN Y RESOLUCIÓN DEL ACUERDO
    y = draw_paragraph(c, "OCTAVA.- DURACIÓN Y RESOLUCIÓN DEL ACUERDO", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    
    y = draw_paragraph(c, "\n8.1 Duración", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    y = draw_paragraph(c, "El presente acuerdo tendrá una duración inicial de un (1) año a contar desde la fecha de su firma[cite: 184]. Finalizado dicho período, el acuerdo se renovará automáticamente por períodos sucesivos de un (1) año, salvo que cualquiera de las partes notifique por escrito su voluntad de no renovación con una antelación mínima de treinta (30) días naturales a la fecha de vencimiento[cite: 185].", margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "\n8.2 Resolución Anticipada", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    y = draw_paragraph(c, "El presente acuerdo podrá resolverse anticipadamente en los siguientes supuestos:", margin_x, y, width - 2*margin_x, height)
    
    supuestos_resolucion = [
        "a) Por incumplimiento grave de cualquiera de las obligaciones establecidas en el presente acuerdo[cite: 188].",
        "b) Por mutuo acuerdo entre las partes, formalizado por escrito[cite: 189].",
        "c) Por decisión unilateral de cualquiera de las partes, mediante preaviso escrito con al menos treinta (30) días naturales de antelación[cite: 190]."
    ]
    y = draw_bullets(c, supuestos_resolucion, margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "\n8.3 Inactividad del Prescriptor", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    y = draw_paragraph(c, "A efectos del presente acuerdo, se considerará que EL COLABORADOR se encuentra en situación de inactividad cuando no haya registrado ningún lead válido en el SIGP durante un período continuado de tres (3) meses[cite: 192]. En tales casos, LA EMPRESA podrá considerar finalizada la participación de EL COLABORADOR en el Programa de Prescriptores o invitarle a adherirse a las condiciones vigentes del programa en ese momento[cite: 193].", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "\n8.4 Efectos de la Resolución", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    y = draw_paragraph(c, "En caso de resolución del presente acuerdo:", margin_x, y, width - 2*margin_x, height)
    
    efectos_resolucion = [
        "EL COLABORADOR dejará de tener derecho a registrar nuevos leads desde la fecha efectiva de finalización[cite: 196].",
        "Se liquidarán exclusivamente las bonificaciones reconocidas conforme a lo establecido en el presente acuerdo y que no estén sujetas a regularización conforme a las cláusulas anteriores.",
        "Las obligaciones relativas a confidencialidad, protección de datos y uso de la información permanecerán vigentes tras la finalización del acuerdo[cite: 198]."
    ]
    y = draw_bullets(c, efectos_resolucion, margin_x, y, width - 2*margin_x, height)

    y -= 10

    # CLÁUSULA 9.- CONFIDENCIALIDAD
    y = draw_paragraph(c, "NOVENA.- CONFIDENCIALIDAD", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    
    y = draw_paragraph(c, "\n9.1 Información Confidencial", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    y = draw_paragraph(c, "EL COLABORADOR se compromete a mantener la más estricta confidencialidad respecto de toda la información a la que tenga acceso como consecuencia de la ejecución del presente acuerdo[cite: 201]. A efectos del presente acuerdo, se considerará información confidencial toda aquella información técnica, comercial, estratégica, financiera o de cualquier otra naturaleza perteneciente a LA EMPRESA, incluyendo, entre otros[cite: 205, 206]:", margin_x, y, width - 2*margin_x, height)
    
    items_confidenciales = [
        "Información comercial o estratégica de Sports Data Campus; [cite: 208]",
        "Datos económicos, financieros o de facturación; [cite: 209]",
        "Condiciones comerciales o contractuales aplicables a los programas formativos; [cite: 210]",
        "Información relativa a alumnos, leads o clientes; [cite: 210]",
        "Funcionamiento interno del SIGP u otras herramientas tecnológicas utilizadas por LA EMPRESA. [cite: 211]"
    ]
    y = draw_bullets(c, items_confidenciales, margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "La información será considerada confidencial incluso cuando no esté expresamente identificada como tal, siempre que por su naturaleza razonablemente deba ser tratada como información reservada. [cite: 212]", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "\n9.2 Alcance de la Obligación", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    alcance_conf = [
        "No divulgar información confidencial a terceros sin autorización previa y por escrito de LA EMPRESA; [cite: 215]",
        "No utilizar la información confidencial para fines distintos a los derivados de la ejecución del presente acuerdo; [cite: 216]",
        "Adoptar las medidas necesarias para evitar el acceso no autorizado a dicha información. [cite: 217]"
    ]
    y = draw_bullets(c, alcance_conf, margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "\n9.3 Vigencia de la Confidencialidad", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    y = draw_paragraph(c, "La obligación de confidencialidad permanecerá vigente durante la duración del presente acuerdo y continuará en vigor durante un período mínimo de cinco (5) años tras su finalización, cualquiera que sea la causa. ", margin_x, y, width - 2*margin_x, height)

    y -= 10

    # CLÁUSULA 10.- PROTECCIÓN DE DATOS
    y = draw_paragraph(c, "DÉCIMA.- PROTECCIÓN DE DATOS", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    
    y = draw_paragraph(c, "\n10.1 Marco Normativo", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    y = draw_paragraph(c, "Las partes se comprometen a cumplir con lo dispuesto en el Reglamento (UE) 2016/679 del Parlamento Europeo y del Consejo, de 27 de abril de 2016 (RGPD), así como con la Ley Orgánica 3/2018 de Protección de Datos Personales y garantía de los derechos digitales (LOPDGDD) y demás normativa vigente en materia de protección de datos personales.", margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "\n10.2 Tratamiento de Datos", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    y = draw_paragraph(c, "EL COLABORADOR tratará los datos personales a los que tenga acceso exclusivamente para la correcta ejecución del presente acuerdo y conforme a las instrucciones de LA EMPRESA. En particular, EL COLABORADOR se compromete a:", margin_x, y, width - 2*margin_x, height)
    
    compromisos_datos = [
        "a) No utilizar los datos personales para fines propios ni distintos a los previstos en el presente acuerdo.",
        "b) No ceder los datos personales a terceros sin autorización previa y expresa de LA EMPRESA, salvo obligación legal.",
        "c) Aplicar las medidas técnicas y organizativas adecuadas para garantizar la seguridad y confidencialidad de los datos personales tratados."
    ]
    y = draw_bullets(c, compromisos_datos, margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "\n10.3 Seguridad e Incidentes", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    y = draw_paragraph(c, "EL COLABORADOR se compromete a informar a LA EMPRESA de manera inmediata en caso de detectar cualquier incidente de seguridad, acceso no autorizado, pérdida o vulneración que afecte a datos personales vinculados al presente acuerdo.", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "\n10.4 Finalización del Tratamiento", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    y = draw_paragraph(c, "A la finalización del presente acuerdo, EL COLABORADOR deberá:", margin_x, y, width - 2*margin_x, height)
    
    obligaciones_datos_fin = [
        "Eliminar o devolver a LA EMPRESA todos los datos personales a los que haya tenido acceso en el marco del presente acuerdo;",
        "Abstenerse de conservar copias de dichos datos, salvo que exista obligación legal de conservación."
    ]
    y = draw_bullets(c, obligaciones_datos_fin, margin_x, y, width - 2*margin_x, height)
    
    y -= 10

    # CLÁUSULA 11
    # CLÁUSULA 11.- SUSTITUCIÓN DE ACUERDOS ANTERIORES Y TRANSICIÓN
    y = draw_paragraph(c, "UNDÉCIMA.- SUSTITUCIÓN DE ACUERDOS ANTERIORES Y TRANSICIÓN", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    
    y = draw_paragraph(c, "\n11.1 Sustitución de Acuerdos Anteriores", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    y = draw_paragraph(c, "El presente acuerdo sustituye y deja sin efecto cualquier acuerdo, convenio o entendimiento previo existente entre las partes relativo a la participación en programas de prescripción o colaboración comercial vinculados a los programas formativos de LA EMPRESA, ya sea de naturaleza verbal o escrita.", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "En caso de contradicción entre el presente acuerdo y cualquier documento anterior suscrito entre las partes respecto del mismo objeto, prevalecerá lo dispuesto en el presente acuerdo.", margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "\n11.2 Prescriptores con Actividad Previa", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    y = draw_paragraph(c, "No obstante lo anterior, en aquellos casos en los que EL COLABORADOR hubiera generado actividad previa dentro del Programa de Prescriptores con anterioridad a la firma del presente acuerdo, LA EMPRESA podrá mantener temporalmente las condiciones previamente aplicables hasta su revisión o adaptación a las condiciones vigentes del programa.", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "\n11.3 Prescriptores Inactivos", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    
    y = draw_paragraph(c, "A efectos del presente acuerdo, se considerará que un prescriptor se encuentra en situación de inactividad cuando no haya registrado ningún lead válido en el SIGP durante un período continuado de tres (3) meses.", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "En tales casos, LA EMPRESA podrá considerar extinguido el acuerdo anterior y ofrecer al prescriptor la adhesión al modelo vigente del Programa de Prescriptores.", margin_x, y, width - 2*margin_x, height)

    y -= 10

    # CLÁUSULA 12.- LEGISLACIÓN APLICABLE Y JURISDICCIÓN
    y = draw_paragraph(c, "DUODÉCIMA.- LEGISLACIÓN APLICABLE Y JURISDICCIÓN", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    
    y = draw_paragraph(c, "El presente acuerdo tiene naturaleza mercantil y se regirá e interpretará conforme a la legislación española vigente.", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "Para la resolución de cualquier controversia, discrepancia o conflicto que pudiera derivarse de la interpretación, ejecución o validez del presente acuerdo, las partes se someten expresamente a la jurisdicción de los Juzgados y Tribunales de Valladolid, España, con renuncia expresa a cualquier otro fuero que pudiera corresponderles.", margin_x, y, width - 2*margin_x, height)

    # ESPACIO PARA FIRMAS
    # (Ya tienes la llamada a draw_signatures al final del archivo que proporcionaste)
    from sigp.services.builders.utils import draw_signatures
    draw_signatures(c, width, height, datos, y)
