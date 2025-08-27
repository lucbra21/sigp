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

    # Firma de contratos
    # SIGN_MODE: DIY (firma electrónica + PAdES local) | SAAS (proveedor externo)
    SIGN_MODE = os.getenv("SIGN_MODE", "DIY").upper()

    # Email del presidente (contra-firmante)
    PRESIDENT_EMAIL = os.getenv("PRESIDENT_EMAIL", "ing.lucasbracamonte@gmail.com")

    # Enlaces de firma (tokens firmados y expirables)
    SIGN_TOKEN_SECRET = os.getenv("SIGN_TOKEN_SECRET", "change-this-token-secret")
    SIGN_LINK_EXP_MINUTES = int(os.getenv("SIGN_LINK_EXP_MINUTES", 60))

    # Certificado del presidente para PAdES (modo DIY)
    # Ruta a .p12/.pfx y password; alternativamente, configuración PKCS#11
    PRESIDENT_CERT_PATH = os.getenv("PRESIDENT_CERT_PATH", "")
    PRESIDENT_CERT_PASS = os.getenv("PRESIDENT_CERT_PASS", "")
    PRESIDENT_PKCS11_URI = os.getenv("PRESIDENT_PKCS11_URI", "")
    PRESIDENT_PKCS11_PIN = os.getenv("PRESIDENT_PKCS11_PIN", "")

    # Facturas prescriptores
    INVOICE_UPLOAD_FOLDER = "static/invoices"
    INVOICE_ALLOWED_EXT = {"pdf", "jpg", "jpeg", "png"}
    INVOICE_MAX_MB = 5

    # Comprobantes de pago a prescriptores
    RECEIPT_UPLOAD_FOLDER = "static/receipts"

    # Comprobantes de pago a prescriptores
    RECEIPT_UPLOAD_FOLDER = "static/receipts"
    def _as_bool(v: str, default=True):
      if v is None:
        return default
      return v.strip().lower() in ("1", "true", "yes", "on")

    # ...
    NOTIFY_ON_PRESCRIPTOR_CREATE = _as_bool(os.getenv("NOTIFY_ON_PRESCRIPTOR_CREATE"), default=True)

    # config.py  (modo desarrollo)
    SQLALCHEMY_ECHO = False

