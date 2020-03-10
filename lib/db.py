import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DB_FILENAME = "shachiku.db"
if os.environ.get("DATABASE_URL", None) is not None:
    RDB_PATH = os.environ["DATABASE_URL"]
else:
    RDB_PATH = "postgresql:///{}".format(DB_FILENAME)

ECHO_LOG = False

Base = declarative_base()
engine = create_engine(RDB_PATH, echo=ECHO_LOG)

Session = sessionmaker(bind=engine)
session = Session()
