import os 
from dotenv import load_dotenv
load_dotenv()


from sqlalchemy.orm import DeclarativeBase , sessionmaker
from sqlalchemy import create_engine

engine = create_engine(
    url=os.getenv("DB_URL"),
    echo=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)


sessionlocal = sessionmaker(
    autocommit = False,
    autoflush=False,
    bind = engine
)

class Base(DeclarativeBase):
    pass


def get_db():
    db = sessionlocal()
    try:
        yield db
    finally:
        db.close()