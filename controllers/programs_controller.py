"""Programs controller: CRUD placeholder."""
import math
from pathlib import Path
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
)
from flask_login import login_required

from sigp import db
from sigp.models import Base

programs_bp = Blueprint("programs", __name__, url_prefix="/programs")


def _model(name):
    """Return automap model by name or None."""
    return getattr(Base.classes, name, None)


from uuid import uuid4
from sigp.security import require_perm
from sigp.common.email_utils import send_simple_mail

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FIELDS = [
    "name",
    "description",
    "price_total",
    "price_scholarship",
    "first_installment_pct",
    "commission_value",
    "language",
    "level",
    "pvp",
    "scholarship_value",
    "registration_value",
    "value_quotas",
    "commercial_emails",
    "campus_id",
    "state",
    "program_url",
    "program_file",
    "image_small",
    "image_large",
]


def _program_form(program_id=None):
    Program = _model("programs")
    if not Program:
        return "Modelo programs no disponible", 500

    program = db.session.get(Program, program_id) if program_id else None

    if request.method == "POST":
        data = {f: request.form.get(f) or None for f in FIELDS}
        # Convert decimals
        for f in FIELDS:
            if f.startswith("price") or f.endswith("value") or f.endswith("pct") or f in ("pvp", "value_quotas"):
                val = data[f]
                if val is not None:
                    data[f] = float(val.replace(",", "."))
        if program is None:
            program = Program(id=str(uuid4()))
            db.session.add(program)
        # first assign simple fields (excluding uploads)
        upload_fields = {
            "program_file_file": "program_file",
            "image_small_file": "image_small",
            "image_large_file": "image_large",
        }
        for k, v in data.items():
            if k not in upload_fields.values():
                setattr(program, k, v)
        # handle uploads
        upload_dir = current_app.config.get("PROGRAM_UPLOAD_FOLDER", Path(current_app.root_path)/"static"/"programs")
        upload_dir.mkdir(parents=True, exist_ok=True)
        def _save_upload(file_field, filename_prefix):
            if file_field and file_field.filename:
                ext = file_field.filename.rsplit('.',1)[-1]
                fname = f"{program.id}_{filename_prefix}.{ext}"
                dest = upload_dir / fname
                file_field.save(dest)
                return url_for('static', filename=f'programs/{fname}')
            return None
        file_map = [
            (request.files.get('program_file'), 'program_file', 'file'),
            (request.files.get('image_small'), 'image_small', 'small'),
            (request.files.get('image_large'), 'image_large', 'large'),
        ]
        for f, attr, prefix in file_map:
            url_saved = _save_upload(f, prefix)
            if url_saved:
                setattr(program, attr, url_saved)
        db.session.commit()
        flash("Programa guardado", "success")
        return redirect(url_for("programs.programs_list"))

    Campus = _model("campus")
    campuses = db.session.query(Campus).all() if Campus else []
    return render_template("records/program_form.html", program=program, campuses=campuses)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@programs_bp.get("/")
@login_required
@require_perm("read_program")
def programs_list():
    Program = _model("programs")
    if not Program:
        return "Modelo programs no disponible", 500

    q = request.args.get("q", "").strip()
    query = db.session.query(Program)
    if q and hasattr(Program, "name"):
        query = query.filter(Program.name.ilike(f"%{q}%"))

    page = int(request.args.get("page", 1))
    per_page = 10
    total = query.count()
    programs = (
        query.order_by(getattr(Program, "name", Program.id))
        .limit(per_page)
        .offset((page - 1) * per_page)
        .all()
    )
    pages = math.ceil(total / per_page)

    # campus map
    Campus = _model("campus")
    campus_map = {}
    if Campus is not None and programs:
        campus_ids = {p.campus_id for p in programs if getattr(p, "campus_id", None)}
        if campus_ids:
            rows = db.session.query(Campus.id, Campus.name).filter(Campus.id.in_(campus_ids)).all()
            campus_map = {cid: cname for cid, cname in rows}

    return render_template(
        "list/programs.html",
        programs=programs,
        campus_map=campus_map,
        q=q,
        page=page,
        pages=pages,
    )


@programs_bp.route("/new", methods=["GET", "POST"])
@login_required
@require_perm("create_program")
def program_new():
    return _program_form()


@programs_bp.route("/<program_id>/edit", methods=["GET", "POST"])
@login_required
@require_perm("update_program")
def program_edit(program_id):
    return _program_form(program_id)


@programs_bp.post("/<program_id>/duplicate")
@login_required
@require_perm("create_program")
def program_duplicate(program_id):
    """Crea una copia del programa y redirige a su edición."""
    Program = _model("programs")
    if not Program:
        return "Modelo programs no disponible", 500
    src = db.session.get(Program, program_id)
    if not src:
        flash("Programa no encontrado", "warning")
        return redirect(url_for("programs.programs_list"))
    new = Program(id=str(uuid4()))
    for f in FIELDS:
        setattr(new, f, getattr(src, f))
    new.name = f"{src.name} (copia)"
    db.session.add(new)
    db.session.commit()
    flash("Programa duplicado", "success")
    return redirect(url_for("programs.program_edit", program_id=new.id))


@programs_bp.post("/test-mail")
@login_required
@require_perm("update_program")
def program_test_mail_fixed():
    """Envía un correo de prueba al remitente configurado (self-test)"""
    from flask import current_app
    from flask import request
    recipient = request.form.get("to") or current_app.config.get("MAIL_DEFAULT_SENDER") or current_app.config.get("MAIL_USERNAME")
    send_simple_mail(
        [recipient],
        "Prueba SMTP SIGP (self-test)",
        "Correo de prueba para verificar el envío SMTP hacia la misma cuenta.",
    )
    flash(f"Correo de prueba enviado a {recipient}", "success")
    return redirect(url_for("programs.programs_list"))


@programs_bp.post("/<program_id>/test-email")
@login_required
@require_perm("update_program")
def program_test_email(program_id):
    """Envía un correo de prueba a las direcciones comerciales del programa."""
    Program = _model("programs")
    if not Program:
        return "Modelo programs no disponible", 500
    program = db.session.get(Program, program_id)
    if not program:
        flash("Programa no encontrado", "warning")
        return redirect(url_for("programs.programs_list"))
    emails = []
    if getattr(program, "commercial_emails", None):
        emails = [e.strip() for e in program.commercial_emails.split(",") if e.strip()]
    if not emails:
        flash("El programa no tiene emails comerciales definidos", "warning")
        return redirect(url_for("programs.programs_list"))
    subject = f"Prueba de envío de correos - Programa {program.name or program.id}"
    body = "Este es un correo de prueba desde SIGP para verificar la configuración de envío."
    send_simple_mail(emails, subject, body)
    flash("Correo de prueba enviado a: " + ", ".join(emails), "success")
    return redirect(url_for("programs.programs_list"))


@programs_bp.post("/<program_id>/toggle")
@login_required
@require_perm("delete_program")
def program_toggle(program_id):
    """Soft delete / restore: cambia state entre Activo y Desactivado"""
    Program = _model("programs")
    if not Program:
        return "Modelo programs no disponible", 500
    program = db.session.get(Program, program_id)
    if program:
        new_state = "Desactivado" if (program.state or "Activo") == "Activo" else "Activo"
        program.state = new_state
        db.session.commit()
        flash(f"Programa marcado como {new_state}", "info")
    return redirect(url_for("programs.programs_list"))
