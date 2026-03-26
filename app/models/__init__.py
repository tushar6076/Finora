from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


Base = declarative_base()


from .settings import UserSetting
from .records import FinancialRecord


__all__ = ["UserSetting", "FinancialRecord", "Base", "init_db"]


def init_db(uri):
    """
    Sets up the engine and returns a scoped session.
    """
    engine = create_engine(uri, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return Session()