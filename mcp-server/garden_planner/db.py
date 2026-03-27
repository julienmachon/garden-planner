import os

from sqlmodel import Session, create_engine

DATA_DIR = os.getenv("DATA_DIR", "./data")
DB_PATH = os.path.join(DATA_DIR, "garden.db")

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
)


def init_db() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)

    from alembic.config import Config
    from alembic import command

    alembic_ini = os.path.join(os.path.dirname(__file__), "..", "alembic.ini")
    cfg = Config(os.path.normpath(alembic_ini))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{DB_PATH}")
    command.upgrade(cfg, "head")


def get_session() -> Session:
    return Session(engine)
