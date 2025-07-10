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

    with app.app_context():
        from .models import reflect_db
        reflect_db(app)

    # ---- permisos en plantillas ----
    from .security import has_perm, has_any_prefix

    @app.context_processor
    def _inject_can():
        from flask_login import current_user
        return dict(can=lambda p: has_perm(current_user, p), can_mod=lambda m: has_any_prefix(current_user, m))

    # Import blueprints here to avoid circular dependencies
    from .controllers.auth_controller import auth_bp
    from .controllers.prescriptor_controller import prescriptors_bp
    from .controllers.dashboard_controller import dashboard_bp
    from .controllers.roles_controller import roles_bp
    from .controllers.users_controller import users_bp
    from .controllers.permissions_controller import perm_bp
    from .controllers.programs_controller import programs_bp
    from .controllers.state_lead_controller import state_lead_bp
    from .controllers.state_ledger_controller import state_ledger_bp
    from .controllers.state_prescriptor_controller import state_prescriptor_bp
    from .controllers.state_user_controller import state_user_bp
    from .controllers.prescriptor_type_controller import prescriptor_type_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(prescriptors_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(roles_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(perm_bp)
    app.register_blueprint(programs_bp)
    app.register_blueprint(state_lead_bp)
    app.register_blueprint(state_ledger_bp)
    app.register_blueprint(state_prescriptor_bp)
    app.register_blueprint(state_user_bp)
    app.register_blueprint(prescriptor_type_bp)

    @app.route("/")
    def index():
        from flask_login import current_user
        if current_user.is_authenticated:
            return redirect(url_for("dashboard.dashboard_home"))
        return redirect(url_for("auth.login_get"))

    return app
