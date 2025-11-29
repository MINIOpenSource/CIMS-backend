from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import appdirs
import os
from .models import Base

APP_NAME = "cims"
APP_AUTHOR = "MINIOpenSource"

# Determine the user-specific data directory
data_dir = appdirs.user_data_dir(APP_NAME, APP_AUTHOR)
os.makedirs(data_dir, exist_ok=True)
db_path = os.path.join(data_dir, "cims.db")

# Create the SQLAlchemy engine
engine = create_engine(
    f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Initialize the database by creating all tables defined in models.
    """
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    Dependency generator for database sessions.
    Yields a database session and closes it after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
