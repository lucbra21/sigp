"""Dashboard para Comité de Dirección"""
from flask import Blueprint, render_template, current_app
from flask_login import login_required

from sigp import db
from sigp.models import Base
from sigp.security import require_perm

bp = Blueprint("dashboard_directive", __name__, url_prefix="/directive")

# Reflected models (pueden no existir en alguna instalación)
Prescriptor = getattr(Base.classes, "prescriptors", None)
StatePrescriptor = getattr(Base.classes, "state_prescriptor", None)
Lead = getattr(Base.classes, "leads", None)
Program = getattr(Base.classes, "programs", None)
Ledger = getattr(Base.classes, "ledger", None)

# Constantes que puedan existir
MATRICULADO_ID = 5  # example value; ajustar si existe tabla states
RENDIDO_ID = 4


def _safe_count(query):
    try:
        return query.count()
    except Exception as exc:
        current_app.logger.error("Error contando registros: %s", exc)
        return 0


def _safe_all(query):
    try:
        return query.all()
    except Exception as exc:
        current_app.logger.error("Error cargando registros: %s", exc)
        return []


@bp.get("/dashboard")
@login_required
@require_perm("view_dashboard_directive")
def dashboard():
    # ---------- Prescriptores ----------
    pres_total = _safe_count(db.session.query(Prescriptor)) if Prescriptor else 0
    pres_by_state = []
    if Prescriptor and StatePrescriptor:
        rows = _safe_all(
            db.session.query(Prescriptor.state_id, db.func.count(Prescriptor.id)).group_by(Prescriptor.state_id)
        )
        state_map = {
            st.id: getattr(st, "name", getattr(st, "nombre", st.id)) for st in _safe_all(db.session.query(StatePrescriptor))
        }
        pres_by_state = [(state_map.get(sid, sid), cnt) for sid, cnt in rows]

    # ---------- Leads ----------
    leads_total = _safe_count(db.session.query(Lead)) if Lead else 0
    leads_matric = 0
    if Lead:
        leads_matric = _safe_count(db.session.query(Lead).filter(Lead.state_id == MATRICULADO_ID))

    # ---------- Rentabilidad por programa ----------
    rentab_program = []
    if Program and Ledger:
        # Rentabilidad por programa se obtiene sumando montos de ledger de leads rendidos
        sub = (
            db.session.query(Lead.program_id, db.func.sum(Ledger.amount).label("total"))
            .join(Lead, Lead.id == Ledger.lead_id)
            .filter(Ledger.state_id == RENDIDO_ID)
            .group_by(Lead.program_id)
        ).subquery()
        rows = _safe_all(
            db.session.query(Program, sub.c.total).join(sub, Program.id == sub.c.program_id)
        )
        rentab_program = [
            (getattr(p, "name", getattr(p, "nombre", p.id)), total or 0) for p, total in rows
        ]

    # ---------- Ranking prescriptores ----------
    ranking = []
    if Prescriptor and Ledger:
        sub2 = (
            db.session.query(Ledger.prescriptor_id, db.func.sum(Ledger.amount).label("total"))
            .filter(Ledger.state_id == RENDIDO_ID)
            .group_by(Ledger.prescriptor_id)
            .order_by(db.desc(db.func.sum(Ledger.amount)))
            .limit(10)
            .subquery()
        )
        rows = _safe_all(
            db.session.query(Prescriptor, sub2.c.total).join(sub2, Prescriptor.id == sub2.c.prescriptor_id)
        )
        ranking = [
            (getattr(p, "squeeze_page_name", getattr(p, "name", p.id)), total or 0) for p, total in rows
        ]

    return render_template(
        "dashboard/directive.html",
        pres_total=pres_total,
        pres_by_state=pres_by_state,
        leads_total=leads_total,
        leads_matric=leads_matric,
        rentab_program=rentab_program,
        ranking=ranking,
    )
