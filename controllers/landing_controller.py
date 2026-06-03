"""Landing pública por prescriptor.

Proporciona una página pública (sin autenticación) que muestra la información básica
 del prescriptor y un formulario para que un interesado deje sus datos. Dicho
 formulario crea un registro en la tabla `leads` ligado al prescriptor.
"""
from __future__ import annotations

import uuid
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional

from sigp import db
from sigp.models import Base

# Tablas reflejadas
Prescriptor = getattr(Base.classes, "prescriptors", None)
Lead = getattr(Base.classes, "leads", None)
Program = getattr(Base.classes, "programs", None)
# En la mayoría de los despliegues el estado "NUEVO" suele tener id=1. Si no
# existiera dicha tabla o el id fuese distinto, simplemente se insertará el id
# declarado a continuación sin romper la inserción.
DEFAULT_LEAD_STATE_ID = 1

landing_bp = Blueprint("landing", __name__, url_prefix="/p")


from wtforms.validators import ValidationError
from sqlalchemy import func


COUNTRY_CALLING_CODES = [
    ("AF", "Afganistán", "+93"), ("AL", "Albania", "+355"), ("DE", "Alemania", "+49"),
    ("AD", "Andorra", "+376"), ("AO", "Angola", "+244"), ("AI", "Anguila", "+1"),
    ("AQ", "Antártida", "+672"), ("AG", "Antigua y Barbuda", "+1"), ("SA", "Arabia Saudita", "+966"),
    ("DZ", "Argelia", "+213"), ("AR", "Argentina", "+54"), ("AM", "Armenia", "+374"),
    ("AW", "Aruba", "+297"), ("AU", "Australia", "+61"), ("AT", "Austria", "+43"),
    ("AZ", "Azerbaiyán", "+994"), ("BS", "Bahamas", "+1"), ("BH", "Baréin", "+973"),
    ("BD", "Bangladés", "+880"), ("BB", "Barbados", "+1"), ("BE", "Bélgica", "+32"),
    ("BZ", "Belice", "+501"), ("BJ", "Benín", "+229"), ("BM", "Bermudas", "+1"),
    ("BY", "Bielorrusia", "+375"), ("BO", "Bolivia", "+591"), ("BA", "Bosnia y Herzegovina", "+387"),
    ("BW", "Botsuana", "+267"), ("BR", "Brasil", "+55"), ("BN", "Brunéi", "+673"),
    ("BG", "Bulgaria", "+359"), ("BF", "Burkina Faso", "+226"), ("BI", "Burundi", "+257"),
    ("BT", "Bután", "+975"), ("CV", "Cabo Verde", "+238"), ("KH", "Camboya", "+855"),
    ("CM", "Camerún", "+237"), ("CA", "Canadá", "+1"), ("BQ", "Caribe Neerlandés", "+599"),
    ("QA", "Catar", "+974"), ("TD", "Chad", "+235"), ("CL", "Chile", "+56"),
    ("CN", "China", "+86"), ("CY", "Chipre", "+357"), ("VA", "Ciudad del Vaticano", "+39"),
    ("CO", "Colombia", "+57"), ("KM", "Comoras", "+269"), ("CG", "Congo", "+242"),
    ("CD", "Congo, República Democrática", "+243"), ("KR", "Corea del Sur", "+82"), ("KP", "Corea del Norte", "+850"),
    ("CI", "Costa de Marfil", "+225"), ("CR", "Costa Rica", "+506"), ("HR", "Croacia", "+385"),
    ("CU", "Cuba", "+53"), ("CW", "Curazao", "+599"), ("DK", "Dinamarca", "+45"),
    ("DM", "Dominica", "+1"), ("EC", "Ecuador", "+593"), ("EG", "Egipto", "+20"),
    ("SV", "El Salvador", "+503"), ("AE", "Emiratos Árabes Unidos", "+971"), ("ER", "Eritrea", "+291"),
    ("SK", "Eslovaquia", "+421"), ("SI", "Eslovenia", "+386"), ("ES", "España", "+34"),
    ("US", "Estados Unidos", "+1"), ("EE", "Estonia", "+372"), ("SZ", "Esuatini", "+268"),
    ("ET", "Etiopía", "+251"), ("PH", "Filipinas", "+63"), ("FI", "Finlandia", "+358"),
    ("FJ", "Fiyi", "+679"), ("FR", "Francia", "+33"), ("GA", "Gabón", "+241"),
    ("GM", "Gambia", "+220"), ("GE", "Georgia", "+995"), ("GH", "Ghana", "+233"),
    ("GI", "Gibraltar", "+350"), ("GD", "Granada", "+1"), ("GR", "Grecia", "+30"),
    ("GL", "Groenlandia", "+299"), ("GP", "Guadalupe", "+590"), ("GU", "Guam", "+1"),
    ("GT", "Guatemala", "+502"), ("GF", "Guayana Francesa", "+594"), ("GG", "Guernsey", "+44"),
    ("GN", "Guinea", "+224"), ("GQ", "Guinea Ecuatorial", "+240"), ("GW", "Guinea-Bisáu", "+245"),
    ("GY", "Guyana", "+592"), ("HT", "Haití", "+509"), ("HN", "Honduras", "+504"),
    ("HK", "Hong Kong", "+852"), ("HU", "Hungría", "+36"), ("IN", "India", "+91"),
    ("ID", "Indonesia", "+62"), ("IQ", "Irak", "+964"), ("IR", "Irán", "+98"),
    ("IE", "Irlanda", "+353"), ("AC", "Isla Ascensión", "+247"), ("IM", "Isla de Man", "+44"),
    ("CX", "Isla de Navidad", "+61"), ("NF", "Isla Norfolk", "+672"), ("IS", "Islandia", "+354"),
    ("KY", "Islas Caimán", "+1"), ("CC", "Islas Cocos", "+61"), ("CK", "Islas Cook", "+682"),
    ("FO", "Islas Feroe", "+298"), ("FK", "Islas Malvinas", "+500"), ("MP", "Islas Marianas del Norte", "+1"),
    ("MH", "Islas Marshall", "+692"), ("PN", "Islas Pitcairn", "+64"), ("SB", "Islas Salomón", "+677"),
    ("TC", "Islas Turcas y Caicos", "+1"), ("VG", "Islas Vírgenes Británicas", "+1"), ("VI", "Islas Vírgenes de EE. UU.", "+1"),
    ("IL", "Israel", "+972"), ("IT", "Italia", "+39"), ("JM", "Jamaica", "+1"),
    ("JP", "Japón", "+81"), ("JE", "Jersey", "+44"), ("JO", "Jordania", "+962"),
    ("KZ", "Kazajistán", "+7"), ("KE", "Kenia", "+254"), ("KG", "Kirguistán", "+996"),
    ("KI", "Kiribati", "+686"), ("XK", "Kosovo", "+383"), ("KW", "Kuwait", "+965"),
    ("LA", "Laos", "+856"), ("LS", "Lesoto", "+266"), ("LV", "Letonia", "+371"),
    ("LB", "Líbano", "+961"), ("LR", "Liberia", "+231"), ("LY", "Libia", "+218"),
    ("LI", "Liechtenstein", "+423"), ("LT", "Lituania", "+370"), ("LU", "Luxemburgo", "+352"),
    ("MO", "Macao", "+853"), ("MK", "Macedonia del Norte", "+389"), ("MG", "Madagascar", "+261"),
    ("MY", "Malasia", "+60"), ("MW", "Malaui", "+265"), ("MV", "Maldivas", "+960"),
    ("ML", "Malí", "+223"), ("MT", "Malta", "+356"), ("MA", "Marruecos", "+212"),
    ("MQ", "Martinica", "+596"), ("MU", "Mauricio", "+230"), ("MR", "Mauritania", "+222"),
    ("YT", "Mayotte", "+262"), ("MX", "México", "+52"), ("FM", "Micronesia", "+691"),
    ("MD", "Moldavia", "+373"), ("MC", "Mónaco", "+377"), ("MN", "Mongolia", "+976"),
    ("ME", "Montenegro", "+382"), ("MS", "Montserrat", "+1"), ("MZ", "Mozambique", "+258"),
    ("MM", "Myanmar", "+95"), ("NA", "Namibia", "+264"), ("NR", "Nauru", "+674"),
    ("NP", "Nepal", "+977"), ("NI", "Nicaragua", "+505"), ("NE", "Níger", "+227"),
    ("NG", "Nigeria", "+234"), ("NU", "Niue", "+683"), ("NO", "Noruega", "+47"),
    ("NC", "Nueva Caledonia", "+687"), ("NZ", "Nueva Zelanda", "+64"), ("OM", "Omán", "+968"),
    ("NL", "Países Bajos", "+31"), ("PK", "Pakistán", "+92"), ("PW", "Palaos", "+680"),
    ("PS", "Palestina", "+970"), ("PA", "Panamá", "+507"), ("PG", "Papúa Nueva Guinea", "+675"),
    ("PY", "Paraguay", "+595"), ("PE", "Perú", "+51"), ("PF", "Polinesia Francesa", "+689"),
    ("PL", "Polonia", "+48"), ("PT", "Portugal", "+351"), ("PR", "Puerto Rico", "+1"),
    ("GB", "Reino Unido", "+44"), ("CF", "República Centroafricana", "+236"), ("CZ", "República Checa", "+420"),
    ("DO", "República Dominicana", "+1"), ("RE", "Reunión", "+262"), ("RW", "Ruanda", "+250"),
    ("RO", "Rumanía", "+40"), ("RU", "Rusia", "+7"), ("EH", "Sahara Occidental", "+212"),
    ("WS", "Samoa", "+685"), ("AS", "Samoa Americana", "+1"), ("BL", "San Bartolomé", "+590"),
    ("KN", "San Cristóbal y Nieves", "+1"), ("SM", "San Marino", "+378"), ("MF", "San Martín", "+590"),
    ("PM", "San Pedro y Miquelón", "+508"), ("VC", "San Vicente y las Granadinas", "+1"),
    ("SH", "Santa Elena", "+290"), ("LC", "Santa Lucía", "+1"), ("ST", "Santo Tomé y Príncipe", "+239"),
    ("SN", "Senegal", "+221"), ("RS", "Serbia", "+381"), ("SC", "Seychelles", "+248"),
    ("SL", "Sierra Leona", "+232"), ("SG", "Singapur", "+65"), ("SX", "Sint Maarten", "+1"),
    ("SY", "Siria", "+963"), ("SO", "Somalia", "+252"), ("LK", "Sri Lanka", "+94"),
    ("ZA", "Sudáfrica", "+27"), ("SD", "Sudán", "+249"), ("SS", "Sudán del Sur", "+211"),
    ("SE", "Suecia", "+46"), ("CH", "Suiza", "+41"), ("SR", "Surinam", "+597"),
    ("SJ", "Svalbard y Jan Mayen", "+47"), ("TH", "Tailandia", "+66"), ("TW", "Taiwán", "+886"),
    ("TZ", "Tanzania", "+255"), ("TJ", "Tayikistán", "+992"), ("IO", "Territorio Británico del Océano Índico", "+246"),
    ("TL", "Timor Oriental", "+670"), ("TG", "Togo", "+228"), ("TK", "Tokelau", "+690"),
    ("TO", "Tonga", "+676"), ("TT", "Trinidad y Tobago", "+1"), ("TN", "Túnez", "+216"),
    ("TM", "Turkmenistán", "+993"), ("TR", "Turquía", "+90"), ("TV", "Tuvalu", "+688"),
    ("UA", "Ucrania", "+380"), ("UG", "Uganda", "+256"), ("UY", "Uruguay", "+598"),
    ("UZ", "Uzbekistán", "+998"), ("VU", "Vanuatu", "+678"), ("VE", "Venezuela", "+58"),
    ("VN", "Vietnam", "+84"), ("WF", "Wallis y Futuna", "+681"), ("YE", "Yemen", "+967"),
    ("DJ", "Yibuti", "+253"), ("ZM", "Zambia", "+260"), ("ZW", "Zimbabue", "+263"),
]


