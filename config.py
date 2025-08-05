import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """
    Configuración base de la aplicación.
    """

    # Clave de sesión (cambiar en producción)
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret")

    # # Evitar que SQLAlchemy imprima todas las consultas en consola
    # SQLALCHEMY_ECHO = False

    # Cadena de conexión a RDS
    SQLALCHEMY_DATABASE_URI = (
        os.getenv("SQLALCHEMY_DATABASE_URI")
        or "mysql+pymysql://admin:<PASSWORD>@db-prescriptores.cl0glysfjbui.eu-west-1.rds.amazonaws.com:3306/db_sigp"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask-WTF
    WTF_CSRF_ENABLED = True

    # Bcrypt
    BCRYPT_LOG_ROUNDS = 13

    # SMTP / Email
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.ionos.es")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 465))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "sigp@sportsdatacampus.com")
    # Se recomienda definir MAIL_PASSWORD en variable de entorno para no exponerla
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "Dep#Ext$2025")
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "True").lower() in {"1", "true", "yes"}
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "False").lower() in {"1", "true", "yes"}
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", MAIL_USERNAME)

    # Carpeta para contratos de prescriptores (dentro de static)
    CONTRACT_UPLOAD_FOLDER = "static/contracts"
    CONTRACT_ALLOWED_EXT = {"pdf"}

    # Facturas prescriptores
    INVOICE_UPLOAD_FOLDER = "static/invoices"
    INVOICE_ALLOWED_EXT = {"pdf", "jpg", "jpeg", "png"}
    INVOICE_MAX_MB = 5

    # Comprobantes de pago a prescriptores
    RECEIPT_UPLOAD_FOLDER = "static/receipts"

    # config.py  (modo desarrollo)
    SQLALCHEMY_ECHO = False

