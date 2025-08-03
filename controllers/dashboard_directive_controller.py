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

# Obtener dinámicamente IDs de estados relevantes
_STATE_ID_CACHE = {}

def _state_id(slug:str):
    if slug in _STATE_ID_CACHE:
        return _STATE_ID_CACHE[slug]
    State = getattr(Base.classes, "state_ledger", None) or getattr(Base.classes, "state_lead", None) or getattr(Base.classes, "states", None)
    if not State:
        return None
    q = db.session.query(State.id)
    for col in (getattr(State, "code", None), getattr(State, "slug", None), getattr(State, "name", None)):
        if col is not None:
            q = q.filter(col.ilike(slug))
            break
    row = q.first()
    if row:
        _STATE_ID_CACHE[slug]=row.id
        return row.id
    return None


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

    # ---------- Subestados ----------
    pres_by_substate = []
    SubState = getattr(Base.classes, "substate_prescriptor", None)
    if Prescriptor and SubState and hasattr(Prescriptor, "sub_state_id"):
        rows2 = _safe_all(
            db.session.query(Prescriptor.sub_state_id, db.func.count(Prescriptor.id)).group_by(Prescriptor.sub_state_id)
        )
        sub_map = {row.id: getattr(row, "name", getattr(row, "nombre", row.id)) for row in _safe_all(db.session.query(SubState))}
        pres_by_substate = [(sub_map.get(sid, sid if sid is not None else "-"), cnt) for sid, cnt in rows2]

    # ---------- Leads por estado ----------
    leads_by_state = []
    LeadState = getattr(Base.classes, "state_lead", None)
    if Lead and LeadState and hasattr(Lead, "state_id"):
        rows_ls = _safe_all(
            db.session.query(Lead.state_id, db.func.count(Lead.id)).group_by(Lead.state_id)
        )
        ls_map = {row.id: getattr(row, "name", getattr(row, "nombre", row.id)) for row in _safe_all(db.session.query(LeadState))}
        leads_by_state = [(ls_map.get(sid, sid), cnt) for sid, cnt in rows_ls]

    # ---------- Leads ----------
    leads_total = _safe_count(db.session.query(Lead)) if Lead else 0
    leads_matric = 0
    if Lead:
        matric_id = _state_id("MATRICULADO") or _state_id("MATRICULADO/A")
        if matric_id:
            leads_matric = _safe_count(db.session.query(Lead).filter(Lead.state_id == matric_id))
        else:
            # si no se encontró id, contar todos los leads con cualquier estado > 0 asumido como matriculados
            leads_matric = leads_total

        # ---------- Rentabilidad por programa ----------
    rend_id = _state_id("RENDIDO")
    rentab_program = []
    if Program and Ledger:
        # Rentabilidad por programa sumando montos de ledger de leads rendidos
        q = (
            db.session.query(Lead.program_id, db.func.sum(Ledger.amount).label("total"))
            .join(Lead, Lead.id == Ledger.lead_id)
        )
        if rend_id:
            q = q.filter(Ledger.state_id == rend_id)
        sub = q.group_by(Lead.program_id).subquery()
        rows = _safe_all(
            db.session.query(Program, sub.c.total).join(sub, Program.id == sub.c.program_id)
        )
        rentab_program = [
            (getattr(p, "name", getattr(p, "nombre", p.id)), total or 0) for p, total in rows
        ]

    # ---------- Ranking prescriptores ----------
    ranking = []
    if Prescriptor and Ledger:
        q2 = db.session.query(Ledger.prescriptor_id, db.func.sum(Ledger.amount).label("total"))
        if rend_id:
            q2 = q2.filter(Ledger.state_id == rend_id)
        sub2 = (
            q2.group_by(Ledger.prescriptor_id)
            .order_by(db.desc(db.func.sum(Ledger.amount)))
            .limit(10)
        ).subquery()
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
        pres_by_substate=pres_by_substate,
        leads_by_state=leads_by_state,
    )
