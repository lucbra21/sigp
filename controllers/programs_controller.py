"""Programs controller: CRUD placeholder."""
import math
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
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
    "state",
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
        for k, v in data.items():
            setattr(program, k, v)
        db.session.commit()
        flash("Programa guardado", "success")
        return redirect(url_for("programs.programs_list"))

    return render_template("records/program_form.html", program=program)


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
    return render_template(
        "list/programs.html",
        programs=programs,
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