def _flag_emoji(country_code: str) -> str:
    if len(country_code) != 2 or not country_code.isalpha():
        return ""
    return "".join(chr(127397 + ord(char)) for char in country_code.upper())


def _country_code_choices() -> list[tuple[str, str]]:
    choices = [
        (dial_code, f"{_flag_emoji(iso_code)} {name} {dial_code}")
        for iso_code, name, dial_code in COUNTRY_CALLING_CODES
    ]
    return sorted(choices, key=lambda item: (item[0] != "+34", item[1]))


class PublicLeadForm(FlaskForm):
    """Formulario de captación visible en la landing."""

    name = StringField("Nombre", validators=[DataRequired(), Length(max=100)])
    email = StringField("Email", validators=[Optional(), Email(), Length(max=255)])
    country_code = SelectField(
        "Código país",
        choices=_country_code_choices(),
        validators=[DataRequired(message="Seleccione el código de país")],
    )
    cellular = StringField("Celular", validators=[DataRequired(message="Ingrese su celular"), Length(max=50)])
    program_info_id = SelectField("Programa", coerce=str, validators=[DataRequired(message="Seleccione un programa")])
    observations = TextAreaField("Observaciones", validators=[Optional(), Length(max=500)])

    def validate_email(self, field):
        email = (field.data or "").strip().lower()
        if not email:
            return
        LeadTbl = getattr(Base.classes, "leads", None)
        if LeadTbl is None:
            return
        exists = db.session.query(LeadTbl).filter(func.lower(LeadTbl.candidate_email) == email).first()
        if exists:
            raise ValidationError("Este correo ya está registrado.")

    def validate_cellular(self, field):
        cellular_number = "".join(ch for ch in (field.data or "") if ch.isdigit())
        if not cellular_number:
            raise ValidationError("Ingrese un número de celular válido.")
    submit = SubmitField("Me interesa")

    class Meta:
        csrf = True


