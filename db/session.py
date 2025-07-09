"""
Crea un SessionLocal independiente del contexto Flask, útil para scripts o tareas offline.
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URI = (
    os.getenv("SQLALCHEMY_DATABASE_URI")
    or "mysql+pymysql://admin:<PASSWORD>@db-prescriptores.cl0glysfjbui.eu-west-1.rds.amazonaws.com:3306/db_sigp"
)

engine = create_engine(DATABASE_URI, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session():
    """
    Devuelve una nueva sesión ORM.
    """
    return SessionLocal()