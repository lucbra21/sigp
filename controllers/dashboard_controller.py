"""Dashboard Controller: muestra KPIs principales."""
from datetime import datetime, timedelta

from flask import Blueprint, render_template
from flask_login import login_required

from sigp import db
from sigp.models import Base

# ---------------------------------------------------------------------------
# Blueprint
# ---------------------------------------------------------------------------

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_model(name):
    return getattr(Base.classes, name, None)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@dashboard_bp.get("/")
@login_required
def dashboard_home():
    Prescriptor = _get_model("prescriptors")
    Lead = _get_model("leads")

    # KPIs con valores por defecto en caso faltante
    prescriptores_activos = 0
    leads_matriculados = 0

    if Prescriptor:
        prescriptores_activos = (
            db.session.query(Prescriptor).filter_by(state_id=5).count()
        )

    if Lead:
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        leads_matriculados = (
            db.session.query(Lead)
            .filter(Lead.state_id == 3, Lead.created_at >= thirty_days_ago)
            .count()
        )

    return render_template(
        "records/dashboard.html",
        prescriptores_activos=prescriptores_activos,
        leads_matriculados=leads_matriculados,
    )
