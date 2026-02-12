from flask import Flask, redirect, url_for, flash, request
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
    from .models import Base
    User = getattr(Base.classes, "users", None)
    if User:
        return db.session.get(User, user_id)
    return None


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    login_manager.init_app(app)
    # Config login redirect
    login_manager.login_view = "auth.login_get"
    login_manager.login_message = "Sesión expirada. Por favor inicia sesión nuevamente."
    login_manager.login_message_category = "warning"
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
        # from sigp.common.security import _perm_set # (comentado si no se usa)
        return dict(can=lambda p: has_perm(current_user, p), can_mod=lambda m: has_any_prefix(current_user, m))

    # prescriptor del usuario conectado
    @app.context_processor
    def _inject_prescriptor():
        from flask_login import current_user
        from .models import Base
        Prescriptor = getattr(Base.classes, "prescriptor", None) or getattr(Base.classes, "prescriptors", None)
        
        if Prescriptor is None or not (current_user and current_user.is_authenticated):
            return dict(current_prescriptor=None)
        try:
            if hasattr(Prescriptor, "user_id"):
                presc = db.session.query(Prescriptor).filter_by(user_id=current_user.id).first()
            else:
                try:
                    presc = db.session.get(Prescriptor, current_user.id)
                except Exception:
                    presc = None
        except Exception:
            presc = None
        
        photo_url=getattr(presc,'photo_url',None) if presc else None
        contract_url=getattr(presc,'contract_url',None) if presc else None
        return dict(current_prescriptor=presc, presc_photo_url=photo_url, presc_contract_url=contract_url)

    # Import blueprints
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
    from sigp.controllers.contracts_controller import contracts_bp
    from sigp.controllers.adjustments_controller import adjustments_bp
    from sigp.controllers.dashboard_directive_controller import bp as dashboard_directive_bp
    
    # --- IMPORTANTE: Aquí importamos y registramos el público ---
    from sigp.controllers.public_controller import public_bp
    app.register_blueprint(public_bp)
    # ------------------------------------------------------------

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
    app.register_blueprint(contracts_bp)
    app.register_blueprint(adjustments_bp)
    app.register_blueprint(dashboard_directive_bp)

    # ---- error handlers (CORREGIDO PARA FAVICON PNG) ----
    
    @app.errorhandler(403)
    def _forbidden(_):
        flash("URL inexistente o sesión expirada", "warning")
        return redirect(url_for("auth.login_get", next=request.full_path))

    @app.errorhandler(404)
    def _not_found(e):
        # Ignorar errores de estáticos y favicons (cualquier extensión)
        path = request.path
        if path.startswith('/static/') or 'favicon' in path:
            return "No encontrado", 404
            
        flash("URL inexistente o sesión expirada", "warning")
        return redirect(url_for("auth.login_get"))

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

    @app.route("/")
    def index():
        from flask_login import current_user
        if current_user.is_authenticated:
            return redirect(url_for("dashboard.dashboard_home"))
        return redirect(url_for("auth.login_get"))

    return app