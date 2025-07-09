"""
Inicializa la reflexión de tablas existentes mediante SQLAlchemy automap.
"""
from flask import current_app
from sqlalchemy.ext.automap import automap_base
from sigp import db

Base = automap_base()


def reflect_db(app=None):
    """
    Ejecuta la reflexión de metadatos solo una vez.
    """
    if Base.classes:
        # Ya se reflejó
        return

    # Obtener engine ya inicializado por Flask-SQLAlchemy
    engine = db.engine
    Base.prepare(engine, reflect=True)

    # Integrar mixin de Flask-Login en la clase users reflejada
    try:
        from flask_login import UserMixin
        User = Base.classes.users
        # Copiar atributos base
        for attr in ("is_authenticated", "is_anonymous", "get_id"):
            if not hasattr(User, attr):
                setattr(User, attr, getattr(UserMixin, attr))
        # is_active personalizado según state_id (2 = activo)
        if not hasattr(User, "is_active"):
            def _is_active(self):
                return getattr(self, "state_id", 2) == 2
            setattr(User, "is_active", _is_active)
    except Exception as e:
        current_app.logger.warning("No se pudo inyectar UserMixin en users: %s", e)