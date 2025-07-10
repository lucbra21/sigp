import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """
    Configuración base de la aplicación.
    """

    # Clave de sesión (cambiar en producción)
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret")

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

    # config.py  (modo desarrollo)
    SQLALCHEMY_ECHO = True
#     * eliminar los estados de prescriptores sobrantes
# en la alta de prescriptor hay que meter los campos que se necesitan 
# * que estan en usuario por ejemplo mail celular nacionalidad etc