@landing_bp.route("/<prescriptor_id>", methods=["GET", "POST"])
def landing_page(prescriptor_id: str):
    """Renderiza la landing y procesa la generación de un lead."""

    if Prescriptor is None:
        flash("Módulo de prescriptores no disponible", "danger")
        return redirect("/")

    prescriptor = db.session.get(Prescriptor, prescriptor_id)
    if prescriptor is None:
        flash("Página no encontrada", "warning")
        return redirect("/")

    form = PublicLeadForm()
    # Poblar choices con programas activos asignados al prescriptor.
    PrescComm = getattr(Base.classes, "prescriptor_commission", None)
    if Program is not None and PrescComm is not None:
        prog_rows = (
            db.session.query(Program)
            .join(PrescComm, PrescComm.program_id == Program.id)
            .filter(PrescComm.prescriptor_id == prescriptor_id)
            .filter(Program.state == "Activo")
            .order_by(getattr(Program, "name", Program.id))
            .all()
        )
        prog_choices = [("", "Seleccione programa")] + [
            (p.id, getattr(p, "name", getattr(p, "nombre", str(p.id)))) for p in prog_rows
        ]
        form.program_info_id.choices = prog_choices
    elif Program is not None:
        prog_rows = (
            db.session.query(Program)
            .filter(Program.state == "Activo")
            .order_by(getattr(Program, "name", Program.id))
            .all()
        )
        form.program_info_id.choices = [("", "Seleccione programa")] + [
            (p.id, getattr(p, "name", getattr(p, "nombre", str(p.id)))) for p in prog_rows
        ]
    else:
        form.program_info_id.choices = [("", "-")]

    if form.validate_on_submit():
        if Lead is None:
            flash("Módulo de leads no disponible", "danger")
            return redirect(request.url)
        country_code = (form.country_code.data or "").strip()
        cellular_number = "".join(ch for ch in (form.cellular.data or "") if ch.isdigit())
        full_cellular = f"{country_code} {cellular_number}".strip()
        # Crear lead ligado al prescriptor
        # Determinar estado del lead: si la squeeze está en TEST utilizar estado 'TEST' si existe.
        state_id = DEFAULT_LEAD_STATE_ID
        StateLead = getattr(Base.classes, "state_lead", None)
        if prescriptor.squeeze_page_status == "TEST" and StateLead is not None:
            test_state = (
                db.session.query(StateLead)
                .filter(StateLead.name.ilike("test"))
                .first()
            )
            if test_state:
                state_id = test_state.id
        new_lead = Lead(
            id=str(uuid.uuid4()),
            prescriptor_id=prescriptor_id,
            candidate_name=form.name.data,
            candidate_email=form.email.data or None,
            candidate_cellular=full_cellular or None,
            program_info_id=form.program_info_id.data or None,
             observations=form.observations.data or None,
            state_id=state_id,
        )
        db.session.add(new_lead)
        db.session.commit()
        current_app.logger.info("Nuevo lead captado para prescriptor %s", prescriptor_id)

        # Notificar a comerciales
        if Program is not None and form.program_info_id.data:
            program = db.session.get(Program, form.program_info_id.data)
            if program and getattr(program, "commercial_emails", None):
                from sigp.common.email_utils import internal_notification_recipients, send_simple_mail  # import aquí para evitar ciclos
                emails = [e.strip() for e in program.commercial_emails.split(",") if e.strip()]
                emails = internal_notification_recipients(emails)
                if emails:
                    subject = f"Nuevo lead para programa {getattr(program,'name',program.id)}"
                    plain_body=(
                        "Se ha generado un nuevo lead desde squeeze page.\n\n"
                        f"Prescriptor: {getattr(prescriptor,'squeeze_page_name', prescriptor.id)}\n"
                        f"Programa: {getattr(program,'name', program.id)}\n"
                        f"Nombre candidato: {form.name.data}\n"
                        f"Email: {form.email.data or '-'}\n"
                        f"Celular: {full_cellular or '-'}\n"
                        f"Observaciones: {form.observations.data or '-'}\n"
                     )
                    html_body = render_template('emails/new_lead.html',
                        origin='Squeeze page',
                        prescriptor=getattr(prescriptor,'squeeze_page_name', prescriptor.id),
                        program=getattr(program,'name', program.id),
                        candidate_name=form.name.data,
                        candidate_email=form.email.data,
                        candidate_cellular=full_cellular,
                        observations=form.observations.data,
                        lead_url=(current_app.config.get('BASE_URL') or request.host_url.rstrip('/')) + url_for('leads.edit_lead', lead_id=new_lead.id))
                    
                    send_simple_mail(emails, subject, html_body, html=True, text_body=plain_body)

        return render_template("public/thanks.html", prescriptor=prescriptor)

    # Reunir imágenes para el carrusel
    images = []
    for attr in ("squeeze_page_image_1", "squeeze_page_image_2", "squeeze_page_image_3"):
        img_url = getattr(prescriptor, attr, None)
        if img_url:
            images.append(img_url)

    return render_template(
        "public/landing_prescriptor.html",
        prescriptor=prescriptor,
        images=images,
         program_urls={
             pid: getattr(prog, "program_file", None)
             for pid, _ in getattr(form.program_info_id, "choices", [])
             if pid
             for prog in [db.session.get(Program, pid)]
         } if Program else {},
        form=form,
    )
