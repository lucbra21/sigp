from flask import Flask, redirect, url_for
from flask_login import current_user
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv

from .config import Config

# Extensiones globales
load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()


@login_manager.user_loader
def load_user(user_id):
    """Carga un usuario por ID para Flask-Login (usa tabla `users`)."""
    from .models import Base  # import tardío para evitar circular
    User = getattr(Base.classes, "users", None)
    if User:
        return db.session.get(User, user_id)
    return None


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    # asegurar carpeta de contratos
    import os, pathlib
    upload_dir = pathlib.Path(app.root_path) / Config.CONTRACT_UPLOAD_FOLDER
    upload_dir.mkdir(parents=True, exist_ok=True)
    app.config["CONTRACT_UPLOAD_FOLDER"] = upload_dir

    with app.app_context():
        from .models import reflect_db
        reflect_db(app)

    # ---- permisos en plantillas ----
    from .security import has_perm, has_any_prefix

    @app.context_processor
    def _inject_can():
        from flask_login import current_user
        return dict(can=lambda p: has_perm(current_user, p), can_mod=lambda m: has_any_prefix(current_user, m))

    # prescriptor del usuario conectado (si corresponde)
    @app.context_processor
    def _inject_prescriptor():
        from flask_login import current_user
        from .models import Base
        Prescriptor = getattr(Base.classes, "prescriptor", None) or getattr(Base.classes, "prescriptors", None)
        if Prescriptor is None or not (current_user and current_user.is_authenticated):
            return dict(current_prescriptor=None)
        try:
            presc = (
                db.session.query(Prescriptor)
                .filter(getattr(Prescriptor, "user_id", None) == current_user.id)
                .first()
            )
        except Exception:
            presc = None
        from flask import url_for
        from pathlib import Path
        photo_url=getattr(presc,'photo_url',None) if presc else None
        contract_url=getattr(presc,'contract_url',None) if presc else None
        return dict(current_prescriptor=presc, presc_photo_url=photo_url, presc_contract_url=contract_url)

    # Import blueprints here to avoid circular dependencies
    from .controllers.auth_controller import auth_bp
    from .controllers.prescriptor_controller import prescriptors_bp
    from .controllers.dashboard_controller import dashboard_bp
    from .controllers.roles_controller import roles_bp
    from .controllers.campus_controller import campus_bp
    from .controllers.users_controller import users_bp
    from .controllers.permissions_controller import perm_bp
    from .controllers.programs_controller import programs_bp
    from .controllers.state_lead_controller import state_lead_bp
    from .controllers.state_ledger_controller import state_ledger_bp
    from .controllers.state_prescriptor_controller import state_prescriptor_bp
    from .controllers.state_user_controller import state_user_bp
    from .controllers.prescriptor_type_controller import prescriptor_type_bp
    from .controllers.confidence_level_controller import confidence_level_bp
    from .controllers.edition_controller import edition_bp
    from sigp.controllers.multimedia_controller import multimedia_bp
    from .controllers.admin_controller import admin_bp
    from .controllers.notifications_controller import notifications_bp
    from .controllers.leads_controller import leads_bp
    from .controllers.landing_controller import landing_bp
    from sigp.controllers.settlements_controller import settlements_bp
    from sigp.controllers.adjustments_controller import adjustments_bp
    from sigp.controllers.dashboard_directive_controller import bp as dashboard_directive_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(prescriptors_bp)
    app.register_blueprint(dashboard_bp)
    if 'roles' not in app.blueprints:
        app.register_blueprint(roles_bp)
    if 'campus' not in app.blueprints:
        app.register_blueprint(campus_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(perm_bp)
    app.register_blueprint(programs_bp)
    app.register_blueprint(state_lead_bp)
    app.register_blueprint(state_ledger_bp)
    app.register_blueprint(state_prescriptor_bp)
    app.register_blueprint(state_user_bp)
    app.register_blueprint(prescriptor_type_bp)
    app.register_blueprint(confidence_level_bp)
    app.register_blueprint(edition_bp)
    app.register_blueprint(multimedia_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(leads_bp)
    app.register_blueprint(landing_bp)
    app.register_blueprint(settlements_bp)
    app.register_blueprint(adjustments_bp)
    app.register_blueprint(dashboard_directive_bp)

    # ---- context processors ----
    @app.context_processor
    def inject_unread_count():
        from flask_login import current_user
        from .models import Base
        Notification = getattr(Base.classes, "notifications", None)
        def _unread_count():
            if Notification is None or not (current_user and current_user.is_authenticated):
                return 0
            try:
                return db.session.query(Notification).filter_by(user_id=current_user.id, is_read=0).count()
            except Exception:
                return 0
        return dict(unread_count=_unread_count)

    # ---- manejador 403 ----
    from flask import render_template, request
    @app.errorhandler(403)
    def _forbidden(err):
        from flask_login import current_user
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login_get', next=request.path))
        return render_template('errors/403.html'), 403

    @app.route("/")
    def index():
        from flask_login import current_user
        if current_user.is_authenticated:
            return redirect(url_for("dashboard.dashboard_home"))
        return redirect(url_for("auth.login_get"))

    return app
