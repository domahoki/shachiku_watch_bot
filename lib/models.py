import os
import logging
import datetime as dt

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql.functions import current_timestamp
from sqlalchemy.dialects.mysql import INTEGER

from . import db

logger = logging.getLogger(__name__)


class Users(db.Base):
    __tablename__ = "users"

    id = Column("id", INTEGER(unsigned=True), primary_key=True, auto_increment=True)
    user_id = Column("user_id", String(256))
    user_name = Column("user_name", String(256))
    update_date = Column(
        "update_date",
        DateTime,
        default=dt.datetime.now(),
        nullable=False,
        server_default=current_timestamp()
    )
    guild_id = Column("guild_id", String(256))

    def __init__(
        self,
        user_id,
        user_name,
        guild_id,
        update_date=dt.datetime.now()
    ):
        self.user_id = user_id
        self.user_name = user_name
        self.update_date = update_date
        self.guild_id = guild_id

    def __str__(self):
        return "User: {}, Added on {}".format(
            self.user_name,
            self.update_date.strftime("%Y/%m/%d %H:%M:%S"),
        )

class Channels(db.Base):
    __tablename__ = "channel"

    channel_id = Column(
        "channel_id",
        String(256),
    )
    date = Column(
        "date",
        DateTime,
        default=dt.datetime.now(),
        nullable=False,
        server_default=current_timestamp()
    )
    guild_id = Column(
        "guild_id",
        String(256),
        unique=True,
        primary_key=True,
    )

    def __init__(
        self,
        guild_id,
        channel_id,
        date=dt.datetime.now()
    ):
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.date = date

    def __str__(self):
        return "Guild: {}, Channel: {}, Set at {}".format(
            str(self.guild_id), str(self.channel_id), self.date.strftime("%Y/%m/%d %H:%M:%S"))

def init_db(force=False):
    if not os.path.isfile(db.DB_FILENAME) or force:
        db.Base.metadata.create_all(db.engine)

    else:
        logger.warning("DB file is already exists.")

class SubInfo(db.Base):
    __tablename__ = "sub_info"

    id = Column("id", INTEGER(unsigned=True), primary_key=True, auto_increment=True)
    user_id = Column("user_id", String(256))
    callback = Column("callback", String(512))
    topic = Column("topic", String(512))
    lease_seconds = Column("lease_seconds", INTEGER(unsigned=True))
    date = Column(
        "date",
        DateTime,
        default=dt.datetime.now(),
        nullable=False,
        server_default=current_timestamp()
    )

    def __init__(
        self,
        user_id,
        callback,
        topic,
        lease_seconds,
        date=dt.datetime.now()
    ):
        self.user_id = user_id
        self.callback = callback
        self.topic = topic
        self.lease_seconds = lease_seconds
        self.date = date

    def __str__(self):
        expired_date = self.get_expired_date()

        return "User: {}, CallbackURL: {}, Topic: {}, Updated at {}, Expired at {}".format(
            self.user_id,
            self.callback,
            self.topic,
            self.date.strftime("%Y/%m/%d %H:%M:%S"),
            expired_date.strftime("%Y/%m/%d %H:%M:%S")
        )

    def get_expired_date(self):
        return self.date + dt.timedelta(seconds=self.lease_seconds)

    def get_unsub_body(self):
        return {
            "hub.callback": self.callback,
            "hub.mode": "unsubscribe",
            "hub.topic": self.topic,
            "hub.lease_seconds": self.lease_seconds,
        }

    def get_sub_body(self):
        return {
            "hub.callback": self.callback,
            "hub.mode": "subscribe",
            "hub.topic": self.topic,
            "hub.lease_seconds": self.lease_seconds,
        }
