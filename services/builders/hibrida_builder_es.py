# sigp/services/builders/juridica_builder_es.py

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
    
    draw_centered(c, "ACUERDO DE COLABORACIÓN COMERCIAL - PROGRAMA DE PRESCRIPTORES hibrida", width, y, size=13)
    y -= 20
    draw_centered(c, "entre", width, y, font="Helvetica", size=11)
    y -= 20
    draw_centered(c, "INNOVA TRAINING CONSULTORIA Y FORMACION S.L. SPORTS DATA CAMPUS", width, y, size=12)
    y -= 20
    draw_centered(c, "y", width, y, font="Helvetica", size=11)
    y -= 20
    draw_centered(c, nombre_entidad.upper(), width, y, size=12)

    y -= 40
    fecha_larga = spanish_long_date()
    draw_right(c, f"En {datos['ciudad']}, {fecha_larga}.", width, y)

    y -= 40
    draw_centered(c, "REUNIDOS", width, y, size=12)
    y -= 30

    y = draw_paragraph(c, "De una parte,", margin_x, y, width - 2*margin_x, height, font="Helvetica-Oblique")
    y = draw_paragraph(c, "Don Jesús Serrano Sanz, con D.N.I. nº 09.303.401-Q, actuando en su condición de Administrador Único y en nombre y representación de INNOVA TRAINING CONSULTORIA Y FORMACION S.L., propietaria de la marca comercial “Sports Data Campus”, con C.I.F. nº B19456128 y domicilio social en C/ del Campo de Gomara, 4, CP 47008, Valladolid, España (en adelante, LA EMPRESA).", margin_x, y, width - 2*margin_x, height)
    
    y -= 10
    y = draw_paragraph(c, "Y de otra parte,", margin_x, y, width - 2*margin_x, height, font="Helvetica-Oblique")
    y = draw_paragraph(c, f"Don/Doña {nombre_representante.upper()}, con {doc_type} nº {doc_num}, actuando en nombre y representación de {nombre_entidad.upper()}, con domicilio social en {domicile}, con facultades suficientes para obligar a dicha entidad en el presente acuerdo (en adelante, EL COLABORADOR).", margin_x, y, width - 2*margin_x, height)

    y -= 10
    y = draw_paragraph(c, "Ambas partes, reconociéndose mutuamente la capacidad legal necesaria para obligarse en el presente acuerdo,", margin_x, y, width - 2*margin_x, height)

    y -= 20
    draw_centered(c, "EXPONEN", width, y, size=12)
    y -= 30
    
    y = draw_paragraph(c, "Que están interesadas en establecer un marco de colaboración dentro del Programa de Prescriptores de Sports Data Campus, con el objetivo de promover y recomendar los programas formativos impartidos por LA EMPRESA.", margin_x, y, width - 2*margin_x, height)
    y = draw_paragraph(c, "En virtud de lo anterior, acuerdan formalizar el presente Acuerdo de Colaboración Comercial, que se regirá por las siguientes:", margin_x, y, width - 2*margin_x, height)

    y -= 20
    draw_centered(c, "CLÁUSULAS", width, y, size=12)
    y -= 30

    # CLÁUSULA 1
    y = draw_paragraph(c, "PRIMERA.– OBJETO DEL ACUERDO", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    y = draw_paragraph(c, "El presente acuerdo tiene por objeto regular la participación de EL COLABORADOR en el Programa de Prescriptores de Sports Data Campus, mediante el cual podrá recomendar y promover los programas formativos impartidos por LA EMPRESA, con el objetivo de facilitar la captación de potenciales alumnos interesados en dichos programas.", margin_x, y, width - 2*margin_x, height)
    y = draw_paragraph(c, "En el marco de este acuerdo, EL COLABORADOR podrá identificar y referir prospectos interesados (en adelante, leads) que serán gestionados y registrados a través del SIGP (Sistema Integral de Gestión de Prescriptores) o de las plataformas oficiales que LA EMPRESA determine.", margin_x, y, width - 2*margin_x, height)
    y = draw_paragraph(c, "El presente acuerdo regula exclusivamente la participación de EL COLABORADOR en el Programa de Prescriptores de Sports Data Campus y es independiente de cualquier otra relación profesional, comercial o institucional que pudiera existir entre las partes.", margin_x, y, width - 2*margin_x, height)
    y = draw_paragraph(c, "La actividad desarrollada por EL COLABORADOR se realizará con plena autonomía organizativa y bajo su propia responsabilidad, sin que exista en ningún caso relación laboral, societaria o de dependencia entre las partes.", margin_x, y, width - 2*margin_x, height)
    y = draw_paragraph(c, "En ningún caso EL COLABORADOR estará facultado para actuar en nombre o representación de LA EMPRESA, ni para asumir compromisos, formalizar acuerdos o modificar condiciones comerciales en nombre de Sports Data Campus frente a terceros.", margin_x, y, width - 2*margin_x, height)
    y -= 10

    # CLÁUSULA 2
    y = draw_paragraph(c, "SEGUNDA.– SISTEMA DE COMISIONES POR MATRÍCULA CONVERTIDA", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    y = draw_paragraph(c, "2.1 Comisión por Matrícula Convertida", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "EL COLABORADOR tendrá derecho a percibir una comisión económica por cada matrícula convertida que provenga de un lead válido previamente registrado en el SIGP (Sistema Integral de Gestión de Prescriptores) y asignado conforme a las reglas establecidas en el presente acuerdo.", margin_x, y, width - 2*margin_x, height)
    y = draw_paragraph(c, "A efectos del presente acuerdo, se entenderá por matrícula convertida aquella en la que el alumno referido por EL COLABORADOR haya formalizado su inscripción en un programa formativo impartido por LA EMPRESA y haya realizado el pago efectivo que activa el devengo de la comisión correspondiente.", margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "2.2 Importe de las Comisiones", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "Las comisiones aplicables serán las siguientes:", margin_x, y, width - 2*margin_x, height)
    
    comisiones_list = [
        "Másteres impartidos en inglés: 300€ por matrícula convertida.",
        "Másteres impartidos en español o portugués: 150€ por matrícula convertida.",
        "Diplomados y cursos de más corta duración: 50€."
    ]
    y = draw_bullets(c, comisiones_list, margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "LA EMPRESA podrá actualizar el presente sistema de comisiones cuando existan cambios en su política comercial o en su estructura de programas formativos, comprometiéndose a comunicar dichas modificaciones con una antelación mínima de treinta (30) días naturales.", margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "2.3 Condiciones Económicas", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "Las comisiones establecidas en el presente acuerdo se entenderán como importes brutos, impuestos indirectos y tasas incluidas, quedando sujetos, en cada caso, a la normativa fiscal aplicable según la naturaleza jurídica, situación fiscal y procedencia de EL COLABORADOR.", margin_x, y, width - 2*margin_x, height)
    y = draw_paragraph(c, "En caso de que EL COLABORADOR sea una persona jurídica o profesional obligado a emitir factura, las comisiones serán abonadas previa presentación de la correspondiente factura conforme a la legislación vigente.", margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "2.4 Registro y Determinación de Comisiones", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "Todas las matrículas convertidas, así como las comisiones correspondientes, serán registradas en el SIGP, que constituirá la única fuente válida para la determinación de:", margin_x, y, width - 2*margin_x, height)
    y = draw_bullets(c, ["Asignación del lead", "Conversión en matrícula", "Importe de la comisión aplicable", "Estado de devengo y liquidación."], margin_x, y, width - 2*margin_x, height)
    y -= 10

    # CLÁUSULA 3
    y = draw_paragraph(c, "TERCERA.– DEVENGO Y LIQUIDACIÓN DE LAS COMISIONES", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    y = draw_paragraph(c, "3.1 Devengo de la Comisión", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "La comisión correspondiente a una matrícula convertida se devengará en el momento en que el alumno referido por EL COLABORADOR haya realizado el pago efectivo de la matrícula del programa formativo correspondiente y dicho pago haya sido recibido y validado por LA EMPRESA conforme a sus sistemas internos de cobro.", margin_x, y, width - 2*margin_x, height)
    y = draw_paragraph(c, "A efectos del presente acuerdo, se entenderá por pago efectivo de matrícula aquel pago inicial o confirmación de inscripción que permita formalizar la incorporación del alumno al programa formativo correspondiente conforme a los procedimientos administrativos de LA EMPRESA.", margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "3.2 Validación de las Comisiones", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "Las comisiones devengadas serán verificadas por el departamento de Administración de LA EMPRESA, quien confirmará la validez de la matrícula, la asignación del lead y la inexistencia de incidencias financieras asociadas al pago realizado por el alumno.", margin_x, y, width - 2*margin_x, height)
    y = draw_paragraph(c, "Una vez validada la información correspondiente, la comisión quedará aprobada para su liquidación.", margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "3.3 Liquidación y Pago", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "Las comisiones aprobadas serán liquidadas con periodicidad mensual.", margin_x, y, width - 2*margin_x, height)
    y = draw_paragraph(c, "El pago se realizará a partir de los primeros diez (10) días hábiles del mes siguiente al devengo de la comisión, siempre que se haya recibido la correspondiente factura por parte de EL COLABORADOR en caso de que sea necesaria conforme a la normativa fiscal aplicable.", margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "3.4 Condiciones para el Pago", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "El pago de las comisiones estará sujeto a las siguientes condiciones:", margin_x, y, width - 2*margin_x, height)
    y = draw_bullets(c, [
        "Que la matrícula haya sido validada conforme a los sistemas de LA EMPRESA;",
        "Que el pago del alumno no haya sido objeto de devolución, retrocesión bancaria o incidencia financiera;",
        "Que la asignación del lead figure correctamente registrada en el SIGP."
    ], margin_x, y, width - 2*margin_x, height)
    y -= 10

    # CLÁUSULA 4
    y = draw_paragraph(c, "CUARTA.– GESTIÓN DE BAJAS Y AJUSTES", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    y = draw_paragraph(c, "4.1 Supuestos de Regularización", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "Las comisiones devengadas conforme a la Cláusula Segunda podrán estar sujetas a regularización en los siguientes supuestos:", margin_x, y, width - 2*margin_x, height)
    y = draw_bullets(c, [
        "a) Cuando el programa formativo no sea finalmente impartido por causas organizativas o por no alcanzarse el número mínimo de alumnos.",
        "b) Cuando el alumno ejerza su derecho de desistimiento o solicite la baja dentro de los plazos legal o contractualmente establecidos por LA EMPRESA.",
        "c) Cuando se produzca la devolución total o parcial del importe abonado por el alumno por cualquier causa debidamente justificada.",
        "d) Cuando exista impago, retrocesión bancaria, chargeback o cualquier incidencia financiera que implique la anulación total o parcial del pago que dio origen al devengo de la comisión."
    ], margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "4.2 Efectos de la Regularización", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "En los supuestos descritos en el apartado anterior:", margin_x, y, width - 2*margin_x, height)
    y = draw_bullets(c, [
        "Si la comisión aún no hubiera sido abonada, no se procederá a su liquidación.",
        "Si la comisión ya hubiera sido abonada, el importe correspondiente podrá ser compensado en la siguiente liquidación mensual mediante el sistema de cuenta corriente entre las partes.",
        "En el caso de que no haya futuras facturas, el importe deberá ser devuelto por el prescriptor por el mismo medio de pago que lo haya recibido."
    ], margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "4.3 Sistema de Cuenta Corriente", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "A efectos de gestión económica entre las partes, se establece un sistema de cuenta corriente, en el cual se reflejarán:", margin_x, y, width - 2*margin_x, height)
    y = draw_bullets(c, ["Débitos: comisiones devengadas a favor de EL COLABORADOR.", "Créditos: ajustes derivados de cancelaciones, devoluciones o incidencias financieras."], margin_x, y, width - 2*margin_x, height)
    y = draw_paragraph(c, "En el caso de que el prescriptor no cuente con crédito, deberá devolver los importes oportunos derivados de los casos anteriores, por el mismo medio de pago por el que haya recibido las comisiones. La compensación de saldos podrá realizarse automáticamente en liquidaciones posteriores hasta la total regularización del importe correspondiente.", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "4.4 Registro y Transparencia", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "Todas las incidencias, cancelaciones, devoluciones o ajustes relacionados con matrículas convertidas serán registradas en el SIGP, que constituirá la única fuente válida para la determinación del estado de cada matrícula y de las comisiones asociadas.", margin_x, y, width - 2*margin_x, height)
    y -= 10

    # CLÁUSULA 5
    y = draw_paragraph(c, "QUINTA.– CONTROL DE CALIDAD Y GESTIÓN DE LEADS", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    y = draw_paragraph(c, "5.1 Definición de Lead Válido", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "A efectos del presente acuerdo, se considerará lead válido aquel prospecto que cumpla simultáneamente con las siguientes condiciones:", margin_x, y, width - 2*margin_x, height)
    y = draw_bullets(c, [
        "a) Proporcione datos de contacto completos, veraces y verificables.",
        "b) Manifieste un interés real en los programas formativos de LA EMPRESA.",
        "c) Cumpla con los requisitos mínimos de acceso al programa formativo correspondiente.",
        "d) No constituya información duplicada, fraudulenta o previamente registrada en el SIGP por otro prescriptor dentro del período de asignación vigente."
    ], margin_x, y, width - 2*margin_x, height)
    y = draw_paragraph(c, "LA EMPRESA se reserva el derecho de validar la condición de lead válido conforme a los criterios internos establecidos en el SIGP.", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "5.2 Registro y Asignación de Leads", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "Para que un lead pueda generar derecho a comisión, deberá ser registrado previamente en el SIGP (Sistema Integral de Gestión de Prescriptores) o en las plataformas oficiales que LA EMPRESA determine. La asignación del lead corresponderá al prescriptor que lo haya registrado correctamente en el SIGP en primer lugar.", margin_x, y, width - 2*margin_x, height)
    y = draw_paragraph(c, "Dicha asignación permanecerá vigente durante un período de seis (6) meses desde la fecha de registro. Transcurrido dicho plazo sin que se haya producido una matrícula convertida, el lead podrá ser trabajado por otros prescriptores, perdiendo el primero la exclusividad sobre el mismo.", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "5.3 Trazabilidad y Determinación de la Titularidad", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "La antigüedad, titularidad y estado de los leads se determinarán exclusivamente mediante el registro efectuado en el SIGP, el cual dispone de sistema de auditoría y registro interno de actividad. El SIGP constituirá la única fuente válida y vinculante para la determinación de: La titularidad del lead, La fecha de registro, La conversión en matrícula, El devengo y estado de la comisión.", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "5.4 Territorialidad y Exclusividad", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "Dado que la actividad formativa de LA EMPRESA se desarrolla principalmente en modalidad online, el presente acuerdo no establece exclusividad territorial. EL COLABORADOR podrá promover los programas formativos en cualquier ámbito geográfico. La comisión corresponderá exclusivamente al prescriptor que haya registrado válidamente el lead en el SIGP dentro del período de asignación establecido.", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "5.5 Resolución de Controversias", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "En caso de controversia sobre la titularidad de un lead o sobre la asignación de una matrícula convertida, LA EMPRESA resolverá la incidencia tomando como referencia la información registrada en el SIGP y los criterios internos de validación del Programa de Prescriptores.", margin_x, y, width - 2*margin_x, height)
    y -= 10

    # CLÁUSULA 6
    y = draw_paragraph(c, "SEXTA.– PROPIEDAD DE LA BASE DE DATOS Y USO DE LA INFORMACIÓN", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    y = draw_paragraph(c, "6.1 Titularidad de los Datos", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "Todos los leads, datos de contacto, información comercial y cualquier otro dato generado, captado o gestionado en el marco del presente acuerdo serán propiedad exclusiva de LA EMPRESA. Dicha información será gestionada a través del SIGP (Sistema Integral de Gestión de Prescriptores) o de las plataformas oficiales que LA EMPRESA determine.", margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "6.2 Limitación de Uso", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "EL COLABORADOR no adquiere ningún derecho de propiedad, titularidad o explotación sobre los datos generados en el marco del presente acuerdo. EL COLABORADOR se compromete a utilizar dicha información exclusivamente para los fines establecidos en el presente acuerdo y conforme a las instrucciones y directrices de LA EMPRESA, respetando en todo momento la legislación vigente de Protección de Datos de cada territorio.", margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "6.3 Prohibición de Uso Externo", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "Queda expresamente prohibido que EL COLABORADOR:", margin_x, y, width - 2*margin_x, height)
    y = draw_bullets(c, [
        "Utilice los datos obtenidos en el marco del presente acuerdo para fines distintos a la promoción de los programas formativos de LA EMPRESA;",
        "Incorpore los datos a bases de datos propias o de terceros;",
        "Comercialice productos o servicios ajenos a LA EMPRESA utilizando la información obtenida durante la vigencia del presente acuerdo."
    ], margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "6.4 Finalización del Acuerdo", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "A la finalización del presente acuerdo, cualquiera que sea la causa, EL COLABORADOR deberá:", margin_x, y, width - 2*margin_x, height)
    y = draw_bullets(c, [
        "Cesar inmediatamente en el uso de los datos y de cualquier información obtenida a través del Programa de Prescriptores;",
        "Eliminar o destruir cualquier copia o registro de datos que obre en su poder;",
        "Abstenerse de contactar nuevamente a los leads generados en el marco del presente acuerdo, salvo autorización expresa y por escrito de LA EMPRESA."
    ], margin_x, y, width - 2*margin_x, height)
    y -= 10

    # CLÁUSULA 7
    y = draw_paragraph(c, "SÉPTIMA – OBLIGACIONES DE LAS PARTES", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    y = draw_paragraph(c, "7.1 Obligaciones de LA EMPRESA", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_bullets(c, [
        "Proporcionar a EL COLABORADOR la información comercial, materiales promocionales y documentación necesaria para la correcta promoción de los programas formativos.",
        "Facilitar el acceso al SIGP (Sistema Integral de Gestión de Prescriptores) u otras herramientas oficiales necesarias para el registro y seguimiento de leads.",
        "Registrar y procesar correctamente las matrículas convertidas y las comisiones devengadas conforme a lo establecido en el presente acuerdo.",
        "Proceder al pago de las comisiones que correspondan en los plazos y condiciones establecidos en el acuerdo.",
        "Mantener actualizado el sistema de comisiones vigente y comunicar por escrito cualquier modificación con una antelación mínima de treinta (30) días naturales, salvo que dicha modificación derive de obligaciones legales o regulatorias de aplicación inmediata."
    ], margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "7.2 Obligaciones de EL COLABORADOR", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_bullets(c, [
        "Promover los programas formativos de LA EMPRESA de forma profesional, ética y conforme a la imagen, valores y directrices comerciales establecidas por Sports Data Campus.",
        "Registrar todos los leads exclusivamente a través del SIGP o de los canales oficiales establecidos por LA EMPRESA.",
        "Cumplir con la normativa vigente en materia de protección de datos, comunicaciones comerciales y cualquier otra regulación aplicable a su actividad.",
        "No ofrecer condiciones económicas, descuentos, becas, garantías o promesas que no estén expresamente autorizadas por LA EMPRESA.",
        "Informar a LA EMPRESA de cualquier incidencia relevante relacionada con los leads o alumnos gestionados.",
        "Actuar en todo momento como colaborador independiente, sin ostentar representación legal ni capacidad para obligar contractualmente a LA EMPRESA frente a terceros."
    ], margin_x, y, width - 2*margin_x, height)
    y -= 10

    # CLÁUSULA 8
    y = draw_paragraph(c, "OCTAVA.– DURACIÓN Y RESOLUCIÓN DEL ACUERDO", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    y = draw_paragraph(c, "8.1 Duración", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "El presente acuerdo tendrá una duración inicial de un (1) año a contar desde la fecha de su firma. Finalizado dicho período, el acuerdo se renovará automáticamente por períodos sucesivos de un (1) año, salvo que cualquiera de las partes notifique por escrito su voluntad de no renovación con una antelación mínima de treinta (30) días naturales a la fecha de vencimiento.", margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "8.2 Resolución Anticipada", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "El presente acuerdo podrá resolverse anticipadamente en los siguientes supuestos:", margin_x, y, width - 2*margin_x, height)
    y = draw_bullets(c, [
        "a) Por incumplimiento grave de cualquiera de las obligaciones establecidas en el presente acuerdo.",
        "b) Por mutuo acuerdo entre las partes, formalizado por escrito.",
        "c) Por decisión unilateral de cualquiera de las partes, mediante preaviso escrito con al menos treinta (30) días naturales de antelación."
    ], margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "8.3 Inactividad del Prescriptor", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "A efectos del presente acuerdo, se considerará que EL COLABORADOR se encuentra en situación de inactividad cuando no haya registrado ningún lead válido en el SIGP durante un período continuado de tres (3) meses. En tales casos, LA EMPRESA podrá considerar finalizada la participación de EL COLABORADOR en el Programa de Prescriptores o invitarle a adherirse a las condiciones vigentes del programa en ese momento.", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "8.4 Efectos de la Resolución", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "En caso de resolución del presente acuerdo:", margin_x, y, width - 2*margin_x, height)
    y = draw_bullets(c, [
        "EL COLABORADOR dejará de tener derecho a registrar nuevos leads desde la fecha efectiva de finalización.",
        "Se liquidarán exclusivamente las comisiones devengadas conforme a lo establecido en el presente acuerdo y que no estén sujetas a regularización conforme a las cláusulas anteriores.",
        "Las obligaciones relativas a confidencialidad, protección de datos y uso de la información permanecerán vigentes tras la finalización del acuerdo."
    ], margin_x, y, width - 2*margin_x, height)
    y -= 10

    # CLÁUSULA 9
    y = draw_paragraph(c, "NOVENA.– CONFIDENCIALIDAD", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    y = draw_paragraph(c, "9.1 Información Confidencial", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "EL COLABORADOR se compromete a mantener la más estricta confidencialidad respecto de toda la información a la que tenga acceso como consecuencia de la ejecución del presente acuerdo.", margin_x, y, width - 2*margin_x, height)
    y = draw_paragraph(c, "A efectos del presente acuerdo, se considerará información confidencial toda aquella información técnica, comercial, estratégica, financiera o de cualquier otra naturaleza perteneciente a LA EMPRESA, incluyendo, entre otros: Información comercial o estratégica de Sports Data Campus; Datos económicos, financieros o de facturación; Condiciones comerciales o contractuales aplicables a los programas formativos; Información relativa a alumnos, leads o clientes; Funcionamiento interno del SIGP u otras herramientas tecnológicas utilizadas por LA EMPRESA. La información será considerada confidencial incluso cuando no esté expresamente identificada como tal, siempre que por su naturaleza razonablemente deba ser tratada como información reservada.", margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "9.2 Alcance de la Obligación", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_bullets(c, [
        "No divulgar información confidencial a terceros sin autorización previa y por escrito de LA EMPRESA;",
        "No utilizar la información confidencial para fines distintos a los derivados de la ejecución del presente acuerdo;",
        "Adoptar las medidas necesarias para evitar el acceso no autorizado a dicha información."
    ], margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "9.3 Vigencia de la Confidencialidad", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "La obligación de confidencialidad permanecerá vigente durante la duración del presente acuerdo y continuará en vigor durante un período mínimo de cinco (5) años tras su finalización, cualquiera que sea la causa.", margin_x, y, width - 2*margin_x, height)
    y -= 10

    # CLÁUSULA 10
    y = draw_paragraph(c, "DÉCIMA.– PROTECCIÓN DE DATOS", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    y = draw_paragraph(c, "10.1 Marco Normativo", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "Las partes se comprometen a cumplir con lo dispuesto en el Reglamento (UE) 2016/679 del Parlamento Europeo y del Consejo, de 27 de abril de 2016 (RGPD), así como con la Ley Orgánica 3/2018 de Protección de Datos Personales y garantía de los derechos digitales (LOPDGDD) y demás normativa vigente en materia de protección de datos personales.", margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "10.2 Tratamiento de Datos", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "EL COLABORADOR tratará los datos personales a los que tenga acceso exclusivamente para la correcta ejecución del presente acuerdo y conforme a las instrucciones de LA EMPRESA. En particular, EL COLABORADOR se compromete a:", margin_x, y, width - 2*margin_x, height)
    y = draw_bullets(c, [
        "a) No utilizar los datos personales para fines propios ni distintos a los previstos en el presente acuerdo.",
        "b) No ceder los datos personales a terceros sin autorización previa y expresa de LA EMPRESA, salvo obligación legal.",
        "c) Aplicar las medidas técnicas y organizativas adecuadas para garantizar la seguridad y confidencialidad de los datos personales tratados."
    ], margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "10.3 Seguridad e Incidentes", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "EL COLABORADOR se compromete a informar a LA EMPRESA de manera inmediata en caso de detectar cualquier incidente de seguridad, acceso no autorizado, pérdida o vulneración que afecte a datos personales vinculados al presente acuerdo.", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "10.4 Finalización del Tratamiento", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "A la finalización del presente acuerdo, EL COLABORADOR deberá: Eliminar o devolver a LA EMPRESA todos los datos personales a los que haya tenido acceso en el marco del presente acuerdo; Abstenerse de conservar copias de dichos datos, salvo que exista obligación legal de conservación.", margin_x, y, width - 2*margin_x, height)
    y -= 10

    # CLÁUSULA 11
    y = draw_paragraph(c, "UNDÉCIMA – SUSTITUCIÓN DE ACUERDOS ANTERIORES Y TRANSICIÓN", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    y = draw_paragraph(c, "11.1 Sustitución de Acuerdos Anteriores", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "El presente acuerdo sustituye y deja sin efecto cualquier acuerdo, convenio o entendimiento previo existente entre las partes relativo a la participación en programas de prescripción o colaboración comercial vinculados a los programas formativos de LA EMPRESA, ya sea de naturaleza verbal o escrita. En caso de contradicción entre el presente acuerdo y cualquier documento anterior suscrito entre las partes respecto del mismo objeto, prevalecerá lo dispuesto en el presente acuerdo.", margin_x, y, width - 2*margin_x, height)
    
    y = draw_paragraph(c, "11.2 Prescriptores con Actividad Previa", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "No obstante lo anterior, en aquellos casos en los que EL COLABORADOR hubiera generado actividad comercial efectiva con anterioridad a la firma del presente acuerdo, LA EMPRESA podrá mantener temporalmente las condiciones previamente pactadas hasta su revisión o renegociación expresa entre las partes.", margin_x, y, width - 2*margin_x, height)

    y = draw_paragraph(c, "11.3 Prescriptores Inactivos", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold", size=10)
    y = draw_paragraph(c, "A efectos del presente acuerdo, se considerará que un prescriptor se encuentra en situación de inactividad cuando no haya registrado ningún lead válido en el SIGP durante un período continuado de tres (3) meses. En tales casos, LA EMPRESA podrá considerar extinguido el acuerdo anterior y ofrecer al prescriptor la adhesión al modelo vigente del Programa de Prescriptores.", margin_x, y, width - 2*margin_x, height)
    y -= 10

    # CLÁUSULA 12
    y = draw_paragraph(c, "DUODÉCIMA.– LEGISLACIÓN APLICABLE Y JURISDICCIÓN", margin_x, y, width - 2*margin_x, height, font="Helvetica-Bold")
    y = draw_paragraph(c, "El presente acuerdo tiene naturaleza mercantil y se regirá e interpretará conforme a la legislación española vigente. Para la resolución de cualquier controversia, discrepancia o conflicto que pudiera derivarse de la interpretación, ejecución o validez del presente acuerdo, las partes se someten expresamente a la jurisdicción de los Juzgados y Tribunales de Valladolid, España, con renuncia expresa a cualquier otro fuero que pudiera corresponderles.", margin_x, y, width - 2*margin_x, height)

    # FINAL: CAJAS DE FIRMA
    # Nos aseguramos de que haya espacio para las firmas, si no, forzamos salto de página.
    if y < 220:
        c.showPage()
        y = height - 72
        draw_header(c, width, height)
        
    y_sig_base = y - 100
    c.setFont("Helvetica", 10)
    
    # Firma Presidente
    c.drawString(80, y_sig_base + 65, "Por Innova Training:")
    c.drawString(80, y_sig_base + 53, "Jesús Serrano Sanz")
    c.drawString(80, y_sig_base + 41, "Presidente y Administrador Único")
    c.rect(80, y_sig_base - 20, 220, 55)
    
    # Firma Prescriptor
    c.drawString(320, y_sig_base + 65, "Por EL COLABORADOR:")
    c.drawString(320, y_sig_base + 53, nombre_representante)
    c.rect(320, y_sig_base - 20, 220, 55)