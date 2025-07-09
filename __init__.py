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

    # Import blueprints here to avoid circular dependencies
    from .controllers.auth_controller import auth_bp
    from .controllers.prescriptor_controller import prescriptors_bp
    from .controllers.dashboard_controller import dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(prescriptors_bp)
    app.register_blueprint(dashboard_bp)

    @app.route("/")
    def index():
        from flask_login import current_user
        if current_user.is_authenticated:
            return redirect(url_for("dashboard.dashboard_home"))
        return redirect(url_for("auth.login_get"))

    return app
